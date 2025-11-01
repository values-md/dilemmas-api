#!/usr/bin/env python3
"""Clean orphaned judgements that reference deleted dilemmas.

Some judgements remain in the database after their dilemmas were deleted,
creating orphaned records that should be removed.

Usage:
    # Preview what will be deleted
    uv run python scripts/clean_orphaned_judgements.py

    # Actually delete
    uv run python scripts/clean_orphaned_judgements.py --delete
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()

# Local database
LOCAL_DB_PATH = Path(__file__).parent.parent / "data" / "dilemmas.db"
LOCAL_DB_URL = f"sqlite+aiosqlite:///{LOCAL_DB_PATH}"


async def clean_orphaned_judgements():
    """Remove judgements that reference non-existent dilemmas."""

    console.print("\n[bold cyan]🧹 Clean Orphaned Judgements[/bold cyan]")
    console.print("=" * 70)

    engine = create_async_engine(LOCAL_DB_URL, echo=False)

    try:
        async with AsyncSession(engine) as session:
            # Get all dilemma IDs
            result = await session.execute(select(DilemmaDB.id))
            dilemma_ids = {row[0] for row in result}
            console.print(f"\n[cyan]Found {len(dilemma_ids)} dilemmas in database[/cyan]")

            # Get all judgements
            result = await session.execute(select(JudgementDB))
            all_judgements = result.scalars().all()
            console.print(f"[cyan]Checking {len(all_judgements)} judgements...[/cyan]")

            # Find orphaned judgements
            orphaned = [j for j in all_judgements if j.dilemma_id not in dilemma_ids]

            if not orphaned:
                console.print("\n[green]✓ No orphaned judgements found - all clean![/green]")
                return 0

            console.print(f"\n[yellow]Found {len(orphaned)} orphaned judgements[/yellow]")

            # Group by dilemma_id
            from collections import Counter
            dilemma_counts = Counter(j.dilemma_id for j in orphaned)

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Missing Dilemma ID", style="red", max_width=38)
            table.add_column("Orphaned Judgements", justify="right")

            for dilemma_id, count in dilemma_counts.most_common():
                table.add_row(
                    dilemma_id,
                    str(count)
                )

            console.print(table)

            # Show experiment breakdown
            exp_counts = Counter(j.experiment_id for j in orphaned if j.experiment_id)
            if exp_counts:
                console.print("\n[bold]Orphaned judgements by experiment:[/bold]")
                for exp_id, count in exp_counts.most_common():
                    console.print(f"  • {exp_id}: {count}")

            # Check if --delete flag
            if "--delete" not in sys.argv:
                console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
                console.print("Run with --delete to actually remove orphaned judgements:")
                console.print("[dim]uv run python scripts/clean_orphaned_judgements.py --delete[/dim]")
                return 0

            # Delete them
            console.print(f"\n[bold]Deleting {len(orphaned)} orphaned judgements...[/bold]")

            for i, judgement in enumerate(orphaned, 1):
                await session.delete(judgement)
                if i % 50 == 0:
                    console.print(f"  Deleted {i}/{len(orphaned)}...")

            await session.commit()
            console.print(f"[green]✓ Deleted {len(orphaned)} orphaned judgements[/green]")

            # Verify
            console.print("\n[bold]Verifying cleanup...[/bold]")
            result = await session.execute(select(JudgementDB))
            all_judgements = result.scalars().all()

            still_orphaned = [j for j in all_judgements if j.dilemma_id not in dilemma_ids]

            if still_orphaned:
                console.print(f"[red]✗ Still have {len(still_orphaned)} orphaned judgements![/red]")
                return 1

            console.print(f"[green]✓ All {len(all_judgements)} judgements verified - no orphans[/green]")

    finally:
        await engine.dispose()

    console.print("\n[bold green]✅ Cleanup Complete![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Reset production: [cyan]uv run python scripts/reset_prod_completely.py --confirm[/cyan]")
    console.print("2. Re-sync: [cyan]uv run python scripts/sync_all_to_prod.py[/cyan]")
    console.print()

    return 0


async def main():
    """Main entry point."""
    try:
        return await clean_orphaned_judgements()
    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
