#!/usr/bin/env python3
"""
Cleanup script: Remove 8 bad dilemmas from bench-1 collection and all associated judgements.

Based on: research/2025-10-29-when-agents-act/RECOVERY_PLAN.md
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

# Short IDs to remove (8-char prefix, 7 bad + 1 curated removal)
SHORT_IDS_TO_REMOVE = [
    "164d2e77",  # Autonomous Vehicle Software Update
    "4fb7edf5",  # Fitness Tracker Epidemic Protocol
    "581964f8",  # Predictive Policing Dilemma
    "5b145fd4",  # Refugee Hiring Dilemma
    "ca78c9da",  # Unconventional Language Coach
    "e412ea8a",  # Public Services Prioritization
    "fe1cd2e4",  # Species Tracker Disclosure
    "5b3dfe69",  # The Union Newsletter Dilemma (curation)
]

# Short IDs that should remain (for verification)
SHORT_IDS_TO_KEEP = [
    "14f8ce4e",  # Welfare Database Access (difficulty 2)
    "9d7aace2",  # Species Tracker Accuracy vs. Public Perception (difficulty 4)
    "9109f344",  # The Interpreter's Dilemma (difficulty 5)
    "99f37be6",  # Pricing Optimizer Dilemma: Revenue vs. Whistleblower (difficulty 5)
    "9e6123bf",  # Conflicting Data Disclosure (difficulty 6)
    "e6990090",  # Algorithm Audit Under Pressure (difficulty 7)
    "1cc47cff",  # Credit Scoring AI: The Glitch (difficulty 8)
    "1a14d9e0",  # Unattributed Art and Health Risks (difficulty 9)
    "57c6f938",  # The Echo Chamber Recommender (difficulty 9)
    "fda2e4c6",  # The Transparent Mind (difficulty 10)
]


def get_full_ids_from_short(short_ids, all_dilemmas):
    """Match short IDs (8-char prefix) to full UUIDs."""
    full_ids = []
    for short_id in short_ids:
        for dilemma in all_dilemmas:
            if dilemma.id.startswith(short_id):
                full_ids.append(dilemma.id)
                break
    return full_ids


async def get_all_dilemmas():
    """Get all dilemmas in bench-1."""
    async for session in db.get_session():
        stmt = select(DilemmaDB).where(DilemmaDB.collection == "bench-1")
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_counts_before(full_ids_to_remove):
    """Get counts before deletion."""
    async for session in db.get_session():
        # Total dilemmas in bench-1
        stmt = select(func.count()).select_from(DilemmaDB).where(DilemmaDB.collection == "bench-1")
        total_dilemmas = await session.scalar(stmt)

        # Judgements for dilemmas to remove
        stmt = select(func.count()).select_from(JudgementDB).where(
            JudgementDB.dilemma_id.in_(full_ids_to_remove)
        )
        judgements_to_remove = await session.scalar(stmt)

        # Total judgements
        stmt = select(func.count()).select_from(JudgementDB)
        total_judgements = await session.scalar(stmt)

        return total_dilemmas, judgements_to_remove, total_judgements


async def delete_dilemmas(full_ids_to_remove):
    """Delete dilemmas and associated judgements."""
    async for session in db.get_session():
        # Delete judgements first
        stmt = select(JudgementDB).where(JudgementDB.dilemma_id.in_(full_ids_to_remove))
        result = await session.execute(stmt)
        judgements = result.scalars().all()
        judgements_deleted = 0
        for judgement in judgements:
            await session.delete(judgement)
            judgements_deleted += 1

        # Delete dilemmas
        stmt = select(DilemmaDB).where(DilemmaDB.id.in_(full_ids_to_remove))
        result = await session.execute(stmt)
        dilemmas = result.scalars().all()
        dilemmas_deleted = 0
        for dilemma in dilemmas:
            await session.delete(dilemma)
            dilemmas_deleted += 1

        await session.commit()
        return dilemmas_deleted, judgements_deleted


async def validate_after(full_ids_to_remove):
    """Validate database state after deletion."""
    async for session in db.get_session():
        # Check dilemmas in bench-1
        stmt = select(DilemmaDB).where(DilemmaDB.collection == "bench-1")
        result = await session.execute(stmt)
        remaining = list(result.scalars().all())

        # Check for any judgements referencing deleted dilemmas
        stmt = select(func.count()).select_from(JudgementDB).where(
            JudgementDB.dilemma_id.in_(full_ids_to_remove)
        )
        orphaned = await session.scalar(stmt)

        # Total judgements remaining
        stmt = select(func.count()).select_from(JudgementDB)
        total_judgements = await session.scalar(stmt)

        return remaining, orphaned, total_judgements


async def main():
    console.print("\n[bold cyan]Phase 1: Database Cleanup & Validation (bench-1 only)[/bold cyan]\n")

    # Step 0: Resolve short IDs to full UUIDs
    console.print("[yellow]Step 0: Resolving IDs...[/yellow]")
    all_dilemmas = await get_all_dilemmas()
    full_ids_to_remove = get_full_ids_from_short(SHORT_IDS_TO_REMOVE, all_dilemmas)
    console.print(f"Resolved {len(full_ids_to_remove)}/{len(SHORT_IDS_TO_REMOVE)} IDs to full UUIDs")

    if len(full_ids_to_remove) != len(SHORT_IDS_TO_REMOVE):
        console.print(f"[red]Warning: Could not resolve all short IDs![/red]")
        missing = set(SHORT_IDS_TO_REMOVE) - {fid[:8] for fid in full_ids_to_remove}
        console.print(f"Missing: {missing}")

    # Step 1: Get counts before
    console.print("\n[yellow]Step 1: Getting counts before deletion...[/yellow]")
    total_dilemmas, judgements_to_remove, total_judgements = await get_counts_before(full_ids_to_remove)

    table = Table(title="Before Deletion (bench-1 collection)")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_row("Total dilemmas in bench-1", str(total_dilemmas))
    table.add_row("Dilemmas to remove", str(len(SHORT_IDS_TO_REMOVE)))
    table.add_row("Judgements for removed dilemmas", str(judgements_to_remove))
    table.add_row("Total judgements (all collections)", str(total_judgements))
    console.print(table)

    # Step 2: Confirm deletion
    console.print("\n[yellow]Step 2: Confirm deletion[/yellow]")
    console.print(f"This will delete {len(SHORT_IDS_TO_REMOVE)} dilemmas and ~{judgements_to_remove} judgements from bench-1.")
    console.print("\nDilemmas to remove:")
    for short_id in SHORT_IDS_TO_REMOVE:
        console.print(f"  - {short_id}")

    response = input("\nProceed with deletion? (yes/no): ")
    if response.lower() != "yes":
        console.print("[red]Aborted.[/red]")
        return

    # Step 3: Delete
    console.print("\n[yellow]Step 3: Deleting...[/yellow]")
    dilemmas_deleted, judgements_deleted = await delete_dilemmas(full_ids_to_remove)
    console.print(f"✅ Deleted {dilemmas_deleted} dilemmas")
    console.print(f"✅ Deleted {judgements_deleted} judgements")

    # Step 4: Validate
    console.print("\n[yellow]Step 4: Validating...[/yellow]")
    remaining, orphaned, total_judgements_after = await validate_after(full_ids_to_remove)

    table = Table(title="After Deletion")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Status", style="green")

    status_dilemmas = "✅" if len(remaining) == 10 else "❌"
    status_orphaned = "✅" if orphaned == 0 else "❌"

    table.add_row("Dilemmas in bench-1", str(len(remaining)), status_dilemmas)
    table.add_row("Orphaned judgements", str(orphaned), status_orphaned)
    table.add_row("Total judgements remaining", str(total_judgements_after), "")
    console.print(table)

    # Step 5: List remaining dilemmas
    console.print("\n[yellow]Step 5: Remaining dilemmas[/yellow]")
    remaining_table = Table(title="10 Clean Dilemmas (bench-1)")
    remaining_table.add_column("ID", style="cyan")
    remaining_table.add_column("Title", style="white")
    remaining_table.add_column("Difficulty", style="magenta")

    for dilemma in sorted(remaining, key=lambda d: d.difficulty_intended):
        domain_data = dilemma.to_domain()
        remaining_table.add_row(
            dilemma.id[:8],
            domain_data.title,
            str(dilemma.difficulty_intended)
        )

    console.print(remaining_table)

    # Final validation
    console.print("\n[bold green]Validation Results:[/bold green]")
    if len(remaining) == 10 and orphaned == 0:
        console.print("✅ Database cleanup successful!")
        console.print("✅ Exactly 10 dilemmas remain in bench-1")
        console.print("✅ No orphaned judgements")
        console.print(f"✅ {total_judgements_after} total judgements remaining (all collections)")

        # Check IDs match expected
        remaining_short_ids = {d.id[:8] for d in remaining}
        expected_short_ids = set(SHORT_IDS_TO_KEEP)
        if remaining_short_ids == expected_short_ids:
            console.print("✅ All remaining IDs match expected")
        else:
            console.print(f"⚠️  ID mismatch:")
            console.print(f"   Missing: {expected_short_ids - remaining_short_ids}")
            console.print(f"   Extra: {remaining_short_ids - expected_short_ids}")
    else:
        console.print("❌ Validation failed!")
        if len(remaining) != 10:
            console.print(f"   Expected 10 dilemmas, got {len(remaining)}")
        if orphaned > 0:
            console.print(f"   Found {orphaned} orphaned judgements")

    console.print("\n[bold cyan]Phase 1 Complete![/bold cyan]")
    console.print("Next: Run Phase 2 validation check")


if __name__ == "__main__":
    asyncio.run(main())
