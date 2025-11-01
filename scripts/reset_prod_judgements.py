"""Reset production judgements (keep dilemmas).

DESTRUCTIVE: This will delete all judgements from production database.
Dilemmas will be preserved.

Use this to clean up before fresh sync from local database.
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


async def reset_judgements():
    """Reset production judgements (keep dilemmas)."""

    console.print("\n[bold red]⚠️  DESTRUCTIVE OPERATION ⚠️[/bold red]")
    console.print("[bold cyan]Reset Production Judgements[/bold cyan]")
    console.print(f"[yellow]Database:[/yellow] {PROD_DATABASE_URL.split('@')[1].split('/')[0]}\n")

    async with AsyncSession(engine) as session:
        # Check current state
        result = await session.execute(select(DilemmaDB))
        dilemmas = result.scalars().all()

        result = await session.execute(select(JudgementDB))
        judgements = result.scalars().all()

        console.print("[bold]Current State:[/bold]")
        console.print(f"  • Dilemmas: {len(dilemmas)} [green](will be preserved)[/green]")
        console.print(f"  • Judgements: {len(judgements)} [red](will be DELETED)[/red]")
        console.print()

        if not judgements:
            console.print("[green]No judgements to delete - already clean[/green]")
            return 0

        # Show breakdown by experiment
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
            console.print("[yellow]To proceed with deletion, run with --confirm flag:[/yellow]")
            console.print("[dim]uv run python scripts/reset_prod_judgements.py --confirm[/dim]\n")
            console.print("[bold]After reset, sync from local with:[/bold]")
            console.print("[dim]uv run python scripts/sync_dilemmas_to_prod.py[/dim]")
            console.print("[dim]uv run python scripts/sync_judgements_to_prod.py --only-with-dilemmas[/dim]\n")
            return 1

        # Final confirmation in confirm mode
        console.print(f"[bold red]⚠️  ABOUT TO DELETE {len(judgements)} JUDGEMENTS ⚠️[/bold red]\n")

        # Actually delete
        console.print("[bold]Deleting judgements...[/bold]")
        await session.execute(delete(JudgementDB))
        await session.commit()

        # Verify deletion
        result = await session.execute(select(JudgementDB))
        remaining = result.scalars().all()

        if remaining:
            console.print(f"[red]✗ ERROR: {len(remaining)} judgements still remain![/red]")
            return 1

        console.print(f"[green]✓ Successfully deleted {len(judgements)} judgements[/green]")

        # Verify dilemmas preserved
        result = await session.execute(select(DilemmaDB))
        dilemmas_after = result.scalars().all()

        if len(dilemmas_after) != len(dilemmas):
            console.print(f"[red]✗ ERROR: Dilemma count changed! Before: {len(dilemmas)}, After: {len(dilemmas_after)}[/red]")
            return 1

        console.print(f"[green]✓ Preserved {len(dilemmas_after)} dilemmas[/green]")

    console.print("\n[bold green]Reset Complete![/bold green]")
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Wait for bench-1 experiment to complete")
    console.print("2. Run: [cyan]uv run python scripts/sync_dilemmas_to_prod.py[/cyan]")
    console.print("3. Run: [cyan]uv run python scripts/sync_judgements_to_prod.py --only-with-dilemmas[/cyan]\n")

    return 0


async def main():
    """Main entry point."""
    try:
        return await reset_judgements()
    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
