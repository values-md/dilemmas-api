"""Test the judge service with 5 dilemmas and GPT-4.1 Mini."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.services.judge import DilemmaJudge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


async def main():
    """Run GPT-4.1 Mini on all dilemmas in theory mode."""
    console.print("\n[bold cyan]Testing Judge Service[/bold cyan]")
    console.print("Running GPT-4.1 Mini on all dilemmas (theory mode, no system prompt)\n")

    # Initialize judge
    judge = DilemmaJudge()

    # Model configuration
    model_id = "openai/gpt-4.1-mini"
    temperature = 1.0

    # Load all dilemmas from database
    db = get_database()
    async for session in db.get_session():
        result = await session.execute(select(DilemmaDB))
        dilemma_dbs = result.scalars().all()

        if not dilemma_dbs:
            console.print("[red]No dilemmas found in database![/red]")
            console.print("Run: [cyan]uv run python scripts/generate_batch_interactive.py[/cyan]")
            return

        dilemmas = [db.to_domain() for db in dilemma_dbs]
        console.print(f"[green]Found {len(dilemmas)} dilemmas in database[/green]\n")

        # Run judgements
        judgements = []

        for i, dilemma in enumerate(dilemmas, 1):
            console.print(f"[bold]{i}/{len(dilemmas)}[/bold] Judging: [cyan]{dilemma.title}[/cyan]")

            try:
                # Run the judgement
                judgement = await judge.judge_dilemma(
                    dilemma=dilemma,
                    model_id=model_id,
                    temperature=temperature,
                    mode="theory",
                    system_prompt_type="none",  # No system prompt - let dilemma provide context
                )

                # Save to database
                judgement_db = JudgementDB.from_domain(judgement)
                session.add(judgement_db)
                await session.commit()

                judgements.append(judgement)

                console.print(
                    f"  → Choice: [yellow]{judgement.choice_id}[/yellow] "
                    f"(confidence: {judgement.confidence:.1f}/10)"
                )
                console.print(f"  → Reasoning: {judgement.reasoning[:100]}...")
                console.print()

            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]\n")
                logger.exception(f"Failed to judge dilemma {dilemma.id}")
                continue

    # Summary
    console.print("\n[bold green]Summary[/bold green]")
    console.print(f"Total dilemmas: {len(dilemmas)}")
    console.print(f"Judgements collected: {len(judgements)}")
    console.print(f"Success rate: {len(judgements)/len(dilemmas)*100:.1f}%")

    if judgements:
        avg_confidence = sum(j.confidence for j in judgements) / len(judgements)
        console.print(f"Average confidence: {avg_confidence:.1f}/10")

        # Show choice distribution
        console.print("\n[bold]Choice Distribution:[/bold]")
        table = Table(show_header=True)
        table.add_column("Dilemma", style="cyan")
        table.add_column("Choice", style="yellow")
        table.add_column("Confidence", style="green")

        for judgement in judgements:
            # Find the dilemma
            dilemma = next((d for d in dilemmas if d.id == judgement.dilemma_id), None)
            if dilemma:
                table.add_row(
                    dilemma.title[:50],
                    judgement.choice_id,
                    f"{judgement.confidence:.1f}/10"
                )

        console.print(table)

    console.print("\n[bold cyan]Done![/bold cyan]")
    console.print("View results: [cyan]uv run python scripts/serve.py[/cyan]")


if __name__ == "__main__":
    asyncio.run(main())
