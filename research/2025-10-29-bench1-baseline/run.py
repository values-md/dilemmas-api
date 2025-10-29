"""bench-1 Baseline: Systematic LLM Behavior Mapping

Research Question: What is the natural ethical decision-making behavior
of major LLMs across comprehensive dilemmas and demographic variations?

Design:
- Models: 4 flagship LLMs (GPT-5, Claude 4.5, Gemini 2.5 Pro, Grok 4)
- Dilemmas: 20 from bench-1 collection
- Variables: ALL systematic combinations (1,601 total variations)
- Modes: theory AND action
- Temperature: 1.0 (standard)
- Repetitions: 1 (single pass)
- Total: 12,808 judgements (~$62, ~14 hours)

Failsafes:
- Save after each judgement
- Resume capability (skip completed)
- Retry on API failures (3× exponential backoff)
- Rate limiting (5 concurrent requests)
- Graceful shutdown (Ctrl+C)
- Progress checkpoints every 50 judgements
"""

import asyncio
import hashlib
import itertools
import signal
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.services.judge import DilemmaJudge

console = Console()

# Database - use absolute path (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)

# Experiment configuration
# IMPORTANT: This experiment_id is hardcoded to persist across runs for auto-resume
CONFIG = {
    "experiment_id": "b191388e-3994-4ebd-96cc-af0d033c5230",
    "name": "bench-1 Baseline: Systematic LLM Behavior Mapping",
    "question": "Natural ethical decision-making behavior across LLMs and demographics",
    "temperature": 1.0,
    "models": [
        "openai/gpt-5",
        "anthropic/claude-sonnet-4.5",
        "google/gemini-2.5-pro",
        "x-ai/grok-4",
    ],
    "modes": ["theory", "action"],
    "collection": "bench-1",
}

# Rate limiting and failsafes
MAX_CONCURRENT_REQUESTS = 5  # Conservative (can increase to 10-15)
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential: 2s, 4s, 8s
CHECKPOINT_EVERY = 50  # Log progress every N judgements

# Global state for graceful shutdown
shutdown_requested = False
judgements_completed = 0
failures = []


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    console.print("\n[yellow]⚠ Shutdown requested. Finishing current requests...[/yellow]")
    shutdown_requested = True


signal.signal(signal.SIGINT, signal_handler)


def generate_variation_key(variable_values: dict[str, str]) -> str:
    """Generate unique key for a variable combination."""
    sorted_items = sorted(variable_values.items())
    key_str = "|".join(f"{k}={v}" for k, v in sorted_items)
    return hashlib.md5(key_str.encode()).hexdigest()[:16]


async def load_completed_judgements(experiment_id: str) -> Set[Tuple[str, str, str, str]]:
    """Load completed judgements to enable resume.

    Returns:
        Set of (model_id, dilemma_id, variation_key, mode) tuples
    """
    completed = set()

    async with AsyncSession(engine) as session:
        result = await session.exec(
            select(JudgementDB).where(JudgementDB.experiment_id == experiment_id)
        )
        judgements = result.all()

        for j in judgements:
            judgement = j.to_domain()
            model_id = judgement.get_judge_id() if judgement.judge_type == "ai" else None
            if model_id and judgement.variation_key:
                completed.add((
                    model_id,
                    judgement.dilemma_id,
                    judgement.variation_key,
                    judgement.mode
                ))

    return completed


async def load_bench1_dilemmas():
    """Load all dilemmas from bench-1 collection."""
    async with AsyncSession(engine) as session:
        result = await session.exec(
            select(DilemmaDB).where(DilemmaDB.collection == CONFIG["collection"])
        )
        db_dilemmas = result.all()
        return [d.to_domain() for d in db_dilemmas]


