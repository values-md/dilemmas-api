"""Check progress of bench-1 baseline experiment."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import JudgementDB

console = Console()

# Use absolute path to database (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)

# Target numbers
TOTAL_JUDGEMENTS = 12808
MODELS = ["openai/gpt-5", "anthropic/claude-sonnet-4.5", "google/gemini-2.5-pro", "x-ai/grok-4"]
MODES = ["theory", "action"]


async def check_progress(experiment_id: str):
    """Check progress of experiment."""
    async with AsyncSession(engine) as session:
        # Get total count
        result = await session.exec(
            select(func.count(JudgementDB.id))
            .where(JudgementDB.experiment_id == experiment_id)
        )
        total_count = result.one()

        # Get breakdown by model and mode
        result = await session.exec(
            select(JudgementDB)
            .where(JudgementDB.experiment_id == experiment_id)
        )
        judgements = result.all()

    # Analyze
    by_model = {model: {"theory": 0, "action": 0} for model in MODELS}

    for j in judgements:
        judgement = j.to_domain()
        if judgement.judge_type == "ai" and judgement.ai_judge:
            model_id = judgement.ai_judge.model_id
            mode = judgement.mode
            if model_id in by_model:
                by_model[model_id][mode] += 1

    # Display
    console.print(f"\n[bold cyan]bench-1 Baseline Progress[/bold cyan]")
    console.print(f"[yellow]Experiment ID:[/yellow] {experiment_id}\n")

    # Overall progress
    progress_pct = (total_count / TOTAL_JUDGEMENTS) * 100
    console.print(f"[bold]Overall Progress:[/bold] {total_count:,} / {TOTAL_JUDGEMENTS:,} ({progress_pct:.1f}%)")

    # Create table
    table = Table(title="Progress by Model & Mode")
    table.add_column("Model", style="cyan")
    table.add_column("Theory", justify="right", style="yellow")
    table.add_column("Action", justify="right", style="yellow")
    table.add_column("Total", justify="right", style="green")

    for model in MODELS:
        model_name = model.split("/")[-1]
        theory_count = by_model[model]["theory"]
        action_count = by_model[model]["action"]
        total = theory_count + action_count

        table.add_row(
            model_name,
            f"{theory_count:,}",
            f"{action_count:,}",
            f"{total:,}"
        )

    console.print()
    console.print(table)

    # Estimate remaining time
    if total_count > 0:
        # Assume 20 sec avg per judgement with 5 concurrent
        remaining = TOTAL_JUDGEMENTS - total_count
        remaining_seconds = (remaining / 5) * 20
        remaining_hours = remaining_seconds / 3600

        console.print(f"\n[bold]Estimated time remaining:[/bold] ~{remaining_hours:.1f} hours")

    console.print()


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        experiment_id = sys.argv[1]
    else:
        # Try to find most recent experiment
        async with AsyncSession(engine) as session:
            result = await session.exec(
                select(JudgementDB.experiment_id)
                .order_by(JudgementDB.created_at.desc())
                .limit(1)
            )
            experiment_id = result.first()

            if not experiment_id:
                console.print("[red]No experiments found. Provide experiment_id as argument.[/red]")
                return 1

    await check_progress(experiment_id)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
