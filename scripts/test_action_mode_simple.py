"""Simple test of action mode with one dilemma."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB
from dilemmas.services.judge import DilemmaJudge

console = Console()

DATABASE_URL = "sqlite+aiosqlite:///data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)


async def test():
    """Test action mode with one dilemma."""
    console.print("\n[bold cyan]Testing Action Mode[/bold cyan]\n")

    # Load a dilemma with tools
    async with AsyncSession(engine) as session:
        result = await session.exec(
            select(DilemmaDB).where(DilemmaDB.title == "The Carbon Confession")
        )
        dilemma_db = result.one()
        dilemma = dilemma_db.to_domain()

    console.print(f"[yellow]Dilemma:[/yellow] {dilemma.title}")
    console.print(f"[yellow]Tools available:[/yellow] {len(dilemma.available_tools)}")
    console.print(f"[yellow]Choices:[/yellow] {len(dilemma.choices)}\n")

    # Show tool mappings
    console.print("[cyan]Tool mappings:[/cyan]")
    for choice in dilemma.choices:
        console.print(f"  {choice.id} → {choice.tool_name}")
    console.print()

    # Test in action mode
    console.print("[bold green]Running in ACTION mode...[/bold green]\n")

    judge = DilemmaJudge()

    try:
        judgement = await judge.judge_dilemma(
            dilemma=dilemma,
            model_id="openai/gpt-4.1-mini",
            temperature=1.0,
            mode="action",
        )

        console.print(Panel.fit(
            f"[bold]Choice:[/bold] {judgement.choice_id}\n\n"
            f"[bold]Reasoning:[/bold]\n{judgement.reasoning}\n\n"
            f"[bold]Confidence:[/bold] {judgement.confidence}/10\n"
            f"[bold]Difficulty:[/bold] {judgement.perceived_difficulty}/10\n\n"
            f"[bold]Response time:[/bold] {judgement.response_time_ms}ms",
            title="✓ Action Mode Result",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        console.print_exception()
        return False

    console.print("\n[green]✓ Action mode works![/green]")
    return True


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
