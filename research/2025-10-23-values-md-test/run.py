"""VALUES.md Impact Experiment: Does ethical guidance change LLM decisions?

This experiment tests whether providing a VALUES.md file influences how LLMs
make ethical decisions, and whether the style (formal vs personal) matters.

Conditions:
1. Control - No VALUES.md
2. Utilitarian (Formal) - Maximize welfare, academic language
3. Utilitarian (Personal) - Maximize welfare, personal voice
4. Deontological (Formal) - Rights/duties, academic language
5. Deontological (Personal) - Rights/duties, personal voice

Usage:
    uv run python scripts/run_values_md_experiment.py

Results:
    Experiment ID will be printed at the end
    Run: uv run python scripts/export_experiment_data.py <experiment_id> research/2025-10-23-values-md-test
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
    # Use all 10 dilemmas
    "num_dilemmas": 10,

    # Single model (control for model variance)
    "model": "openai/gpt-4.1-mini",

    # Single temperature (natural decision-making)
    "temperature": 1.0,

    # How many repetitions per (dilemma, condition) combination
    "repetitions": 3,

    # Mode
    "mode": "theory",

    # VALUES.md conditions to test
    # Format: (file_name, system_prompt_type, description)
    "conditions": [
        (None, "none", "Control (No VALUES.md)"),
        ("utilitarian-formal.md", "custom_values", "Utilitarian - Formal"),
        ("utilitarian-personal.md", "custom_values", "Utilitarian - Personal"),
        ("deontological-formal.md", "custom_values", "Deontological - Formal"),
        ("deontological-personal.md", "custom_values", "Deontological - Personal"),
    ],
}

# Path to VALUES.md files
VALUES_DIR = Path(__file__).parent.parent / "research" / "2025-10-23-values-md-test" / "values"


def load_values_file(file_name: str | None) -> str | None:
    """Load a VALUES.md file from the experiment directory.

    Args:
        file_name: Name of the VALUES.md file (e.g., "utilitarian-formal.md")
                   or None for control condition

    Returns:
        Content of the file, or None for control
    """
    if file_name is None:
        return None

    file_path = VALUES_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"VALUES.md file not found: {file_path}")

    return file_path.read_text()


async def run_values_md_experiment():
    """Run the VALUES.md impact experiment.

    For each (dilemma, condition) combination, run N repetitions
    and save all judgements with experiment tracking.
    """
    console.print("\n[bold cyan]VALUES.md Impact Experiment[/bold cyan]")
    console.print("Testing whether ethical guidance changes LLM decisions\n")

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
        config_table.add_row("Model", CONFIG["model"])
        config_table.add_row("Temperature", str(CONFIG["temperature"]))
        config_table.add_row("Conditions", str(len(CONFIG["conditions"])))
        config_table.add_row("Repetitions", str(CONFIG["repetitions"]))
        config_table.add_row("Total Judgements",
                           str(len(dilemmas) * len(CONFIG["conditions"]) * CONFIG["repetitions"]))

        console.print(config_table)
        console.print()

        # Show conditions
        conditions_table = Table(title="Test Conditions", show_header=True)
        conditions_table.add_column("#", style="cyan", width=3)
        conditions_table.add_column("Condition", style="yellow")
        conditions_table.add_column("File", style="green")

        for i, (file_name, _, description) in enumerate(CONFIG["conditions"], 1):
            conditions_table.add_row(
                str(i),
                description,
                file_name or "(none)"
            )

        console.print(conditions_table)
        console.print()

        # Initialize judge
        judge = DilemmaJudge()

        # Track progress
        total = len(dilemmas) * len(CONFIG["conditions"]) * CONFIG["repetitions"]
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
                for file_name, system_prompt_type, description in CONFIG["conditions"]:
                    # Load VALUES.md content
                    try:
                        system_prompt = load_values_file(file_name)
                    except FileNotFoundError as e:
                        console.print(f"[red]Error: {e}[/red]")
                        return

                    for rep in range(1, CONFIG["repetitions"] + 1):
                        try:
                            # Run judgement
                            judgement = await judge.judge_dilemma(
                                dilemma=dilemma,
                                model_id=CONFIG["model"],
                                temperature=CONFIG["temperature"],
                                mode=CONFIG["mode"],
                                system_prompt=system_prompt,
                                system_prompt_type=system_prompt_type,
                                values_file_name=file_name,
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
                                f"Error on {description} rep={rep} on {dilemma.title}: {e}"
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
        console.print(f"1. Export data: [cyan]uv run python scripts/export_experiment_data.py {experiment_id} research/2025-10-23-values-md-test[/cyan]")
        console.print(f"2. Analyze results: [cyan]cd research/2025-10-23-values-md-test && analyze...[/cyan]")
        console.print(f"3. View in web: [cyan]uv run python scripts/serve.py[/cyan]")


if __name__ == "__main__":
    asyncio.run(run_values_md_experiment())
