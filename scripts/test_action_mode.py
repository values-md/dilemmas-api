"""Test action mode with a single dilemma.

This script verifies that action mode works correctly:
1. Agent receives a dilemma
2. Agent has access to execute_decision tool
3. Agent calls the tool with proper parameters
4. We successfully extract the decision
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.db.database import get_session
from dilemmas.models.db import DilemmaDB
from dilemmas.services.judge import DilemmaJudge

console = Console()

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)


async def test_action_mode():
    """Test action mode with one dilemma."""
    console.print("\n[bold cyan]Testing Action Mode[/bold cyan]\n")

    # Step 1: Get a dilemma from the database
    console.print("[yellow]Step 1:[/yellow] Loading a dilemma from database...")
    async with AsyncSession(engine) as session:
        # Get the first dilemma
        from sqlmodel import select
        result = await session.execute(select(DilemmaDB).limit(1))
        dilemma_db = result.scalar_one()
        dilemma = dilemma_db.to_domain()

    console.print(f"  ✓ Loaded: [green]{dilemma.title}[/green]")
    console.print(f"  Choices: {len(dilemma.choices)}")

    # Step 2: Run in ACTION mode
    console.print("\n[yellow]Step 2:[/yellow] Running judgement in ACTION mode...")
    console.print("  Model: [cyan]openai/gpt-4.1-mini[/cyan]")
    console.print("  Temperature: 1.0")
    console.print("  Mode: [magenta]action[/magenta] (agent believes it's real)\n")

    judge = DilemmaJudge()

    try:
        judgement = await judge.judge_dilemma(
            dilemma=dilemma,
            model_id="openai/gpt-4.1-mini",
            temperature=1.0,
            mode="action",  # ACTION MODE!
        )

        # Step 3: Display results
        console.print("[green]✓ Action mode successful![/green]\n")

        console.print(Panel.fit(
            f"[bold]Choice:[/bold] {judgement.choice_id}\n\n"
            f"[bold]Reasoning:[/bold]\n{judgement.reasoning}\n\n"
            f"[bold]Confidence:[/bold] {judgement.confidence}/10\n"
            f"[bold]Perceived Difficulty:[/bold] {judgement.perceived_difficulty}/10\n\n"
            f"[bold]Response Time:[/bold] {judgement.response_time_ms}ms",
            title="Action Mode Result",
            border_style="green"
        ))

        # Step 4: Compare with THEORY mode
        console.print("\n[yellow]Step 3:[/yellow] Running same dilemma in THEORY mode for comparison...")

        theory_judgement = await judge.judge_dilemma(
            dilemma=dilemma,
            model_id="openai/gpt-4.1-mini",
            temperature=1.0,
            mode="theory",  # THEORY MODE
        )

        console.print("[green]✓ Theory mode successful![/green]\n")

        console.print(Panel.fit(
            f"[bold]Choice:[/bold] {theory_judgement.choice_id}\n\n"
            f"[bold]Reasoning:[/bold]\n{theory_judgement.reasoning}\n\n"
            f"[bold]Confidence:[/bold] {theory_judgement.confidence}/10\n"
            f"[bold]Perceived Difficulty:[/bold] {theory_judgement.perceived_difficulty}/10\n\n"
            f"[bold]Response Time:[/bold] {theory_judgement.response_time_ms}ms",
            title="Theory Mode Result",
            border_style="blue"
        ))

        # Comparison
        console.print("\n[bold cyan]Comparison:[/bold cyan]")
        console.print(f"  Same choice? {'✓ Yes' if judgement.choice_id == theory_judgement.choice_id else '✗ No'}")
        console.print(f"  Action confidence: {judgement.confidence:.1f}")
        console.print(f"  Theory confidence: {theory_judgement.confidence:.1f}")
        console.print(f"  Action difficulty: {judgement.perceived_difficulty:.1f}")
        console.print(f"  Theory difficulty: {theory_judgement.perceived_difficulty:.1f}")

    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        console.print_exception()
        return False

    console.print("\n[bold green]✓ Action mode test complete![/bold green]")
    console.print("\nNext: Run theory vs action experiment across all dilemmas")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_action_mode())
    sys.exit(0 if success else 1)
