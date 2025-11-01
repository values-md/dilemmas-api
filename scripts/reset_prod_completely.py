#!/usr/bin/env python3
"""Complete production database reset - DELETE ALL DATA.

DESTRUCTIVE: This will delete ALL dilemmas AND judgements from production.

Use this when you need to completely clean production and re-sync from local.

Usage:
    # Preview what will be deleted
    uv run python scripts/reset_prod_completely.py

    # Actually delete everything
    uv run python scripts/reset_prod_completely.py --confirm
"""

import asyncio
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from sqlmodel import select, delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()

# Get production database URL from env
PROD_DATABASE_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DATABASE_URL:
    console.print("[red]ERROR: PROD_DATABASE_URL not set in environment[/red]")
    console.print("[yellow]Set it in .env file[/yellow]")
    sys.exit(1)

# Clean URL for asyncpg
if "postgresql://" in PROD_DATABASE_URL:
    PROD_DATABASE_URL = PROD_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
if "sslmode=require" in PROD_DATABASE_URL:
    PROD_DATABASE_URL = PROD_DATABASE_URL.replace("sslmode=require", "ssl=require")
if "channel_binding" in PROD_DATABASE_URL:
    # Remove channel_binding parameter
    import urllib.parse
    parts = urllib.parse.urlparse(PROD_DATABASE_URL)
    query_params = urllib.parse.parse_qs(parts.query)
    query_params.pop("channel_binding", None)
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    PROD_DATABASE_URL = urllib.parse.urlunparse((
        parts.scheme, parts.netloc, parts.path,
        parts.params, new_query, parts.fragment
    ))

engine = create_async_engine(PROD_DATABASE_URL, echo=False)


async def reset_completely():
    """Complete production database reset - DELETE ALL DATA."""

    console.print("\n[bold red]⚠️  COMPLETE PRODUCTION RESET ⚠️[/bold red]")
    console.print("[bold cyan]This will DELETE ALL DATA from production![/bold cyan]")
    console.print(f"[yellow]Database:[/yellow] {PROD_DATABASE_URL.split('@')[1].split('/')[0]}\n")

    async with AsyncSession(engine) as session:
        # Check current state
        result = await session.execute(select(DilemmaDB))
        dilemmas = result.scalars().all()

        result = await session.execute(select(JudgementDB))
        judgements = result.scalars().all()

        console.print("[bold]Current Production State:[/bold]")
        console.print(f"  • Dilemmas: [red]{len(dilemmas)} (will be DELETED)[/red]")
        console.print(f"  • Judgements: [red]{len(judgements)} (will be DELETED)[/red]")
        console.print()

        if not dilemmas and not judgements:
            console.print("[green]Production is already empty - nothing to delete[/green]")
            return 0

        # Show breakdown by collection
        if dilemmas:
            from collections import Counter
            collections = Counter(d.collection for d in dilemmas if d.collection)
            if collections:
                console.print("[bold]Dilemmas by Collection:[/bold]")
                for coll, count in collections.most_common():
                    console.print(f"  • {coll}: {count}")
                console.print()

        # Show breakdown by experiment
        if judgements:
            from collections import Counter
            exp_ids = Counter(j.experiment_id for j in judgements if j.experiment_id)
            if exp_ids:
                console.print("[bold]Judgements by Experiment:[/bold]")
                for exp_id, count in exp_ids.most_common(5):
                    console.print(f"  • {exp_id[:36]}: {count}")
                if len(exp_ids) > 5:
                    console.print(f"  • ... and {len(exp_ids) - 5} more experiments")
                console.print()

        # Require --confirm flag
        if "--confirm" not in sys.argv:
            console.print("[yellow]To proceed with COMPLETE DELETION, run with --confirm flag:[/yellow]")
            console.print("[dim]uv run python scripts/reset_prod_completely.py --confirm[/dim]\n")
            console.print("[bold red]⚠️  THIS WILL DELETE ALL DATA ⚠️[/bold red]")
            console.print("[bold]After reset, re-sync with:[/bold]")
            console.print("[dim]uv run python scripts/sync_all_to_prod.py[/dim]\n")
            return 1

        # Final confirmation
        console.print(f"[bold red]⚠️  ABOUT TO DELETE {len(dilemmas)} DILEMMAS AND {len(judgements)} JUDGEMENTS ⚠️[/bold red]\n")

        # Delete judgements first (foreign key constraint)
        if judgements:
            console.print("[bold]Deleting judgements...[/bold]")
            await session.execute(delete(JudgementDB))
            console.print(f"[red]✓ Deleted {len(judgements)} judgements[/red]")

        # Delete dilemmas
        if dilemmas:
            console.print("[bold]Deleting dilemmas...[/bold]")
            await session.execute(delete(DilemmaDB))
            console.print(f"[red]✓ Deleted {len(dilemmas)} dilemmas[/red]")

        await session.commit()

        # Verify deletion
        result = await session.execute(select(DilemmaDB))
        remaining_dilemmas = result.scalars().all()

        result = await session.execute(select(JudgementDB))
        remaining_judgements = result.scalars().all()

        if remaining_dilemmas or remaining_judgements:
            console.print(f"[red]✗ ERROR: Some data still remains![/red]")
            console.print(f"  Dilemmas: {len(remaining_dilemmas)}")
            console.print(f"  Judgements: {len(remaining_judgements)}")
            return 1

        console.print(f"\n[green]✓ Production database completely reset[/green]")
        console.print(f"[green]✓ All {len(dilemmas)} dilemmas deleted[/green]")
        console.print(f"[green]✓ All {len(judgements)} judgements deleted[/green]")

    console.print("\n[bold green]Reset Complete![/bold green]")
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Run migrations and sync: [cyan]uv run python scripts/sync_all_to_prod.py[/cyan]\n")

    return 0


async def main():
    """Main entry point."""
    try:
        return await reset_completely()
    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
