#!/usr/bin/env python3
"""Full experiment runner: When Agents Act v2.0

Features:
- Parallel execution with adaptive backoff on errors
- Save after each judgment to DB
- Resume capability (skips completed judgments)
- Exponential backoff on rate limits
- Interactive pause between dilemmas
- Full request/response logging to JSON files

Usage:
    uv run python research/2025-11-27-when-agents-act/run.py --dry-run
    uv run python research/2025-11-27-when-agents-act/run.py
    uv run python research/2025-11-27-when-agents-act/run.py --dilemma bench2-01-phone-agent-child
    uv run python research/2025-11-27-when-agents-act/run.py --start-from bench2-05-surgical-robot-tremor
"""

import sys
from pathlib import Path
import asyncio
import uuid
import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any

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

# Experiment ID - persisted to file for resume capability
EXPERIMENT_ID_FILE = Path(__file__).parent / ".experiment_id"

def get_or_create_experiment_id() -> str:
    """Get existing experiment ID or create new one."""
    if EXPERIMENT_ID_FILE.exists():
        return EXPERIMENT_ID_FILE.read_text().strip()
    else:
        new_id = str(uuid.uuid4())
        EXPERIMENT_ID_FILE.write_text(new_id)
        return new_id

EXPERIMENT_ID = get_or_create_experiment_id()
COLLECTION = "bench-2"
TEMPERATURE = 1.0
METHODOLOGY = "v2_freeform"

MODELS = [
    "anthropic/claude-opus-4.5",
    "openai/gpt-5",
    "openai/gpt-5-nano",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    "google/gemini-3-pro-preview",
    "google/gemini-2.5-flash",
    "x-ai/grok-4",
    "x-ai/grok-4-fast",
]

MODES = ["theory", "action"]

# Retry settings
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # seconds
MAX_BACKOFF = 60  # seconds

# Parallelism settings
INITIAL_PARALLEL = 3  # Start with 3 concurrent requests
MIN_PARALLEL = 1  # Back off to sequential if too many errors

# Paths
RESEARCH_DIR = Path(__file__).parent
LOGS_DIR = RESEARCH_DIR / "logs"
JUDGMENTS_LOG_DIR = LOGS_DIR / "judgments"


# =============================================================================
# Data structures
# =============================================================================

@dataclass
class JudgmentTask:
    """A single judgment to run."""
    dilemma: Dilemma
    model_id: str
    mode: str
    variation_key: str
    variable_values: dict[str, str]


@dataclass
class JudgmentResult:
    """Result of a judgment run."""
    task: JudgmentTask
    success: bool
    judgment_id: str | None = None
    choice_id: str | None = None
    confidence: float | None = None
    error: str | None = None
    response_time_ms: int | None = None


# =============================================================================
# Utility functions
# =============================================================================

def compute_variation_key(variable_values: dict[str, str]) -> str:
    """Compute a hash key for a set of variable values."""
    sorted_items = sorted(variable_values.items())
    key_str = json.dumps(sorted_items, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()[:12]


def get_all_variations(dilemma: Dilemma) -> list[dict[str, str]]:
    """Get all variable value combinations for a dilemma."""
    if not dilemma.variables:
        return [{}]

    # For single variable (our case), just iterate values
    variations = []
    for var_name, var_values in dilemma.variables.items():
        for value in var_values:
            variations.append({var_name: value})

    return variations


def setup_logging():
    """Create logging directories."""
    LOGS_DIR.mkdir(exist_ok=True)
    JUDGMENTS_LOG_DIR.mkdir(exist_ok=True)


def log_judgment(
    task: JudgmentTask,
    judgment: Any,
    request_data: dict,
    response_data: dict,
):
    """Save full judgment details to JSON file."""
    dilemma_id = task.dilemma.id
    var_key = task.variation_key
    model_name = task.model_id.split("/")[-1]
    mode = task.mode

    filename = f"{dilemma_id}_{var_key}_{model_name}_{mode}.json"
    filepath = JUDGMENTS_LOG_DIR / filename

    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "judgment_id": judgment.id if judgment else None,
        "experiment_id": EXPERIMENT_ID,
        "dilemma_id": dilemma_id,
        "dilemma_title": task.dilemma.title,
        "model_id": task.model_id,
        "mode": mode,
        "temperature": TEMPERATURE,
        "variation_key": var_key,
        "variable_values": task.variable_values,
        "request": request_data,
        "response": response_data,
        "metadata": {
            "response_time_ms": judgment.response_time_ms if judgment else None,
            "choice_id": judgment.choice_id if judgment else None,
            "confidence": judgment.confidence if judgment else None,
        }
    }

    with open(filepath, "w") as f:
        json.dump(log_data, f, indent=2, default=str)


