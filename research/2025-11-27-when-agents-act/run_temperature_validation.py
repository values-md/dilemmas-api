#!/usr/bin/env python3
"""Temperature validation for When Agents Act v2.0

Purpose: Validate that our findings are not artifacts of temperature 1.0.

Design:
- Test high-reversal dilemmas at temp 0.0 and 0.5
- Use representative models spanning consistency range
- Compare reversal rates to temp 1.0 baseline

Models selected (span the range):
- Gemini 3 Pro (23.1% reversal at temp 1.0 - most consistent)
- Claude Sonnet 4.5 (30.8% - frontier consistent)
- GPT-5 (69.2% - high reversal)
- Grok-4 (41.0% - middle)

Dilemmas selected (high reversal at temp 1.0):
- Surgical Robot (63.9% reversal)
- Warehouse Robot (66.7% reversal)
- Military Drone (66.7% reversal)

Expected: ~48 judgments (3 dilemmas × 4 models × 2 modes × 2 temps)
Runtime: 5-10 minutes

Usage:
    uv run python research/2025-11-27-when-agents-act/run_temperature_validation.py --dry-run
    uv run python research/2025-11-27-when-agents-act/run_temperature_validation.py
"""

import sys
from pathlib import Path
import asyncio
import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

from dilemmas.models.dilemma import Dilemma
from dilemmas.services.judge import DilemmaJudge
from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB
from sqlalchemy import select

console = Console()

# =============================================================================
# Configuration
# =============================================================================

# New experiment for temperature validation
EXPERIMENT_ID_FILE = Path(__file__).parent / ".temp_validation_experiment_id"

def get_or_create_experiment_id() -> str:
    """Get existing experiment ID or create new one."""
    if EXPERIMENT_ID_FILE.exists():
        return EXPERIMENT_ID_FILE.read_text().strip()
    else:
        new_id = str(uuid.uuid4())
        EXPERIMENT_ID_FILE.write_text(new_id)
        return new_id

EXPERIMENT_ID = get_or_create_experiment_id()

# Temperature validation parameters
TEMPERATURES = [0.0, 0.5]  # We already have 1.0 data
METHODOLOGY = "v2_freeform"

# Representative models spanning the consistency range
MODELS = [
    "google/gemini-3-pro-preview",  # 23.1% reversal (most consistent)
    "anthropic/claude-sonnet-4.5",  # 30.8% reversal (consistent frontier)
    "x-ai/grok-4",                   # 41.0% reversal (middle)
    "openai/gpt-5",                  # 69.2% reversal (high)
]

# High-reversal dilemmas
DILEMMA_IDS = [
    "bench2-05-surgical-robot-tremor",   # 63.9% reversal
    "bench2-06-warehouse-robot-override", # 66.7% reversal
    "bench2-08-military-drone-strike",    # 66.7% reversal
]

MODES = ["theory", "action"]

# Retry settings
MAX_RETRIES = 3
INITIAL_BACKOFF = 1

# Paths
RESEARCH_DIR = Path(__file__).parent
LOGS_DIR = RESEARCH_DIR / "logs_temp_validation"
JUDGMENTS_LOG_DIR = LOGS_DIR / "judgments"


# =============================================================================
# Data structures
# =============================================================================

@dataclass
class ValidationTask:
    """A single judgment to run."""
    dilemma: Dilemma
    model_id: str
    temperature: float
    mode: str


@dataclass
class ValidationResult:
    """Result of a validation run."""
    task: ValidationTask
    success: bool
    judgment_id: str | None = None
    choice_id: str | None = None
    confidence: float | None = None
    error: str | None = None


# =============================================================================
# Utility functions
# =============================================================================

def setup_logging():
    """Create logging directories."""
    LOGS_DIR.mkdir(exist_ok=True)
    JUDGMENTS_LOG_DIR.mkdir(exist_ok=True)


