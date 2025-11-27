#!/usr/bin/env python3
"""
Delete fda2e4c6 (The Transparent Mind) from bench-1 collection.

Reason: Variable mismatch - hardcodes "transparent" when {LEDGER_TYPE} varies
Date: 2025-11-21
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select, func
from rich.console import Console
from rich.table import Table

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()
db = get_database()

DILEMMA_ID_TO_DELETE = "fda2e4c6"  # Short ID prefix


async def main():
    console.print("\n[bold cyan]Delete fda2e4c6 (The Transparent Mind)[/bold cyan]\n")
    console.print("[yellow]Reason:[/yellow] Variable mismatch - hardcodes 'transparent' when {LEDGER_TYPE} varies\n")

    # Step 1: Find full ID
    console.print("[yellow]Step 1: Finding full UUID...[/yellow]")
    async for session in db.get_session():
        stmt = select(DilemmaDB).where(
            DilemmaDB.collection == "bench-1",
            DilemmaDB.id.like(f"{DILEMMA_ID_TO_DELETE}%")
        )
        result = await session.execute(stmt)
        dilemma = result.scalar_one_or_none()

        if not dilemma:
            console.print(f"[red]Error: Dilemma {DILEMMA_ID_TO_DELETE} not found![/red]")
            return

        full_id = dilemma.id
        domain = dilemma.to_domain()
        console.print(f"Found: {full_id[:8]} - {domain.title}")
        break

    # Step 2: Count judgements
    console.print("\n[yellow]Step 2: Counting judgements...[/yellow]")
    async for session in db.get_session():
        stmt = select(func.count()).select_from(JudgementDB).where(
            JudgementDB.dilemma_id == full_id
        )
        judgement_count = await session.scalar(stmt)
        console.print(f"Found {judgement_count} judgements for this dilemma")
        break

    # Step 3: Confirm
    console.print("\n[yellow]Step 3: Confirm deletion[/yellow]")
    console.print(f"This will delete:")
    console.print(f"  - 1 dilemma: {domain.title}")
    console.print(f"  - {judgement_count} judgements")
    console.print(f"\nFinal bench-1 count will be: 9 dilemmas")

    response = input("\nProceed with deletion? (yes/no): ")
    if response.lower() != "yes":
        console.print("[red]Aborted.[/red]")
        return

    # Step 4: Delete
    console.print("\n[yellow]Step 4: Deleting...[/yellow]")
    async for session in db.get_session():
        # Delete judgements first
        stmt = select(JudgementDB).where(JudgementDB.dilemma_id == full_id)
        result = await session.execute(stmt)
        judgements = result.scalars().all()
        for judgement in judgements:
            await session.delete(judgement)

        # Delete dilemma
        stmt = select(DilemmaDB).where(DilemmaDB.id == full_id)
        result = await session.execute(stmt)
        dilemma_to_delete = result.scalar_one()
        await session.delete(dilemma_to_delete)

        await session.commit()
        console.print(f"✅ Deleted 1 dilemma")
        console.print(f"✅ Deleted {len(judgements)} judgements")
        break

    # Step 5: Verify
    console.print("\n[yellow]Step 5: Verifying final state...[/yellow]")
    async for session in db.get_session():
        # Count remaining dilemmas
        stmt = select(func.count()).select_from(DilemmaDB).where(
            DilemmaDB.collection == "bench-1"
        )
        remaining_count = await session.scalar(stmt)

        # List remaining dilemmas
        stmt = select(DilemmaDB).where(DilemmaDB.collection == "bench-1")
        result = await session.execute(stmt)
        remaining = result.scalars().all()

        table = Table(title="Final 9 Clean Dilemmas")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Difficulty", style="magenta")

        for d in sorted(remaining, key=lambda x: x.difficulty_intended):
            domain = d.to_domain()
            table.add_row(d.id[:8], domain.title, str(d.difficulty_intended))

        console.print(table)

        if remaining_count == 9:
            console.print("\n[bold green]✅ Success! bench-1 now has 9 clean dilemmas[/bold green]")
        else:
            console.print(f"\n[red]⚠️  Warning: Expected 9 dilemmas, got {remaining_count}[/red]")
        break

    await db.close()
    console.print("\n[bold cyan]Deletion complete![/bold cyan]")


if __name__ == "__main__":
    asyncio.run(main())
