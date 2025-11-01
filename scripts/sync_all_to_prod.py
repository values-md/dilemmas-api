#!/usr/bin/env python3
"""Complete sync from local to production.

This script:
1. Runs Alembic migrations on production
2. Syncs all dilemmas from local to production
3. Syncs all judgements from local to production

Usage:
    # Dry run (preview what will be synced)
    uv run python scripts/sync_all_to_prod.py --dry-run

    # Actually sync
    uv run python scripts/sync_all_to_prod.py

    # Skip confirmation prompts
    uv run python scripts/sync_all_to_prod.py --yes
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()


def clean_database_url(url: str) -> str:
    """Clean database URL for asyncpg compatibility."""
    if "postgresql://" in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")
    if "channel_binding" in url:
        import urllib.parse
        parts = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parts.query)
        query_params.pop("channel_binding", None)
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        url = urllib.parse.urlunparse((
            parts.scheme, parts.netloc, parts.path,
            parts.params, new_query, parts.fragment
        ))
    return url


# Get database URLs
LOCAL_DB_PATH = Path(__file__).parent.parent / "data" / "dilemmas.db"
LOCAL_DB_URL = f"sqlite+aiosqlite:///{LOCAL_DB_PATH}"

PROD_DATABASE_URL = os.getenv("PROD_DATABASE_URL")
if not PROD_DATABASE_URL:
    console.print("[red]ERROR: PROD_DATABASE_URL not set in environment[/red]")
    sys.exit(1)

PROD_DATABASE_URL = clean_database_url(PROD_DATABASE_URL)


async def run_migrations():
    """Run Alembic migrations on production database."""
    console.print("\n[bold cyan]Step 1: Running Alembic Migrations[/bold cyan]")
    console.print("=" * 70)

    try:
        # Set environment variable for Alembic
        env = os.environ.copy()
        env["DATABASE_URL"] = os.getenv("PROD_DATABASE_URL")  # Original URL for Alembic

        # Run alembic upgrade
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print(f"[red]✗ Migration failed:[/red]")
            console.print(result.stderr)
            return False

        console.print("[green]✓ Migrations completed successfully[/green]")
        console.print(result.stdout)
        return True

    except Exception as e:
        console.print(f"[red]✗ Migration error: {e}[/red]")
        return False


async def sync_dilemmas(dry_run=False):
    """Sync dilemmas from local to production."""
    console.print("\n[bold cyan]Step 2: Syncing Dilemmas[/bold cyan]")
    console.print("=" * 70)

    # Connect to both databases
    local_engine = create_async_engine(LOCAL_DB_URL, echo=False)
    prod_engine = create_async_engine(PROD_DATABASE_URL, echo=False)

    try:
        async with AsyncSession(local_engine) as local_session, \
                   AsyncSession(prod_engine) as prod_session:

            # Get local dilemmas
            result = await local_session.execute(select(DilemmaDB))
            local_dilemmas = result.scalars().all()
            console.print(f"[cyan]Found {len(local_dilemmas)} dilemmas in local database[/cyan]")

            # Get production dilemmas
            result = await prod_session.execute(select(DilemmaDB))
            prod_dilemmas = result.scalars().all()
            prod_ids = {d.id for d in prod_dilemmas}
            console.print(f"[cyan]Found {len(prod_dilemmas)} dilemmas in production[/cyan]")

            # Find missing
            missing = [d for d in local_dilemmas if d.id not in prod_ids]
            console.print(f"\n[yellow]Need to sync {len(missing)} new dilemmas[/yellow]")

            if not missing:
                console.print("[green]✓ All dilemmas already in production[/green]")
                return True

            # Show preview
            if missing:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Title", style="cyan", max_width=40)
                table.add_column("Collection", style="yellow")
                table.add_column("Difficulty", justify="right")

                for d in missing[:10]:
                    table.add_row(
                        d.title[:37] + "..." if len(d.title) > 40 else d.title,
                        d.collection or "",
                        str(d.difficulty_intended)
                    )

                console.print(table)
                if len(missing) > 10:
                    console.print(f"[dim]... and {len(missing) - 10} more[/dim]")

            if dry_run:
                console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
                return True

            # Sync - need to convert to domain and back to create new instances
            console.print(f"\n[bold]Syncing {len(missing)} dilemmas...[/bold]")
            for i, dilemma_db in enumerate(missing, 1):
                # Convert to domain model and back to create new instance for prod session
                dilemma = dilemma_db.to_domain()
                new_dilemma_db = DilemmaDB.from_domain(dilemma)
                prod_session.add(new_dilemma_db)

                if i % 10 == 0:
                    console.print(f"  Added {i}/{len(missing)}...")

            await prod_session.commit()
            console.print(f"[green]✓ Successfully synced {len(missing)} dilemmas[/green]")
            return True

    except Exception as e:
        console.print(f"[red]✗ Dilemma sync error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False

    finally:
        await local_engine.dispose()
        await prod_engine.dispose()


async def sync_judgements(dry_run=False):
    """Sync judgements from local to production."""
    console.print("\n[bold cyan]Step 3: Syncing Judgements[/bold cyan]")
    console.print("=" * 70)

    # Connect to both databases
    local_engine = create_async_engine(LOCAL_DB_URL, echo=False)
    prod_engine = create_async_engine(PROD_DATABASE_URL, echo=False)

    try:
        async with AsyncSession(local_engine) as local_session, \
                   AsyncSession(prod_engine) as prod_session:

            # Get production dilemma IDs (only sync judgements for existing dilemmas)
            result = await prod_session.execute(select(DilemmaDB))
            prod_dilemma_ids = {d.id for d in result.scalars().all()}
            console.print(f"[cyan]Production has {len(prod_dilemma_ids)} dilemmas[/cyan]")

            # Get local judgements (filtered by dilemmas that exist in prod)
            result = await local_session.execute(select(JudgementDB))
            all_local_judgements = result.scalars().all()
            local_judgements = [
                j for j in all_local_judgements
                if j.dilemma_id in prod_dilemma_ids
            ]

            skipped = len(all_local_judgements) - len(local_judgements)
            if skipped > 0:
                console.print(f"[yellow]Skipped {skipped} judgements (dilemma not in prod)[/yellow]")

            console.print(f"[cyan]Found {len(local_judgements)} judgements in local database[/cyan]")

            # Get production judgements
            result = await prod_session.execute(select(JudgementDB))
            prod_judgements = result.scalars().all()
            prod_ids = {j.id for j in prod_judgements}
            console.print(f"[cyan]Found {len(prod_judgements)} judgements in production[/cyan]")

            # Find missing
            missing = [j for j in local_judgements if j.id not in prod_ids]
            console.print(f"\n[yellow]Need to sync {len(missing)} new judgements[/yellow]")

            if not missing:
                console.print("[green]✓ All judgements already in production[/green]")
                return True

            # Show preview
            if missing:
                # Group by experiment and model
                from collections import Counter
                experiments = Counter(j.experiment_id for j in missing if j.experiment_id)
                models = Counter(j.judge_id for j in missing)

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Experiment ID", style="cyan", max_width=38)
                table.add_column("Count", justify="right")

                for exp_id, count in experiments.most_common(5):
                    table.add_row(
                        exp_id[:35] + "..." if exp_id and len(exp_id) > 38 else exp_id or "(no experiment)",
                        str(count)
                    )

                console.print(table)
                if len(experiments) > 5:
                    console.print(f"[dim]... and {len(experiments) - 5} more experiments[/dim]")

                console.print(f"\nModels: {', '.join(models.keys())}")

            if dry_run:
                console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
                return True

            # Sync in batches - convert to domain and back to create new instances
            console.print(f"\n[bold]Syncing {len(missing)} judgements...[/bold]")
            batch_size = 100
            for i in range(0, len(missing), batch_size):
                batch = missing[i:i+batch_size]
                for judgement_db in batch:
                    # Convert to domain model and back to create new instance for prod session
                    judgement = judgement_db.to_domain()
                    new_judgement_db = JudgementDB.from_domain(judgement)
                    prod_session.add(new_judgement_db)

                await prod_session.commit()
                console.print(f"  Added {min(i+batch_size, len(missing))}/{len(missing)}...")

            console.print(f"[green]✓ Successfully synced {len(missing)} judgements[/green]")
            return True

    except Exception as e:
        console.print(f"[red]✗ Judgement sync error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False

    finally:
        await local_engine.dispose()
        await prod_engine.dispose()


async def main():
    """Main execution."""
    console.print()
    console.print("=" * 70)
    console.print("[bold]Complete Sync: Local → Production[/bold]")
    console.print("=" * 70)

    dry_run = "--dry-run" in sys.argv
    skip_confirm = "--yes" in sys.argv

    if dry_run:
        console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")

    # Step 1: Run migrations
    if not dry_run:
        success = await run_migrations()
        if not success:
            console.print("\n[red]✗ Migration failed - aborting sync[/red]")
            return 1
    else:
        console.print("\n[yellow]Skipping migrations in dry-run mode[/yellow]")

    # Step 2: Sync dilemmas
    success = await sync_dilemmas(dry_run=dry_run)
    if not success:
        console.print("\n[red]✗ Dilemma sync failed - aborting[/red]")
        return 1

    # Step 3: Sync judgements
    success = await sync_judgements(dry_run=dry_run)
    if not success:
        console.print("\n[red]✗ Judgement sync failed[/red]")
        return 1

    # Final summary
    console.print("\n" + "=" * 70)
    if dry_run:
        console.print("[bold yellow]DRY RUN COMPLETE[/bold yellow]")
        console.print("\nRun without --dry-run to actually sync:")
        console.print("[dim]uv run python scripts/sync_all_to_prod.py[/dim]")
    else:
        console.print("[bold green]✓ SYNC COMPLETE![/bold green]")
        console.print("\nProduction database is now up to date with local.")

    console.print("=" * 70)
    console.print()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