def log_judgment(task: ValidationTask, judgment, request_data: dict, response_data: dict):
    """Save full judgment details to JSON file."""
    dilemma_id = task.dilemma.id
    model_name = task.model_id.split("/")[-1]
    mode = task.mode
    temp_str = f"temp{task.temperature:.1f}".replace(".", "_")

    filename = f"{dilemma_id}_{model_name}_{mode}_{temp_str}.json"
    filepath = JUDGMENTS_LOG_DIR / filename

    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "judgment_id": judgment.id if judgment else None,
        "experiment_id": EXPERIMENT_ID,
        "dilemma_id": dilemma_id,
        "dilemma_title": task.dilemma.title,
        "model_id": task.model_id,
        "mode": mode,
        "temperature": task.temperature,
        "request": request_data,
        "response": response_data,
    }

    with open(filepath, "w") as f:
        json.dump(log_data, f, indent=2, default=str)


# =============================================================================
# Database functions
# =============================================================================

async def load_dilemmas() -> list[Dilemma]:
    """Load selected dilemmas from database."""
    db = get_database()
    async for session in db.get_session():
        stmt = select(DilemmaDB).where(DilemmaDB.id.in_(DILEMMA_IDS))
        result = await session.execute(stmt)
        dilemmas_db = result.scalars().all()
        return [d.to_domain() for d in dilemmas_db]
    return []


async def get_completed_judgments() -> set[tuple[str, str, float, str]]:
    """Get set of (dilemma_id, model_id, temperature, mode) already completed."""
    db = get_database()
    completed = set()

    async for session in db.get_session():
        stmt = select(JudgementDB).where(JudgementDB.experiment_id == EXPERIMENT_ID)
        result = await session.execute(stmt)
        judgments = result.scalars().all()

        for j in judgments:
            if j.ai_judge:
                temp = j.ai_judge.temperature
                completed.add((j.dilemma_id, j.judge_id, temp, j.mode))

    return completed


async def save_judgment(judgment):
    """Save judgment to database."""
    db = get_database()
    async for session in db.get_session():
        db_judgment = JudgementDB.from_domain(judgment)
        session.add(db_judgment)
        await session.commit()


# =============================================================================
# Core execution
# =============================================================================

async def run_single_judgment(judge: DilemmaJudge, task: ValidationTask) -> ValidationResult:
    """Run a single judgment with retry logic."""
    backoff = INITIAL_BACKOFF
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            # Build request data for logging
            request_data = {
                "system_prompt": task.dilemma.action_context if task.mode == "action" else None,
                "situation_template": task.dilemma.situation_template,
                "mode": task.mode,
                "temperature": task.temperature,
            }

            # Run judgment
            judgment = await judge.judge_dilemma(
                dilemma=task.dilemma,
                model_id=task.model_id,
                temperature=task.temperature,
                mode=task.mode,
                methodology=METHODOLOGY,
            )

            # Set experiment metadata
            judgment.experiment_id = EXPERIMENT_ID
            judgment.experiment_metadata = {
                "experiment": "temperature_validation",
                "parent_experiment": "03de21a4-25ed-4df4-b03a-4715b1ca1256",
                "temperature": task.temperature,
            }

            # Save to database
            await save_judgment(judgment)

            # Build response data for logging
            response_data = {
                "choice_id": judgment.choice_id,
                "confidence": judgment.confidence,
                "reasoning": judgment.reasoning,
            }

            # Log full details
            log_judgment(task, judgment, request_data, response_data)

            return ValidationResult(
                task=task,
                success=True,
                judgment_id=judgment.id,
                choice_id=judgment.choice_id,
                confidence=judgment.confidence,
            )

        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(backoff)
                backoff *= 2

    return ValidationResult(
        task=task,
        success=False,
        error=last_error,
    )


