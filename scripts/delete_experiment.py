#!/usr/bin/env python3
"""Delete all judgements for a specific experiment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio
from rich.console import Console
from sqlalchemy import select, delete

from dilemmas.db.database import get_database
from dilemmas.models.db import JudgementDB

console = Console()

async def delete_experiment(experiment_id: str, dry_run: bool = False):
    """Delete all judgements for an experiment."""

    db = get_database()

    async for session in db.get_session():
        # First, count how many judgements will be deleted
        statement = select(JudgementDB).where(JudgementDB.experiment_id == experiment_id)
        result = await session.execute(statement)
        judgements = result.scalars().all()

        count = len(judgements)

        if count == 0:
            console.print(f"[yellow]No judgements found for experiment {experiment_id}[/yellow]")
            return

        console.print(f"\n[bold]Found {count} judgements for experiment:[/bold] [cyan]{experiment_id}[/cyan]")

        if dry_run:
            console.print("[yellow]DRY RUN - no changes made[/yellow]")
            return

        # Confirm deletion
        console.print(f"\n[red]⚠ This will permanently delete {count} judgements![/red]")
        confirm = input("Type 'DELETE' to confirm: ")

        if confirm != "DELETE":
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Delete
        delete_statement = delete(JudgementDB).where(JudgementDB.experiment_id == experiment_id)
        await session.execute(delete_statement)
        await session.commit()

        console.print(f"[green]✓ Deleted {count} judgements[/green]")

    await db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[red]Usage: uv run python scripts/delete_experiment.py <experiment_id> [--dry-run][/red]")
        sys.exit(1)

    experiment_id = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    asyncio.run(delete_experiment(experiment_id, dry_run=dry_run))