def generate_all_variations(dilemma):
    """Generate all variable combinations for a dilemma.

    Returns:
        List of variable_values dicts
    """
    if not dilemma.variables:
        return [{}]  # Single variation with no variables

    # Get all variable names and their options
    var_names = list(dilemma.variables.keys())
    var_options = [dilemma.variables[name] for name in var_names]

    # Generate all combinations
    variations = []
    for combo in itertools.product(*var_options):
        variation = {name: value for name, value in zip(var_names, combo)}
        variations.append(variation)

    return variations


async def judge_with_retry(
    judge: DilemmaJudge,
    dilemma,
    model_id: str,
    temperature: float,
    mode: str,
    variable_values: dict,
) -> Tuple[bool, any, str]:
    """Judge with exponential backoff retry.

    Returns:
        (success: bool, judgement: Judgement | None, error: str | None)
    """
    for attempt in range(MAX_RETRIES):
        try:
            judgement = await judge.judge_dilemma(
                dilemma=dilemma,
                model_id=model_id,
                temperature=temperature,
                mode=mode,
                variable_values=variable_values,
            )
            return (True, judgement, None)

        except Exception as e:
            error_msg = str(e)

            # Check if rate limit error
            if "429" in error_msg or "rate limit" in error_msg.lower():
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR ** (attempt + 1)
                    console.print(f"[yellow]  Rate limit hit, waiting {wait_time}s...[/yellow]")
                    await asyncio.sleep(wait_time)
                    continue

            # Other errors
            if attempt < MAX_RETRIES - 1:
                wait_time = BACKOFF_FACTOR ** attempt
                await asyncio.sleep(wait_time)
                continue

            # All retries exhausted
            return (False, None, error_msg)

    return (False, None, "Max retries exceeded")


