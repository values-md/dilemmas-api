"""Retry variable extraction on dilemmas that failed.

This script re-runs extraction on dilemmas that have no variables,
using the updated prompt and GPT-4.1 Mini for better structured output.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator

console = Console()


async def main():
    console.print("\n[bold cyan]Retrying Variable Extraction[/bold cyan]")
    console.print("Using updated prompt + GPT-4.1 Mini\n")

    # Initialize generator
    generator = DilemmaGenerator()

    # Load dilemmas without variables
    db = get_database()
    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        dilemma_dbs = result.scalars().all()

        dilemmas = [d.to_domain() for d in dilemma_dbs]

        # Filter to ones without variables
        failed_dilemmas = [d for d in dilemmas if not d.variables]

        console.print(f"[yellow]Found {len(failed_dilemmas)} dilemmas without variables[/yellow]")

        if not failed_dilemmas:
            console.print("[green]All dilemmas already have variables![/green]")
            return

        console.print(f"[cyan]Will retry extraction on:[/cyan]")
        for i, d in enumerate(failed_dilemmas, 1):
            console.print(f"  {i}. {d.title[:60]}...")

        console.print()

        # Retry extraction
        success_count = 0
        still_failed = 0

        for i, dilemma in enumerate(failed_dilemmas, 1):
            console.print(f"\n[bold]{i}/{len(failed_dilemmas)}[/bold] {dilemma.title}")

            try:
                # Run extraction with new model
                updated_dilemma = await generator.variablize_dilemma(dilemma)

                if updated_dilemma.variables:
                    console.print(f"  [green]✓ Extracted {len(updated_dilemma.variables)} variables![/green]")
                    for placeholder in updated_dilemma.variables.keys():
                        console.print(f"    - {placeholder}")

                    # Update in database
                    dilemma_db = DilemmaDB.from_domain(updated_dilemma)
                    await session.merge(dilemma_db)
                    await session.commit()

                    success_count += 1
                else:
                    console.print(f"  [yellow]⚠ Still no variables extracted[/yellow]")
                    still_failed += 1

            except Exception as e:
                console.print(f"  [red]✗ Error: {e}[/red]")
                still_failed += 1

        # Summary
        console.print("\n" + "=" * 80)
        console.print(f"[bold green]Extraction Retry Complete![/bold green]")
        console.print(f"  Success: [green]{success_count}/{len(failed_dilemmas)}[/green]")
        console.print(f"  Still failed: [yellow]{still_failed}/{len(failed_dilemmas)}[/yellow]")

        if success_count > 0:
            console.print("\n[cyan]Check results:[/cyan]")
            console.print("  uv run python scripts/check_recent_dilemmas.py")


if __name__ == "__main__":
    asyncio.run(main())