async def run_validation(dry_run: bool = False, auto_confirm: bool = False):
    """Run the temperature validation experiment."""

    setup_logging()

    # Header
    console.print(Panel.fit(
        f"[bold]Temperature Validation Study[/bold]\n"
        f"Experiment ID: {EXPERIMENT_ID}\n"
        f"Temperatures: {TEMPERATURES}\n"
        f"Models: {len(MODELS)}\n"
        f"Dilemmas: {len(DILEMMA_IDS)}",
        border_style="cyan"
    ))

    if dry_run:
        console.print("\n[yellow]DRY RUN - No judgments will be executed[/yellow]\n")

    # Load dilemmas
    console.print("[bold]Loading dilemmas...[/bold]")
    dilemmas = await load_dilemmas()

    if len(dilemmas) != len(DILEMMA_IDS):
        console.print(f"[red]Error: Expected {len(DILEMMA_IDS)} dilemmas, found {len(dilemmas)}[/red]")
        missing = set(DILEMMA_IDS) - {d.id for d in dilemmas}
        if missing:
            console.print(f"[red]Missing dilemmas: {missing}[/red]")
        return

    console.print(f"[green]Loaded {len(dilemmas)} dilemmas[/green]\n")

    # Get completed judgments
    console.print("[bold]Checking for completed judgments...[/bold]")
    completed = await get_completed_judgments()
    console.print(f"[dim]Found {len(completed)} completed judgments[/dim]\n")

    # Build all tasks
    tasks = []
    for dilemma in dilemmas:
        for model_id in MODELS:
            for temperature in TEMPERATURES:
                for mode in MODES:
                    # Skip if already completed
                    if (dilemma.id, model_id, temperature, mode) in completed:
                        continue

                    tasks.append(ValidationTask(
                        dilemma=dilemma,
                        model_id=model_id,
                        temperature=temperature,
                        mode=mode,
                    ))

    # Show plan
    console.print("[bold]Validation Plan:[/bold]")
    table = Table(show_header=True)
    table.add_column("Dilemma", style="cyan")
    table.add_column("Temp 1.0 Reversal", justify="right")
    table.add_column("Judgments/Model", justify="right")

    reversal_rates = {
        "bench2-05-surgical-robot-tremor": "63.9%",
        "bench2-06-warehouse-robot-override": "66.7%",
        "bench2-08-military-drone-strike": "66.7%",
    }

    for d in dilemmas:
        judgments_per_model = len(TEMPERATURES) * len(MODES)
        table.add_row(
            d.title[:40],
            reversal_rates.get(d.id, "?"),
            str(judgments_per_model)
        )

    console.print(table)

    console.print(f"\n[bold]Total judgments planned:[/bold] {len(tasks)}")
    console.print(f"[bold]Already completed:[/bold] {len(completed)}")
    console.print(f"[bold]Remaining:[/bold] {len(tasks)}\n")

    console.print("[bold]Models:[/bold]")
    model_info = {
        "google/gemini-3-pro-preview": "23.1% @ temp 1.0 (most consistent)",
        "anthropic/claude-sonnet-4.5": "30.8% @ temp 1.0 (consistent)",
        "x-ai/grok-4": "41.0% @ temp 1.0 (middle)",
        "openai/gpt-5": "69.2% @ temp 1.0 (high reversal)",
    }
    for model in MODELS:
        console.print(f"  • {model.split('/')[-1]}: {model_info.get(model, '?')}")

    if dry_run:
        console.print("\n[yellow]Dry run complete. Exiting.[/yellow]")
        return

    if len(tasks) == 0:
        console.print("[green]All judgments already completed![/green]")
        return

    # Confirm start
    if not auto_confirm:
        console.print("\n[yellow]Press Enter to start, Ctrl+C to cancel...[/yellow]")
        input()

    # Initialize judge
    judge = DilemmaJudge()
    results = []

    # Run tasks
    console.print(f"\n[bold cyan]Running {len(tasks)} judgments...[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("[cyan]Temperature validation", total=len(tasks))

        for task in tasks:
            result = await run_single_judgment(judge, task)
            results.append(result)
            progress.update(task_id, advance=1)

            # Brief status
            if result.success:
                status = f"✓ {task.dilemma.id[:15]}... {task.model_id.split('/')[-1]} temp{task.temperature} {task.mode}"
                console.print(f"[dim]{status}[/dim]")
            else:
                status = f"✗ {task.dilemma.id[:15]}... {task.model_id.split('/')[-1]} temp{task.temperature} {task.mode}"
                console.print(f"[red]{status}[/red]")
                if result.error:
                    console.print(f"[dim red]  Error: {result.error[:100]}...[/dim red]")

    # Final summary
    console.print(f"\n{'='*60}")
    console.print("[bold green]Temperature Validation Complete![/bold green]")
    console.print(f"{'='*60}\n")

    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    console.print(f"[bold]Experiment ID:[/bold] {EXPERIMENT_ID}")
    console.print(f"[bold]Total judgments:[/bold] {len(results)}")
    console.print(f"[bold]Successful:[/bold] {len(successes)}")
    console.print(f"[bold]Failed:[/bold] {len(failures)}")

    if failures:
        console.print(f"\n[red]Failed judgments:[/red]")
        for f in failures:
            console.print(f"  • {f.task.dilemma.id} {f.task.model_id} temp{f.task.temperature} {f.task.mode}")
            if f.error:
                console.print(f"    [dim red]Error: {f.error}[/dim red]")

    # Analysis preview
    console.print(f"\n[bold cyan]Quick Analysis:[/bold cyan]")

    # Group by (model, dilemma) to find reversals
    theory_choices = {}
    action_choices = {}

    for r in successes:
        if r.task.mode == "theory":
            key = (r.task.model_id, r.task.dilemma.id, r.task.temperature)
            theory_choices[key] = r.choice_id
        else:
            key = (r.task.model_id, r.task.dilemma.id, r.task.temperature)
            action_choices[key] = r.choice_id

    # Count reversals per temperature
    temp_reversals = {t: 0 for t in TEMPERATURES}
    temp_total = {t: 0 for t in TEMPERATURES}

    for key in theory_choices:
        if key in action_choices:
            temp_total[key[2]] += 1
            if theory_choices[key] != action_choices[key]:
                temp_reversals[key[2]] += 1

    console.print("\nReversal rates by temperature:")
    for temp in sorted(TEMPERATURES):
        if temp_total[temp] > 0:
            rate = temp_reversals[temp] / temp_total[temp] * 100
            console.print(f"  Temp {temp}: {temp_reversals[temp]}/{temp_total[temp]} pairs reversed ({rate:.1f}%)")

    console.print(f"\n[dim]Baseline (temp 1.0 from main experiment): 47.6% reversal rate[/dim]")

    # Next steps
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Review logs: [cyan]{LOGS_DIR}[/cyan]")
    console.print(f"  2. Export data: [cyan]uv run python scripts/export_experiment_data.py {EXPERIMENT_ID} research/2025-11-27-when-agents-act/temp_validation_data[/cyan]")
    console.print(f"  3. Full analysis: [cyan]uv run python research/2025-11-27-when-agents-act/analyze_temperature_validation.py[/cyan]")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Temperature validation for When Agents Act v2.0")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without running")
    parser.add_argument("--new-experiment", action="store_true", help="Start fresh (new experiment ID)")
    parser.add_argument("--show-id", action="store_true", help="Show current experiment ID")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if args.new_experiment:
        if EXPERIMENT_ID_FILE.exists():
            old_id = EXPERIMENT_ID_FILE.read_text().strip()
            EXPERIMENT_ID_FILE.unlink()
            console.print(f"[yellow]Removed old experiment ID: {old_id}[/yellow]")
        new_id = str(uuid.uuid4())
        EXPERIMENT_ID_FILE.write_text(new_id)
        console.print(f"[green]Created new experiment ID: {new_id}[/green]")
        sys.exit(0)
    elif args.show_id:
        console.print(f"[bold]Current Experiment ID:[/bold] {EXPERIMENT_ID}")
        console.print(f"[dim]Stored in: {EXPERIMENT_ID_FILE}[/dim]")
    else:
        asyncio.run(run_validation(dry_run=args.dry_run, auto_confirm=args.yes))