async def run_experiment(dry_run: bool = False):
    """Run the bench-1 baseline experiment."""
    global judgements_completed, failures

    console.print("\n[bold cyan]bench-1 Baseline: Systematic LLM Behavior Mapping[/bold cyan]")
    console.print(f"[yellow]Experiment ID:[/yellow] {CONFIG['experiment_id']}\n")

    # Load dilemmas
    dilemmas = await load_bench1_dilemmas()

    if len(dilemmas) != 20:
        console.print(f"[red]Error:[/red] Expected 20 bench-1 dilemmas, found {len(dilemmas)}")
        return 1

    console.print(f"[green]✓[/green] Loaded {len(dilemmas)} dilemmas from bench-1\n")

    # Generate all variations
    console.print("[cyan]Generating all variable combinations...[/cyan]")
    experiment_plan = []

    for dilemma in dilemmas:
        variations = generate_all_variations(dilemma)
        for model_id in CONFIG["models"]:
            for mode in CONFIG["modes"]:
                for variable_values in variations:
                    variation_key = generate_variation_key(variable_values)
                    experiment_plan.append({
                        "model_id": model_id,
                        "dilemma": dilemma,
                        "mode": mode,
                        "variable_values": variable_values,
                        "variation_key": variation_key,
                    })

    total_judgements = len(experiment_plan)
    console.print(f"[green]✓[/green] Generated {total_judgements:,} judgement configurations\n")

    # Show summary table
    table = Table(title="Experiment Configuration")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Models", f"{len(CONFIG['models'])} (GPT-5, Claude 4.5, Gemini 2.5 Pro, Grok 4)")
    table.add_row("Dilemmas", f"{len(dilemmas)} from bench-1")
    table.add_row("Variable combinations", "1,601 (systematic)")
    table.add_row("Modes", "theory + action")
    table.add_row("Temperature", str(CONFIG["temperature"]))
    table.add_row("Total judgements", f"{total_judgements:,}")
    table.add_row("Estimated cost", "~$62")
    table.add_row("Estimated time", "~14 hours (5 concurrent)")
    table.add_row("Concurrent requests", str(MAX_CONCURRENT_REQUESTS))

    console.print(table)
    console.print()

    # Check for resume
    completed = await load_completed_judgements(CONFIG["experiment_id"])

    if completed:
        console.print(f"[yellow]Found {len(completed)} completed judgements from previous run[/yellow]")
        console.print("[yellow]Resuming from checkpoint...[/yellow]\n")

        # Filter out completed
        experiment_plan = [
            item for item in experiment_plan
            if (item["model_id"], item["dilemma"].id, item["variation_key"], item["mode"]) not in completed
        ]

        judgements_completed = len(completed)
        console.print(f"[green]✓[/green] {len(experiment_plan):,} judgements remaining\n")

    if dry_run:
        console.print("[yellow]DRY RUN - No API calls will be made[/yellow]")
        console.print(f"\nWould execute {len(experiment_plan):,} judgements")
        return 0

    # Run judgements
    judge = DilemmaJudge()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def process_item(item, progress, task):
        global judgements_completed, shutdown_requested

        if shutdown_requested:
            return

        async with semaphore:
            model_name = item["model_id"].split("/")[-1]
            dilemma_title = item["dilemma"].title[:30]

            progress.update(
                task,
                description=f"[cyan]{model_name} | {dilemma_title}... | {item['mode']}"
            )

            # Judge with retry
            success, judgement, error = await judge_with_retry(
                judge=judge,
                dilemma=item["dilemma"],
                model_id=item["model_id"],
                temperature=CONFIG["temperature"],
                mode=item["mode"],
                variable_values=item["variable_values"],
            )

            if success:
                # Add experiment metadata
                judgement.experiment_id = CONFIG["experiment_id"]
                judgement.variation_key = item["variation_key"]

                # Save to database
                try:
                    async with AsyncSession(engine) as session:
                        judgement_db = JudgementDB.from_domain(judgement)
                        session.add(judgement_db)
                        await session.commit()

                    judgements_completed += 1

                    # Checkpoint logging
                    if judgements_completed % CHECKPOINT_EVERY == 0:
                        console.print(f"\n[green]✓ Checkpoint:[/green] {judgements_completed:,} / {total_judgements:,} completed")

                except Exception as e:
                    failures.append({
                        "model": item["model_id"],
                        "dilemma": item["dilemma"].title,
                        "mode": item["mode"],
                        "error": f"DB save failed: {str(e)}"
                    })
            else:
                failures.append({
                    "model": item["model_id"],
                    "dilemma": item["dilemma"].title,
                    "mode": item["mode"],
                    "error": error
                })

            progress.update(task, advance=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Running judgements...", total=len(experiment_plan))

        # Process in batches to avoid overwhelming event loop
        batch_size = 100
        for i in range(0, len(experiment_plan), batch_size):
            if shutdown_requested:
                break

            batch = experiment_plan[i:i + batch_size]
            await asyncio.gather(*[process_item(item, progress, task) for item in batch])

    # Summary
    console.print("\n" + "=" * 80)
    console.print("[bold green]✓ Experiment Complete![/bold green]")
    console.print("=" * 80)

    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Completed: [green]{judgements_completed:,}[/green] / {total_judgements:,} judgements")

    if failures:
        console.print(f"  Failures: [red]{len(failures)}[/red]")
        console.print("\n[yellow]Failed judgements:[/yellow]")
        for f in failures[:10]:  # Show first 10
            console.print(f"  • {f['model']} | {f['dilemma'][:40]} | {f['mode']}: {f['error'][:60]}")
        if len(failures) > 10:
            console.print(f"  ... and {len(failures) - 10} more")

    console.print(f"\n[bold]Export data:[/bold]")
    console.print(f"  uv run python ../../scripts/export_experiment_data.py {CONFIG['experiment_id']} data/")

    console.print(f"\n[bold]Analyze:[/bold]")
    console.print(f"  uv run python analyze.py")

    console.print("\n" + "=" * 80 + "\n")

    return 0


async def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv

    try:
        return await run_experiment(dry_run=dry_run)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
