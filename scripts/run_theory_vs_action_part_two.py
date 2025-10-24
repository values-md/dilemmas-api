"""Theory vs Action Mode - Part Two: Robustness Test.

Research Question: Is the "tools make decisions easier" finding universal
across different models and dilemmas?

Design:
- Models: 6 models (mix of reasoning-capable and standard)
- Dilemmas: 10 dilemmas with tools
- Conditions: theory mode vs action mode
- Repetitions: 5 per condition
- Total: 6 models × 10 dilemmas × 2 modes × 5 reps = 600 judgements
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
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
    "name": "Theory vs Action Mode - Part Two: Robustness Test",
    "question": "Is the 'tools make decisions easier' finding universal?",
    "temperature": 1.0,
    "repetitions": 5,
    "models": [
        "openai/gpt-4.1-mini",      # Baseline (already tested in part one)
        "anthropic/claude-sonnet-4.5",  # Extended reasoning
        "google/gemini-2.5-flash",   # Multimodal reasoning
        "google/gemini-2.5-pro",     # Larger, more capable
        "deepseek/deepseek-chat-v3-0324",  # Reasoning capability
        "openai/gpt-4.1",            # Larger OpenAI model
    ],
    "conditions": [
        {"mode": "theory", "description": "Hypothetical reasoning"},
        {"mode": "action", "description": "Agent believes it's real, calls tools"},
    ],
    "target_dilemma_count": 10,  # Will use all available dilemmas with tools
}


async def run_experiment():
    """Run the theory vs action robustness experiment."""
    console.print("\n[bold cyan]Theory vs Action Mode - Part Two: Robustness Test[/bold cyan]")
    console.print(f"[yellow]Experiment ID:[/yellow] {CONFIG['experiment_id']}\n")

    # Load dilemmas with tools
    async with AsyncSession(engine) as session:
        result = await session.exec(select(DilemmaDB))
        all_dilemmas = [db.to_domain() for db in result.all()]
        # Filter: has tools AND tools count matches choices count
        dilemmas = [
            d for d in all_dilemmas
            if d.available_tools and len(d.available_tools) == len(d.choices)
        ]

    # Show dilemma inventory
    console.print(f"[green]✓[/green] Found {len(dilemmas)} dilemmas with tools\n")

    if len(dilemmas) < 10:
        console.print(f"[yellow]⚠ Warning:[/yellow] Only {len(dilemmas)} dilemmas with tools available.")
        console.print(f"[yellow]Target:[/yellow] 10 dilemmas")
        console.print(f"[yellow]Will proceed with {len(dilemmas)} dilemmas[/yellow]\n")

    # Show dilemmas
    table = Table(title="Dilemmas in Experiment")
    table.add_column("Title", style="cyan")
    table.add_column("Tools", justify="right", style="yellow")
    table.add_column("Choices", justify="right", style="green")

    for d in dilemmas[:10]:  # Use up to 10
        table.add_row(d.title[:50], str(len(d.available_tools)), str(len(d.choices)))

    console.print(table)
    console.print()

    # Use only first 10 dilemmas
    dilemmas = dilemmas[:10]

    # Calculate totals
    total_judgements = len(CONFIG["models"]) * len(dilemmas) * len(CONFIG["conditions"]) * CONFIG["repetitions"]

    console.print(f"[yellow]Models:[/yellow] {len(CONFIG['models'])}")
    for model in CONFIG["models"]:
        console.print(f"  - {model}")
    console.print(f"\n[yellow]Conditions:[/yellow] {len(CONFIG['conditions'])}")
    console.print(f"[yellow]Repetitions:[/yellow] {CONFIG['repetitions']}")
    console.print(f"[yellow]Total judgements:[/yellow] {total_judgements}\n")

    console.print("[bold yellow]Ready to run experiment?[/bold yellow]")
    console.print(f"This will make ~{total_judgements} LLM calls and may take 30-40 minutes.\n")

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

        for model_id in CONFIG["models"]:
            for dilemma in dilemmas:
                for condition in CONFIG["conditions"]:
                    mode = condition["mode"]

                    for rep in range(CONFIG["repetitions"]):
                        progress.update(
                            task,
                            description=f"[cyan]{model_id.split('/')[-1][:15]} | {dilemma.title[:20]}... | {mode} | {rep+1}/5"
                        )

                        try:
                            judgement = await judge.judge_dilemma(
                                dilemma=dilemma,
                                model_id=model_id,
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
                                "model": model_id,
                                "dilemma": dilemma.title,
                                "mode": mode,
                                "rep": rep + 1,
                                "error": str(e),
                            })
                            console.print(f"\n[red]✗ Error:[/red] {model_id.split('/')[-1]} | {dilemma.title[:30]} | {mode} | {str(e)[:60]}")

                        progress.advance(task)

    # Summary
    console.print(f"\n[bold green]✓ Experiment complete![/bold green]")
    console.print(f"[green]Successful:[/green] {len(judgements)}/{total_judgements}")

    if failures:
        console.print(f"[red]Failed:[/red] {len(failures)}/{total_judgements}")
        console.print(f"\n[yellow]Failure breakdown by model:[/yellow]")

        from collections import Counter
        model_failures = Counter([f['model'] for f in failures])
        for model, count in model_failures.most_common():
            console.print(f"  - {model}: {count} failures")

    console.print(f"\n[cyan]Experiment ID:[/cyan] {CONFIG['experiment_id']}")
    console.print("[cyan]Next steps:[/cyan]")
    console.print(f"  1. Export data: uv run python scripts/export_experiment_data.py {CONFIG['experiment_id']} research/2025-10-23-theory-vs-action-part-two/data")
    console.print(f"  2. Run analysis: uv run python research/2025-10-23-theory-vs-action-part-two/analyze.py")

    return CONFIG["experiment_id"]


if __name__ == "__main__":
    experiment_id = asyncio.run(run_experiment())
    print(f"\nExperiment ID: {experiment_id}")