def log_error(task: JudgmentTask, error: str):
    """Append error to errors log."""
    error_file = LOGS_DIR / "errors.log"
    timestamp = datetime.now(timezone.utc).isoformat()

    with open(error_file, "a") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Dilemma: {task.dilemma.id}\n")
        f.write(f"Model: {task.model_id}\n")
        f.write(f"Mode: {task.mode}\n")
        f.write(f"Variation: {task.variation_key}\n")
        f.write(f"Error: {error}\n")


def log_progress(message: str):
    """Append to experiment progress log."""
    log_file = LOGS_DIR / "experiment.log"
    timestamp = datetime.now(timezone.utc).isoformat()

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


# =============================================================================
# Database functions
# =============================================================================

async def load_dilemmas() -> list[Dilemma]:
    """Load all bench-2 dilemmas from database."""
    db = get_database()
    async for session in db.get_session():
        stmt = select(DilemmaDB).where(DilemmaDB.collection == COLLECTION).order_by(DilemmaDB.id)
        result = await session.execute(stmt)
        dilemmas_db = result.scalars().all()
        return [d.to_domain() for d in dilemmas_db]
    return []


async def get_completed_judgments() -> set[tuple[str, str, str, str]]:
    """Get set of (dilemma_id, variation_key, model_id, mode) already completed."""
    db = get_database()
    completed = set()

    async for session in db.get_session():
        stmt = select(JudgementDB).where(JudgementDB.experiment_id == EXPERIMENT_ID)
        result = await session.execute(stmt)
        judgments = result.scalars().all()

        for j in judgments:
            completed.add((j.dilemma_id, j.variation_key or "", j.judge_id, j.mode))

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

async def run_single_judgment(
    judge: DilemmaJudge,
    task: JudgmentTask,
    semaphore: asyncio.Semaphore,
) -> JudgmentResult:
    """Run a single judgment with retry logic."""

    async with semaphore:
        backoff = INITIAL_BACKOFF
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                # Build request data for logging
                request_data = {
                    "system_prompt": task.dilemma.action_context if task.mode == "action" else None,
                    "situation_template": task.dilemma.situation_template,
                    "variable_values": task.variable_values,
                    "mode": task.mode,
                    "methodology": METHODOLOGY,
                }

                # Run judgment
                judgment = await judge.judge_dilemma(
                    dilemma=task.dilemma,
                    model_id=task.model_id,
                    temperature=TEMPERATURE,
                    mode=task.mode,
                    methodology=METHODOLOGY,
                    variable_values=task.variable_values,
                )

                # Set experiment metadata
                judgment.experiment_id = EXPERIMENT_ID
                judgment.variation_key = task.variation_key
                judgment.experiment_metadata = {
                    "experiment": "when_agents_act_v2",
                    "collection": COLLECTION,
                    "variable_values": task.variable_values,
                }

                # Save to database
                await save_judgment(judgment)

                # Build response data for logging
                response_data = {
                    "choice_id": judgment.choice_id,
                    "confidence": judgment.confidence,
                    "reasoning": judgment.reasoning,
                    "reasoning_trace": judgment.reasoning_trace,
                }
                if judgment.ai_judge and judgment.ai_judge.tool_calls:
                    response_data["tool_calls"] = [
                        {"tool_name": tc.tool_name, "parameters": tc.parameters}
                        for tc in judgment.ai_judge.tool_calls
                    ]

                # Log full details
                log_judgment(task, judgment, request_data, response_data)

                return JudgmentResult(
                    task=task,
                    success=True,
                    judgment_id=judgment.id,
                    choice_id=judgment.choice_id,
                    confidence=judgment.confidence,
                    response_time_ms=judgment.response_time_ms,
                )

            except Exception as e:
                last_error = str(e)
                error_lower = last_error.lower()

                # Check if rate limit error
                is_rate_limit = any(x in error_lower for x in ["rate", "limit", "429", "quota"])

                if is_rate_limit and attempt < MAX_RETRIES - 1:
                    console.print(f"[yellow]Rate limit hit, waiting {backoff}s...[/yellow]")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF)
                elif attempt < MAX_RETRIES - 1:
                    # Other error, shorter wait
                    await asyncio.sleep(1)

        # All retries failed
        log_error(task, last_error or "Unknown error")
        return JudgmentResult(
            task=task,
            success=False,
            error=last_error,
        )


