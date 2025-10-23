"""Test consistency of LLM judgements across repetitions.

This script runs the same model on the same dilemma multiple times at different
temperatures to measure:
1. Choice consistency: How often does it pick the same choice?
2. Reasoning similarity: How similar is the reasoning text?
3. Confidence variation: How stable are confidence scores?

Usage:
    uv run python scripts/test_consistency.py

Configuration:
    Edit the CONFIG section below to:
    - Select which dilemmas to test
    - Choose models and temperatures
    - Set number of repetitions per condition
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.services.judge import DilemmaJudge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================

CONFIG = {
    # How many dilemmas to test (takes first N from database)
    "num_dilemmas": 3,

    # Which models to test
    "models": [
        "openai/gpt-4.1-mini",
        "google/gemini-2.5-flash",
    ],

    # Which temperatures to test
    "temperatures": [0.0, 0.5, 1.0, 1.5],

    # How many repetitions per (model, dilemma, temperature) combination
    "repetitions": 10,

    # Mode (theory only for now)
    "mode": "theory",

    # System prompt type
    "system_prompt_type": "none",
}


async def run_consistency_experiment():
    """Run the consistency experiment.

    For each (model, dilemma, temperature) combination, run N repetitions
    and save all judgements with experiment tracking.
    """
    console.print("\n[bold cyan]LLM Consistency Testing Experiment[/bold cyan]")
    console.print("Testing how consistent LLM judgements are across repetitions\n")

    # Generate experiment ID
    experiment_id = str(uuid.uuid4())
    console.print(f"[green]Experiment ID:[/green] {experiment_id}\n")

    # Load dilemmas from database
    db = get_database()
    async for session in db.get_session():
        result = await session.execute(select(DilemmaDB).limit(CONFIG["num_dilemmas"]))
        dilemma_dbs = result.scalars().all()

        if not dilemma_dbs:
            console.print("[red]No dilemmas found in database![/red]")
            console.print("Run: [cyan]uv run python scripts/generate_batch_interactive.py[/cyan]")
            return

        dilemmas = [db.to_domain() for db in dilemma_dbs]
        console.print(f"[green]Testing {len(dilemmas)} dilemmas[/green]")

        # Show configuration
        config_table = Table(title="Experiment Configuration", show_header=True)
        config_table.add_column("Parameter", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Dilemmas", str(len(dilemmas)))
        config_table.add_row("Models", ", ".join(CONFIG["models"]))
        config_table.add_row("Temperatures", ", ".join(map(str, CONFIG["temperatures"])))
        config_table.add_row("Repetitions", str(CONFIG["repetitions"]))
        config_table.add_row("Total Judgements",
                           str(len(dilemmas) * len(CONFIG["models"]) *
                               len(CONFIG["temperatures"]) * CONFIG["repetitions"]))

        console.print(config_table)
        console.print()

        # Initialize judge
        judge = DilemmaJudge()

        # Track progress
        total = (len(dilemmas) * len(CONFIG["models"]) *
                len(CONFIG["temperatures"]) * CONFIG["repetitions"])
        completed = 0
        errors = 0

        # Run experiments
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Running judgements...", total=total)

            for dilemma in dilemmas:
                for model_id in CONFIG["models"]:
                    for temperature in CONFIG["temperatures"]:
                        for rep in range(1, CONFIG["repetitions"] + 1):
                            try:
                                # Run judgement
                                judgement = await judge.judge_dilemma(
                                    dilemma=dilemma,
                                    model_id=model_id,
                                    temperature=temperature,
                                    mode=CONFIG["mode"],
                                    system_prompt_type=CONFIG["system_prompt_type"],
                                )

                                # Add experiment tracking
                                judgement.experiment_id = experiment_id
                                judgement.repetition_number = rep

                                # Save to database
                                judgement_db = JudgementDB.from_domain(judgement)
                                session.add(judgement_db)
                                await session.commit()

                                completed += 1

                            except Exception as e:
                                logger.error(
                                    f"Error on {model_id} (temp={temperature}) "
                                    f"rep={rep} on {dilemma.title}: {e}"
                                )
                                errors += 1

                            progress.update(task, advance=1)

        # Summary
        console.print("\n[bold green]Experiment Complete![/bold green]")
        console.print(f"Experiment ID: [cyan]{experiment_id}[/cyan]")
        console.print(f"Successful judgements: [green]{completed}[/green]")
        console.print(f"Errors: [red]{errors}[/red]")
        console.print(f"Success rate: {completed/total*100:.1f}%")

        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"1. Analyze results: [cyan]uv run python scripts/analyze_consistency.py {experiment_id}[/cyan]")
        console.print(f"2. View in web: [cyan]uv run python scripts/serve.py[/cyan]")


if __name__ == "__main__":
    asyncio.run(run_consistency_experiment())
