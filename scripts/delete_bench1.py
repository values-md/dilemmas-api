#!/usr/bin/env python3
"""Delete all dilemmas from bench-1 collection."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.prompt import Confirm
from sqlalchemy import select, delete

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB

console = Console()


async def main():
    """List and optionally delete bench-1 dilemmas."""
    db = get_database()

    # List dilemmas
    async for session in db.get_session():
        result = await session.execute(
            select(DilemmaDB)
            .where(DilemmaDB.collection == "bench-1")
            .order_by(DilemmaDB.created_at)
        )
        dilemmas = result.scalars().all()

        if not dilemmas:
            console.print("[yellow]No dilemmas found in bench-1 collection.[/yellow]")
            return 0

        console.print(f"\n[bold]Found {len(dilemmas)} dilemmas in bench-1 collection:[/bold]\n")
        for d in dilemmas:
            dilemma = d.to_domain()
            console.print(f"  • {d.id[:8]}... | {dilemma.title[:60]}... | {d.created_at}")

        console.print()

        # Confirm deletion
        if not Confirm.ask(f"[red]Delete all {len(dilemmas)} dilemmas from bench-1?[/red]", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return 0

        # Delete
        await session.execute(
            delete(DilemmaDB).where(DilemmaDB.collection == "bench-1")
        )
        await session.commit()

        console.print(f"\n[green]✓ Deleted {len(dilemmas)} dilemmas from bench-1 collection.[/green]")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