async def run_dilemma(
    judge: DilemmaJudge,
    dilemma: Dilemma,
    completed: set[tuple[str, str, str, str]],
    parallel_limit: int,
) -> tuple[list[JudgmentResult], int]:
    """Run all judgments for a single dilemma.

    Returns:
        Tuple of (results, new_parallel_limit)
    """
    # Build all tasks for this dilemma
    tasks = []
    variations = get_all_variations(dilemma)

    for var_values in variations:
        var_key = compute_variation_key(var_values) if var_values else "default"

        for model_id in MODELS:
            for mode in MODES:
                # Skip if already completed
                if (dilemma.id, var_key, model_id, mode) in completed:
                    continue

                tasks.append(JudgmentTask(
                    dilemma=dilemma,
                    model_id=model_id,
                    mode=mode,
                    variation_key=var_key,
                    variable_values=var_values,
                ))

    if not tasks:
        console.print(f"[dim]  All judgments already completed for {dilemma.id}[/dim]")
        return [], parallel_limit

    console.print(f"[cyan]  Running {len(tasks)} judgments ({len(tasks)} remaining)...[/cyan]")

    # Run with semaphore for parallelism control
    semaphore = asyncio.Semaphore(parallel_limit)
    results = []
    errors_in_batch = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"[cyan]{dilemma.id}", total=len(tasks))

        # Run tasks
        async def run_and_track(t):
            nonlocal errors_in_batch
            result = await run_single_judgment(judge, t, semaphore)
            progress.update(task_id, advance=1)
            if not result.success:
                errors_in_batch += 1
            return result

        results = await asyncio.gather(*[run_and_track(t) for t in tasks])

    # Adjust parallelism based on errors
    new_parallel = parallel_limit
    if errors_in_batch > len(tasks) * 0.2:  # >20% errors
        new_parallel = max(MIN_PARALLEL, parallel_limit - 1)
        console.print(f"[yellow]High error rate, reducing parallelism to {new_parallel}[/yellow]")
    elif errors_in_batch == 0 and parallel_limit < INITIAL_PARALLEL:
        new_parallel = min(INITIAL_PARALLEL, parallel_limit + 1)
        console.print(f"[green]No errors, increasing parallelism to {new_parallel}[/green]")

    return list(results), new_parallel


