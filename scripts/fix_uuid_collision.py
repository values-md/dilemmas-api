"""Fix UUID collision between old GPT-4.1 experiment and bench-1 baseline.

The experiment_id b191388e-3994-4ebd-96cc-af0d033c5230 was accidentally reused.
This script migrates the 128 old GPT-4.1 judgements to a new UUID.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import JudgementDB

console = Console()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)

OLD_EXPERIMENT_ID = "b191388e-3994-4ebd-96cc-af0d033c5230"
NEW_OLD_EXPERIMENT_ID = str(uuid4())  # Generate new UUID for old experiment
CUTOFF_DATE = datetime(2025, 10, 29)  # Old judgements are before this date


async def find_old_judgements():
    """Find old GPT-4.1 judgements with collision UUID."""
    async with AsyncSession(engine) as session:
        # Find judgements matching old experiment criteria
        result = await session.execute(
            select(JudgementDB)
            .where(JudgementDB.experiment_id == OLD_EXPERIMENT_ID)
            .where(JudgementDB.created_at < CUTOFF_DATE)
        )
        old_judgements = result.scalars().all()

        return old_judgements


async def verify_and_migrate():
    """Main migration logic with verification."""

    console.print("\n[bold cyan]UUID Collision Fix[/bold cyan]")
    console.print(f"[yellow]Old experiment ID:[/yellow] {OLD_EXPERIMENT_ID}")
    console.print(f"[yellow]New experiment ID:[/yellow] {NEW_OLD_EXPERIMENT_ID}\n")

    # Step 1: Find old judgements
    console.print("[bold]Step 1: Finding old judgements...[/bold]")
    old_judgements = await find_old_judgements()

    if not old_judgements:
        console.print("[green]✓ No old judgements found with collision UUID[/green]")
        return 0

    console.print(f"[yellow]Found {len(old_judgements)} old judgements to migrate[/yellow]\n")

    # Step 2: Show sample
    console.print("[bold]Step 2: Sample of judgements to migrate:[/bold]")
    table = Table(show_header=True)
    table.add_column("Model", style="cyan")
    table.add_column("Dilemma", style="yellow")
    table.add_column("Mode", style="green")
    table.add_column("Created", style="magenta")

    for j in old_judgements[:5]:  # Show first 5
        domain = j.to_domain()
        model_id = domain.ai_judge.model_id if domain.judge_type == "ai" else "N/A"
        table.add_row(
            model_id,
            j.dilemma_id[:30] + "...",
            j.mode,
            j.created_at.strftime("%Y-%m-%d %H:%M")
        )

    console.print(table)

    if len(old_judgements) > 5:
        console.print(f"[dim]... and {len(old_judgements) - 5} more[/dim]\n")

    # Step 3: Show breakdown by model
    console.print("\n[bold]Step 3: Breakdown by model:[/bold]")
    from collections import Counter
    model_counts = Counter()
    for j in old_judgements:
        domain = j.to_domain()
        if domain.judge_type == "ai" and domain.ai_judge:
            model_counts[domain.ai_judge.model_id] += 1

    for model, count in sorted(model_counts.items()):
        console.print(f"  • {model}: {count} judgements")

    # Step 4: Ask for confirmation
    console.print(f"\n[bold red]⚠️  WARNING:[/bold red] This will update {len(old_judgements)} judgement records")
    console.print(f"[yellow]New UUID:[/yellow] {NEW_OLD_EXPERIMENT_ID}")
    console.print(f"[yellow]Database:[/yellow] {DATABASE_URL}\n")

    # Check for --confirm flag
    if "--confirm" not in sys.argv:
        console.print("[yellow]Run with --confirm flag to proceed with migration[/yellow]")
        console.print(f"[dim]Command: uv run python scripts/fix_uuid_collision.py --confirm[/dim]\n")
        return 1

    # Step 5: Perform migration
    console.print("\n[bold]Step 5: Migrating judgements...[/bold]")
    async with AsyncSession(engine) as session:
        # Reload judgements in this session
        result = await session.execute(
            select(JudgementDB)
            .where(JudgementDB.experiment_id == OLD_EXPERIMENT_ID)
            .where(JudgementDB.created_at < CUTOFF_DATE)
        )
        judgements_to_update = result.scalars().all()

        # Update experiment_id
        for judgement in judgements_to_update:
            judgement.experiment_id = NEW_OLD_EXPERIMENT_ID

        # Commit
        await session.commit()

        console.print(f"[green]✓ Migrated {len(judgements_to_update)} judgements[/green]")

    # Step 6: Verify migration
    console.print("\n[bold]Step 6: Verifying migration...[/bold]")

    # Check no old judgements remain with old UUID
    remaining_old = await find_old_judgements()

    if remaining_old:
        console.print(f"[red]✗ ERROR: {len(remaining_old)} old judgements still have old UUID![/red]")
        return 1

    console.print("[green]✓ No old judgements remain with collision UUID[/green]")

    # Check new judgements exist with new UUID
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(JudgementDB)
            .where(JudgementDB.experiment_id == NEW_OLD_EXPERIMENT_ID)
        )
        new_judgements = result.scalars().all()

    if len(new_judgements) != len(old_judgements):
        console.print(f"[red]✗ ERROR: Expected {len(old_judgements)} with new UUID, found {len(new_judgements)}[/red]")
        return 1

    console.print(f"[green]✓ Found {len(new_judgements)} judgements with new UUID[/green]")

    # Step 7: Check bench-1 baseline still intact
    console.print("\n[bold]Step 7: Verifying bench-1 baseline intact...[/bold]")
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(JudgementDB)
            .where(JudgementDB.experiment_id == OLD_EXPERIMENT_ID)
            .where(JudgementDB.created_at >= CUTOFF_DATE)
        )
        bench1_judgements = result.scalars().all()

    console.print(f"[green]✓ bench-1 baseline has {len(bench1_judgements)} judgements with original UUID[/green]")

    # Summary
    console.print("\n[bold green]Migration Complete![/bold green]")
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  • Old experiment UUID (migrated): {NEW_OLD_EXPERIMENT_ID}")
    console.print(f"  • Old judgements migrated: {len(new_judgements)}")
    console.print(f"  • bench-1 baseline UUID (unchanged): {OLD_EXPERIMENT_ID}")
    console.print(f"  • bench-1 judgements: {len(bench1_judgements)}")
    console.print(f"\n[yellow]Next steps:[/yellow]")
    console.print(f"  1. Document new UUID in old experiment README (if exists)")
    console.print(f"  2. Update research/index.md if needed")
    console.print(f"  3. If data was synced to production, run this script there too\n")

    return 0


async def main():
    """Main entry point."""
    try:
        return await verify_and_migrate()
    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
