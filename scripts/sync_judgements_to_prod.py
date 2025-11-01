#!/usr/bin/env python3
"""Sync local judgements to production database.

This script compares local judgements with production and pushes any that are missing.

Usage:
    # Dry run (preview what would be synced)
    uv run python scripts/sync_judgements_to_prod.py --dry-run

    # Actually sync (will ask for confirmation)
    uv run python scripts/sync_judgements_to_prod.py

    # Skip confirmation prompt (non-interactive)
    uv run python scripts/sync_judgements_to_prod.py --yes

    # Filter by experiment ID
    uv run python scripts/sync_judgements_to_prod.py --experiment-id abc123...

    # Filter by dilemma collections
    uv run python scripts/sync_judgements_to_prod.py --collections "initial_experiments,standard_v1"

    # Only sync judgements for dilemmas that exist in prod
    uv run python scripts/sync_judgements_to_prod.py --only-with-dilemmas --yes
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

from dilemmas.models.db import DilemmaDB, JudgementDB

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
    """Sync local judgements to production."""
    parser = argparse.ArgumentParser(description="Sync local judgements to production")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without syncing",
    )
    parser.add_argument(
        "--experiment-id",
        type=str,
        help="Only sync judgements from this experiment",
    )
    parser.add_argument(
        "--collections",
        type=str,
        help="Only sync judgements for dilemmas in these collections (comma-separated)",
    )
    parser.add_argument(
        "--only-with-dilemmas",
        action="store_true",
        help="Only sync judgements where the dilemma exists in production",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    # Print header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔄 Sync Local Judgements to Production[/bold cyan]",
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
        # Fetch local judgements
        console.print("[cyan]Fetching local judgements...[/cyan]")
        async with local_session_maker() as local_session:
            # If filtering by collections, first get dilemma IDs from those collections
            dilemma_ids_filter = None
            if args.collections:
                collection_list = [c.strip() for c in args.collections.split(",")]
                console.print(f"[dim]Filtering by dilemma collections: {', '.join(collection_list)}[/dim]")
                dilemma_stmt = select(DilemmaDB.id).where(DilemmaDB.collection.in_(collection_list))
                dilemma_result = await local_session.execute(dilemma_stmt)
                dilemma_ids_filter = set(dilemma_result.scalars().all())
                console.print(f"[dim]Found {len(dilemma_ids_filter)} dilemmas in those collections[/dim]")

            statement = select(JudgementDB)
            if args.experiment_id:
                statement = statement.where(JudgementDB.experiment_id == args.experiment_id)
            if dilemma_ids_filter:
                statement = statement.where(JudgementDB.dilemma_id.in_(dilemma_ids_filter))

            result = await local_session.execute(statement)
            local_judgements = result.scalars().all()

        console.print(f"[green]✓ Found {len(local_judgements)} local judgements[/green]")

        if not local_judgements:
            console.print("[yellow]No local judgements to sync.[/yellow]")
            return 0

        # Fetch production data
        console.print("[cyan]Fetching production data...[/cyan]")
        async with prod_session_maker() as prod_session:
            # Get judgement IDs
            result = await prod_session.execute(select(JudgementDB.id))
            prod_judgement_ids = set(result.scalars().all())

            # Get dilemma IDs (if filtering)
            prod_dilemma_ids = None
            if args.only_with_dilemmas:
                result = await prod_session.execute(select(DilemmaDB.id))
                prod_dilemma_ids = set(result.scalars().all())

        console.print(f"[green]✓ Found {len(prod_judgement_ids)} production judgements[/green]")
        if prod_dilemma_ids is not None:
            console.print(f"[green]✓ Found {len(prod_dilemma_ids)} production dilemmas[/green]")
        console.print()

        # Find missing judgements
        local_ids = {j.id for j in local_judgements}
        missing_ids = local_ids - prod_judgement_ids
        missing_judgements = [j for j in local_judgements if j.id in missing_ids]

        # Filter by dilemma existence if requested
        if args.only_with_dilemmas and prod_dilemma_ids is not None:
            before_count = len(missing_judgements)
            missing_judgements = [
                j for j in missing_judgements
                if j.dilemma_id in prod_dilemma_ids
            ]
            skipped = before_count - len(missing_judgements)
            if skipped > 0:
                console.print(f"[yellow]Skipped {skipped} judgements (dilemma not in prod)[/yellow]\n")

        if not missing_judgements:
            console.print("[green]✓ All local judgements already exist in production![/green]")
            return 0

        # Show summary
        console.print(f"[bold yellow]Found {len(missing_judgements)} judgements to sync:[/bold yellow]\n")

        # Group by experiment_id
        by_experiment = {}
        for j in missing_judgements:
            exp_id = j.experiment_id or "(no experiment)"
            by_experiment.setdefault(exp_id, []).append(j)

        # Show table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Experiment ID", style="cyan", max_width=20)
        table.add_column("Model", style="yellow", max_width=30)
        table.add_column("Mode", style="green", justify="center")
        table.add_column("Count", style="white", justify="right")

        for exp_id, judgements in sorted(by_experiment.items()):
            models = set(j.judge_id for j in judgements)
            modes = set(j.mode for j in judgements)
            table.add_row(
                exp_id[:17] + "..." if len(exp_id) > 20 else exp_id,
                ", ".join(sorted(models)[:2]) if len(models) <= 2 else f"{len(models)} models",
                ", ".join(sorted(modes)),
                str(len(judgements)),
            )

        console.print(table)
        console.print()

        # Show sample judgements
        console.print("[bold]Sample judgements:[/bold]")
        for j in missing_judgements[:3]:
            # Parse domain model to get confidence
            judgement_obj = j.to_domain()
            console.print(f"  • {j.judge_id} → choice: {j.choice_id}, confidence: {judgement_obj.confidence:.1f}")
        if len(missing_judgements) > 3:
            console.print(f"  ... and {len(missing_judgements) - 3} more")
        console.print()

        # Dry run?
        if args.dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
            console.print(f"Would sync {len(missing_judgements)} judgements to production.")
            return 0

        # Confirm
        console.print(f"[bold]This will add {len(missing_judgements)} judgements to production.[/bold]")
        console.print("[yellow]Existing judgements in production will NOT be modified.[/yellow]\n")

        if not args.yes:
            try:
                if not Confirm.ask("Continue with sync?", default=False):
                    console.print("[yellow]Cancelled.[/yellow]")
                    return 0
            except EOFError:
                console.print("\n[yellow]No interactive terminal detected. Use --yes to confirm sync.[/yellow]")
                return 1

        # Sync to production
        console.print("\n[cyan]Syncing to production...[/cyan]")
        async with prod_session_maker() as prod_session:
            for i, judgement in enumerate(missing_judgements, 1):
                # Convert to domain model to get all fields populated correctly
                domain_judgement = judgement.to_domain()

                # Use from_domain to create properly populated DB instance
                prod_judgement = JudgementDB.from_domain(domain_judgement)

                prod_session.add(prod_judgement)

                if i % 50 == 0 or i == len(missing_judgements):
                    console.print(f"  Added {i}/{len(missing_judgements)}...")

            await prod_session.commit()

        console.print(f"\n[green]✓ Successfully synced {len(missing_judgements)} judgements to production![/green]")

    finally:
        await local_engine.dispose()
        await prod_engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