def print_dilemma_summary(dilemma: Dilemma, results: list[JudgmentResult]):
    """Print summary after completing a dilemma."""
    if not results:
        return

    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    # Count gaps
    theory_choices = {}
    action_choices = {}

    for r in successes:
        key = (r.task.variation_key, r.task.model_id)
        if r.task.mode == "theory":
            theory_choices[key] = r.choice_id
        else:
            action_choices[key] = r.choice_id

    gaps = 0
    for key in theory_choices:
        if key in action_choices and theory_choices[key] != action_choices[key]:
            gaps += 1

    # Print summary
    console.print(f"\n[bold]Summary for {dilemma.title}:[/bold]")
    console.print(f"  Completed: {len(successes)}/{len(results)}")
    console.print(f"  Failures: {len(failures)}")
    console.print(f"  Judgment-Action Gaps: {gaps}")

    if failures:
        console.print(f"  [red]Failed tasks:[/red]")
        for f in failures[:3]:  # Show first 3
            console.print(f"    - {f.task.model_id} {f.task.mode}: {f.error[:50]}...")


# =============================================================================
# Main runner
# =============================================================================

async def run_experiment(
    dry_run: bool = False,
    single_dilemma: str | None = None,
    start_from: str | None = None,
):
    """Run the full experiment."""

    setup_logging()

    # Header
    console.print(Panel.fit(
        f"[bold]When Agents Act v2.0 - Full Experiment[/bold]\n"
        f"Experiment ID: {EXPERIMENT_ID}\n"
        f"Collection: {COLLECTION}\n"
        f"Models: {len(MODELS)}\n"
        f"Temperature: {TEMPERATURE}",
        border_style="cyan"
    ))

    log_progress(f"Experiment started: {EXPERIMENT_ID}")

    if dry_run:
        console.print("\n[yellow]DRY RUN - No judgments will be executed[/yellow]\n")

    # Load dilemmas
    console.print("[bold]Loading dilemmas...[/bold]")
    dilemmas = await load_dilemmas()
    console.print(f"[green]Loaded {len(dilemmas)} dilemmas from {COLLECTION}[/green]\n")

    # Filter if single dilemma specified
    if single_dilemma:
        dilemmas = [d for d in dilemmas if d.id == single_dilemma]
        if not dilemmas:
            console.print(f"[red]Dilemma '{single_dilemma}' not found[/red]")
            return

    # Skip to start_from if specified
    if start_from:
        start_idx = next((i for i, d in enumerate(dilemmas) if d.id == start_from), None)
        if start_idx is None:
            console.print(f"[red]Dilemma '{start_from}' not found[/red]")
            return
        dilemmas = dilemmas[start_idx:]
        console.print(f"[yellow]Starting from {start_from} ({len(dilemmas)} dilemmas remaining)[/yellow]\n")

    # Get completed judgments for resume
    console.print("[bold]Checking for completed judgments...[/bold]")
    completed = await get_completed_judgments()
    console.print(f"[dim]Found {len(completed)} completed judgments for this experiment[/dim]\n")

    # Calculate totals
    total_judgments = 0
    for d in dilemmas:
        variations = get_all_variations(d)
        total_judgments += len(variations) * len(MODELS) * len(MODES)

    remaining = total_judgments - len(completed)

    # Show plan
    console.print("[bold]Experiment Plan:[/bold]")
    table = Table(show_header=True)
    table.add_column("Dilemma ID", style="cyan")
    table.add_column("Title")
    table.add_column("Variations", justify="right")
    table.add_column("Judgments", justify="right")

    for d in dilemmas:
        variations = get_all_variations(d)
        judgments = len(variations) * len(MODELS) * len(MODES)
        table.add_row(d.id, d.title[:40], str(len(variations)), str(judgments))

    console.print(table)
    console.print(f"\n[bold]Total judgments:[/bold] {total_judgments}")
    console.print(f"[bold]Remaining:[/bold] {remaining}")
    console.print(f"[bold]Already completed:[/bold] {len(completed)}\n")

    if dry_run:
        console.print("[yellow]Dry run complete. Exiting.[/yellow]")
        return

    if remaining == 0:
        console.print("[green]All judgments already completed![/green]")
        return

    # Confirm start
    console.print("[yellow]Press Enter to start, Ctrl+C to cancel...[/yellow]")
    input()

    # Initialize
    judge = DilemmaJudge()
    parallel_limit = INITIAL_PARALLEL
    all_results = []

    # Run each dilemma
    for i, dilemma in enumerate(dilemmas):
        console.print(f"\n{'='*60}")
        console.print(f"[bold cyan]Dilemma {i+1}/{len(dilemmas)}: {dilemma.title}[/bold cyan]")
        console.print(f"[dim]ID: {dilemma.id}[/dim]")
        console.print(f"{'='*60}\n")

        log_progress(f"Starting dilemma: {dilemma.id}")

        # Run all judgments for this dilemma
        results, parallel_limit = await run_dilemma(
            judge, dilemma, completed, parallel_limit
        )
        all_results.extend(results)

        # Print summary
        print_dilemma_summary(dilemma, results)

        log_progress(f"Completed dilemma: {dilemma.id} ({len([r for r in results if r.success])} successes)")

        # Progress update (no pause - runs continuously)
        if i < len(dilemmas) - 1:
            console.print(f"\n[green]Dilemma {i+1}/{len(dilemmas)} complete. Continuing...[/green]")

    # Final summary
    console.print(f"\n{'='*60}")
    console.print("[bold green]Experiment Complete![/bold green]")
    console.print(f"{'='*60}\n")

    total_success = len([r for r in all_results if r.success])
    total_failed = len([r for r in all_results if not r.success])

    console.print(f"[bold]Experiment ID:[/bold] {EXPERIMENT_ID}")
    console.print(f"[bold]Total judgments run:[/bold] {len(all_results)}")
    console.print(f"[bold]Successful:[/bold] {total_success}")
    console.print(f"[bold]Failed:[/bold] {total_failed}")

    log_progress(f"Experiment complete: {total_success} successes, {total_failed} failures")

    # Export instructions
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Review logs: [cyan]{LOGS_DIR}[/cyan]")
    console.print(f"  2. Export data: [cyan]uv run python scripts/export_experiment_data.py {EXPERIMENT_ID} research/2025-11-27-when-agents-act/data[/cyan]")
    console.print(f"  3. Analyze: [cyan]uv run python research/2025-11-27-when-agents-act/analyze.py[/cyan]")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run When Agents Act v2.0 experiment")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without running")
    parser.add_argument("--dilemma", type=str, help="Run only a single dilemma by ID")
    parser.add_argument("--start-from", type=str, help="Start from a specific dilemma ID")
    parser.add_argument("--new-experiment", action="store_true",
                        help="Start a new experiment (generates new ID, ignores previous progress)")
    parser.add_argument("--show-id", action="store_true", help="Show current experiment ID and exit")
    args = parser.parse_args()

    # Handle --new-experiment
    if args.new_experiment:
        if EXPERIMENT_ID_FILE.exists():
            old_id = EXPERIMENT_ID_FILE.read_text().strip()
            EXPERIMENT_ID_FILE.unlink()
            console.print(f"[yellow]Removed old experiment ID: {old_id}[/yellow]")
        new_id = str(uuid.uuid4())
        EXPERIMENT_ID_FILE.write_text(new_id)
        console.print(f"[green]Created new experiment ID: {new_id}[/green]")
        console.print(f"\n[dim]Now run again without --new-experiment to start[/dim]")
        sys.exit(0)
    elif args.show_id:
        console.print(f"[bold]Current Experiment ID:[/bold] {EXPERIMENT_ID}")
        console.print(f"[dim]Stored in: {EXPERIMENT_ID_FILE}[/dim]")
        console.print(f"\n[dim]To start fresh: --new-experiment[/dim]")
    else:
        asyncio.run(run_experiment(
            dry_run=args.dry_run,
            single_dilemma=args.dilemma,
            start_from=args.start_from,
        ))
