#!/usr/bin/env python3
"""Sync local dilemmas to production database.

This script compares local dilemmas with production and pushes any that are missing.

Usage:
    # Dry run (preview what would be synced)
    uv run python scripts/sync_dilemmas_to_prod.py --dry-run

    # Actually sync (will ask for confirmation)
    uv run python scripts/sync_dilemmas_to_prod.py

    # Filter by collections (one or more)
    uv run python scripts/sync_dilemmas_to_prod.py --collections initial_experiments
    uv run python scripts/sync_dilemmas_to_prod.py --collections "initial_experiments,standard_v1"
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from dilemmas.models.db import DilemmaDB

# Load environment variables
load_dotenv()

console = Console()


async def get_prod_connection_string():
    """Get production database URL from environment."""
    prod_url = os.getenv("PROD_DATABASE_URL")
    if not prod_url:
        console.print("[red]ERROR: PROD_DATABASE_URL not found in environment[/red]")
        console.print("Add it to your .env file:")
        console.print("  PROD_DATABASE_URL=postgresql+asyncpg://user:pass@host/db")
        sys.exit(1)

    # Convert to async if needed
    if prod_url.startswith("postgresql://"):
        prod_url = prod_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not prod_url.startswith("postgresql+asyncpg://"):
        console.print(f"[yellow]Warning: Expected postgres URL, got: {prod_url[:20]}...[/yellow]")

    # Fix SSL parameters for asyncpg (convert sslmode to ssl)
    # Neon uses ?sslmode=require, but asyncpg doesn't understand sslmode
    if "sslmode=" in prod_url:
        prod_url = prod_url.replace("?sslmode=require", "?ssl=require")
        prod_url = prod_url.replace("&sslmode=require", "&ssl=require")

    # Remove channel_binding parameter (asyncpg doesn't support it)
    if "channel_binding=" in prod_url:
        # Remove &channel_binding=prefer or ?channel_binding=prefer
        import re
        prod_url = re.sub(r'[&?]channel_binding=[^&]*', '', prod_url)
        # Clean up any double & or trailing ?
        prod_url = prod_url.replace('&&', '&').rstrip('?&')

    return prod_url


async def get_local_connection_string():
    """Get local database URL."""
    db_path = Path(__file__).parent.parent / "data" / "dilemmas.db"
    return f"sqlite+aiosqlite:///{db_path}"


async def main():
    """Sync local dilemmas to production."""
    parser = argparse.ArgumentParser(description="Sync local dilemmas to production")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without syncing",
    )
    parser.add_argument(
        "--collections",
        type=str,
        help="Only sync dilemmas from these collections (comma-separated)",
    )

    args = parser.parse_args()

    # Print header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔄 Sync Local Dilemmas to Production[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    # Get connection strings
    local_url = await get_local_connection_string()
    prod_url = await get_prod_connection_string()

    console.print(f"[dim]Local:  {local_url}[/dim]")
    console.print(f"[dim]Remote: {prod_url[:50]}...[/dim]\n")

    # Create engines
    local_engine = create_async_engine(local_url)
    prod_engine = create_async_engine(prod_url)

    local_session_maker = sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
    prod_session_maker = sessionmaker(prod_engine, class_=AsyncSession, expire_on_commit=False)

    try:
        # Fetch local dilemmas
        console.print("[cyan]Fetching local dilemmas...[/cyan]")
        async with local_session_maker() as local_session:
            statement = select(DilemmaDB)
            if args.collections:
                collection_list = [c.strip() for c in args.collections.split(",")]
                statement = statement.where(DilemmaDB.collection.in_(collection_list))
                console.print(f"[dim]Filtering by collections: {', '.join(collection_list)}[/dim]")
            result = await local_session.execute(statement)
            local_dilemmas = result.scalars().all()

        console.print(f"[green]✓ Found {len(local_dilemmas)} local dilemmas[/green]")

        if not local_dilemmas:
            console.print("[yellow]No local dilemmas to sync.[/yellow]")
            return 0

        # Fetch production dilemma IDs
        console.print("[cyan]Fetching production dilemmas...[/cyan]")
        async with prod_session_maker() as prod_session:
            result = await prod_session.execute(select(DilemmaDB.id))
            prod_ids = set(result.scalars().all())

        console.print(f"[green]✓ Found {len(prod_ids)} production dilemmas[/green]\n")

        # Find missing dilemmas
        local_ids = {d.id for d in local_dilemmas}
        missing_ids = local_ids - prod_ids
        missing_dilemmas = [d for d in local_dilemmas if d.id in missing_ids]

        if not missing_dilemmas:
            console.print("[green]✓ All local dilemmas already exist in production![/green]")
            return 0

        # Show summary
        console.print(f"[bold yellow]Found {len(missing_dilemmas)} dilemmas to sync:[/bold yellow]\n")

        # Show table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Title", style="cyan", max_width=50)
        table.add_column("Collection", style="yellow")
        table.add_column("Difficulty", style="green", justify="center")
        table.add_column("Created", style="dim")

        for dilemma in missing_dilemmas[:20]:  # Show first 20
            table.add_row(
                dilemma.title[:47] + "..." if len(dilemma.title) > 50 else dilemma.title,
                dilemma.collection or "[dim](none)[/dim]",
                str(dilemma.difficulty_intended),
                dilemma.created_at.strftime("%Y-%m-%d"),
            )

        if len(missing_dilemmas) > 20:
            table.add_row("...", f"... and {len(missing_dilemmas) - 20} more", "", "")

        console.print(table)
        console.print()

        # Dry run?
        if args.dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
            console.print(f"Would sync {len(missing_dilemmas)} dilemmas to production.")
            return 0

        # Confirm
        console.print(f"[bold]This will add {len(missing_dilemmas)} dilemmas to production.[/bold]")
        console.print("[yellow]Existing dilemmas in production will NOT be modified.[/yellow]\n")

        if not Confirm.ask("Continue with sync?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return 0

        # Sync to production
        console.print("\n[cyan]Syncing to production...[/cyan]")
        async with prod_session_maker() as prod_session:
            for i, dilemma in enumerate(missing_dilemmas, 1):
                # Convert to domain model to get all fields populated correctly
                domain_dilemma = dilemma.to_domain()

                # Use from_domain to create properly populated DB instance
                prod_dilemma = DilemmaDB.from_domain(domain_dilemma)

                prod_session.add(prod_dilemma)

                if i % 10 == 0 or i == len(missing_dilemmas):
                    console.print(f"  Added {i}/{len(missing_dilemmas)}...")

            await prod_session.commit()

        console.print(f"\n[green]✓ Successfully synced {len(missing_dilemmas)} dilemmas to production![/green]")

    finally:
        await local_engine.dispose()
        await prod_engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
