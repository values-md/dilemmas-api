"""Theory vs Action Mode Experiment.

Research Question: Do LLMs make different ethical decisions when they believe
their actions are real (action mode) vs hypothetical (theory mode)?

Design:
- Dilemmas: 4 dilemmas with tools
- Conditions: theory mode vs action mode
- Model: GPT-4.1 Mini (temperature 1.0)
- Repetitions: 5 per condition per dilemma
- Total: 2 conditions × 4 dilemmas × 5 reps = 40 judgements
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.services.judge import DilemmaJudge

console = Console()

DATABASE_URL = "sqlite+aiosqlite:///data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)

# Experiment configuration
CONFIG = {
    "experiment_id": str(uuid.uuid4()),
    "name": "Theory vs Action Mode",
    "question": "Do LLMs make different decisions when they believe actions are real?",
    "model": "openai/gpt-4.1-mini",
    "temperature": 1.0,
    "repetitions": 5,
    "conditions": [
        {"mode": "theory", "description": "Hypothetical reasoning about what should be done"},
        {"mode": "action", "description": "Agent believes it's real and calls tools"},
    ],
    "dilemma_titles": [
        "The Carbon Confession",
        "Supply Chain Skills Assessment Transparency",
        "The Adaptive Voice Protocol",
        "The Dissertation Detection Dilemma",
    ],
}


async def run_experiment():
    """Run the theory vs action experiment."""
    console.print("\n[bold cyan]Theory vs Action Mode Experiment[/bold cyan]")
    console.print(f"[yellow]Experiment ID:[/yellow] {CONFIG['experiment_id']}\n")

    # Load dilemmas
    async with AsyncSession(engine) as session:
        dilemmas = []
        for title in CONFIG["dilemma_titles"]:
            result = await session.exec(select(DilemmaDB).where(DilemmaDB.title == title))
            dilemma_db = result.one()
            dilemmas.append(dilemma_db.to_domain())

    console.print(f"[green]✓[/green] Loaded {len(dilemmas)} dilemmas with tools")
    console.print(f"[yellow]Conditions:[/yellow] {len(CONFIG['conditions'])}")
    console.print(f"[yellow]Repetitions per condition:[/yellow] {CONFIG['repetitions']}")

    total_judgements = len(dilemmas) * len(CONFIG["conditions"]) * CONFIG["repetitions"]
    console.print(f"[yellow]Total judgements:[/yellow] {total_judgements}\n")

    # Confirm
    console.print("[bold yellow]Ready to run experiment?[/bold yellow]")
    console.print("This will make ~40 LLM calls and may take 3-5 minutes.\n")

    # Run judgements
    judge = DilemmaJudge()
    judgements = []
    failures = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Running judgements...", total=total_judgements)

        for dilemma in dilemmas:
            for condition in CONFIG["conditions"]:
                mode = condition["mode"]

                for rep in range(CONFIG["repetitions"]):
                    progress.update(
                        task,
                        description=f"[cyan]{dilemma.title[:30]}... | {mode} | rep {rep+1}/{CONFIG['repetitions']}"
                    )

                    try:
                        judgement = await judge.judge_dilemma(
                            dilemma=dilemma,
                            model_id=CONFIG["model"],
                            temperature=CONFIG["temperature"],
                            mode=mode,
                        )

                        # Add experiment metadata
                        judgement.experiment_id = CONFIG["experiment_id"]
                        judgement.repetition_number = rep + 1

                        # Save to database
                        async with AsyncSession(engine) as session:
                            judgement_db = JudgementDB.from_domain(judgement)
                            session.add(judgement_db)
                            await session.commit()

                        judgements.append(judgement)

                    except Exception as e:
                        failures.append({
                            "dilemma": dilemma.title,
                            "mode": mode,
                            "rep": rep + 1,
                            "error": str(e),
                        })
                        console.print(f"\n[red]✗ Error:[/red] {dilemma.title[:40]} | {mode} | {e}")

                    progress.advance(task)

    # Summary
    console.print(f"\n[bold green]✓ Experiment complete![/bold green]")
    console.print(f"[green]Successful:[/green] {len(judgements)}/{total_judgements}")

    if failures:
        console.print(f"[red]Failed:[/red] {len(failures)}/{total_judgements}")
        console.print("\n[yellow]Failures:[/yellow]")
        for f in failures[:5]:  # Show first 5
            console.print(f"  - {f['dilemma'][:40]} | {f['mode']} | {f['error'][:60]}")

    console.print(f"\n[cyan]Experiment ID:[/cyan] {CONFIG['experiment_id']}")
    console.print("[cyan]Next step:[/cyan] Run analysis script")

    return CONFIG["experiment_id"]


if __name__ == "__main__":
    experiment_id = asyncio.run(run_experiment())
    print(f"\nExperiment ID: {experiment_id}")
