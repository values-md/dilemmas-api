#!/usr/bin/env python3
"""Label existing dilemmas with a collection name.

This script updates dilemmas in the database to add a collection label.

Usage:
    # Label all existing dilemmas
    uv run python scripts/label_collection.py "initial_experiments"

    # Label dilemmas created before a certain date
    uv run python scripts/label_collection.py "initial_experiments" --before "2025-10-29"

    # Label specific dilemmas by ID
    uv run python scripts/label_collection.py "pilot_study" --ids id1,id2,id3

    # Dry run (preview changes without applying)
    uv run python scripts/label_collection.py "test_set" --dry-run
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB

console = Console()


async def main():
    """Label dilemmas with collection name."""
    parser = argparse.ArgumentParser(description="Label dilemmas with collection name")
    parser.add_argument(
        "collection",
        type=str,
        help="Collection name to apply (e.g., 'initial_experiments', 'standard_v1')",
    )
    parser.add_argument(
        "--before",
        type=str,
        help="Only label dilemmas created before this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--after",
        type=str,
        help="Only label dilemmas created after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--ids",
        type=str,
        help="Comma-separated list of dilemma IDs to label",
    )
    parser.add_argument(
        "--unlabeled-only",
        action="store_true",
        help="Only label dilemmas that don't have a collection set",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )

    args = parser.parse_args()

    # Print welcome
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]🏷️  Label Dilemmas with Collection[/bold cyan]\n"
        f"Collection: [yellow]{args.collection}[/yellow]",
        border_style="cyan",
    ))
    console.print()

    # Build query
    db = get_database()
    statement = select(DilemmaDB)

    # Apply filters
    if args.before:
        before_date = datetime.strptime(args.before, "%Y-%m-%d")
        statement = statement.where(DilemmaDB.created_at < before_date)
        console.print(f"Filter: Created before {args.before}")

    if args.after:
        after_date = datetime.strptime(args.after, "%Y-%m-%d")
        statement = statement.where(DilemmaDB.created_at > after_date)
        console.print(f"Filter: Created after {args.after}")

    if args.ids:
        id_list = [id.strip() for id in args.ids.split(",")]
        statement = statement.where(DilemmaDB.id.in_(id_list))
        console.print(f"Filter: {len(id_list)} specific IDs")

    if args.unlabeled_only:
        statement = statement.where(DilemmaDB.collection.is_(None))
        console.print(f"Filter: Only unlabeled dilemmas")

    # Fetch matching dilemmas
    async for session in db.get_session():
        result = await session.execute(statement)
        dilemmas = result.scalars().all()

        if not dilemmas:
            console.print("[yellow]No dilemmas found matching criteria.[/yellow]")
            await db.close()
            return 0

        # Show preview
        console.print(f"\n[bold]Found {len(dilemmas)} dilemmas to label:[/bold]\n")

        # Show sample
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Title", style="cyan", max_width=40)
        table.add_column("Created", style="dim")
        table.add_column("Current Collection", style="yellow")

        for dilemma in dilemmas[:10]:  # Show first 10
            table.add_row(
                dilemma.id[:8] + "...",
                dilemma.title[:40],
                dilemma.created_at.strftime("%Y-%m-%d"),
                dilemma.collection or "[dim](none)[/dim]",
            )

        if len(dilemmas) > 10:
            table.add_row("...", f"... and {len(dilemmas) - 10} more", "", "")

        console.print(table)

        # Confirm or dry run
        if args.dry_run:
            console.print(f"\n[yellow]DRY RUN - No changes will be made[/yellow]")
            console.print(f"Would label {len(dilemmas)} dilemmas with collection: [bold]{args.collection}[/bold]")
            await db.close()
            return 0

        console.print(f"\n[bold]This will set collection=[yellow]{args.collection}[/yellow] for {len(dilemmas)} dilemmas.[/bold]")
        if not Confirm.ask("Continue?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            await db.close()
            return 0

        # Apply labels
        console.print(f"\n[cyan]Labeling dilemmas...[/cyan]")
        for dilemma in dilemmas:
            dilemma.collection = args.collection

            # Also update the JSON data
            domain_dilemma = dilemma.to_domain()
            domain_dilemma.collection = args.collection
            dilemma.data = domain_dilemma.model_dump_json()

        await session.commit()

        console.print(f"[green]✓ Successfully labeled {len(dilemmas)} dilemmas with collection '{args.collection}'[/green]")

    await db.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
