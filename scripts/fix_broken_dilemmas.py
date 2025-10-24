#!/usr/bin/env python3
"""Fix broken dilemmas that are missing concrete situation text.

This script will:
1. Identify dilemmas that have situation_template but rendering fails
2. Delete them from the database
3. Optionally regenerate fresh dilemmas to replace them

Usage:
    uv run python scripts/fix_broken_dilemmas.py --check          # Check for broken dilemmas
    uv run python scripts/fix_broken_dilemmas.py --delete         # Delete broken dilemmas
    uv run python scripts/fix_broken_dilemmas.py --delete --regenerate 37  # Delete and regenerate
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import json

from sqlmodel import select, delete

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB

async def check_dilemmas():
    """Check for broken dilemmas."""
    db = get_database()
    broken = []

    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        all_dilemmas = result.scalars().all()

        print(f"📊 Checking {len(all_dilemmas)} dilemmas...\n")

        for d in all_dilemmas:
            try:
                # Try to load as domain model
                dilemma = d.to_domain()

                # Try to render
                rendered = dilemma.render()

                # Check for corruption markers
                if '</parameter' in dilemma.title or '<parameter' in dilemma.title:
                    broken.append({
                        'id': d.id,
                        'title': dilemma.title[:100],
                        'reason': 'Corrupted title (XML tags)',
                    })
                elif not rendered or len(rendered) < 50:
                    broken.append({
                        'id': d.id,
                        'title': dilemma.title,
                        'reason': 'Rendering failed or too short',
                    })

            except Exception as e:
                broken.append({
                    'id': d.id,
                    'title': 'FAILED TO LOAD',
                    'reason': str(e),
                })

    await db.close()

    print(f"✓ Check complete: {len(all_dilemmas)} total, {len(broken)} broken\n")

    if broken:
        print("🔴 Broken dilemmas found:\n")
        for b in broken:
            print(f"ID: {b['id']}")
            print(f"  Title: {b['title']}")
            print(f"  Reason: {b['reason']}")
            print()
    else:
        print("✓ All dilemmas are valid!")

    return broken


async def delete_broken(dry_run=True):
    """Delete broken dilemmas."""
    broken = await check_dilemmas()

    if not broken:
        print("No broken dilemmas to delete.")
        return 0

    if dry_run:
        print(f"\n⚠️  DRY RUN - Would delete {len(broken)} dilemmas")
        return len(broken)

    db = get_database()
    broken_ids = [b['id'] for b in broken]

    async for session in db.get_session():
        # Delete by IDs
        for dilemma_id in broken_ids:
            statement = delete(DilemmaDB).where(DilemmaDB.id == dilemma_id)
            await session.execute(statement)

        await session.commit()
        print(f"\n✓ Deleted {len(broken_ids)} broken dilemmas")

    await db.close()
    return len(broken_ids)


async def main():
    parser = argparse.ArgumentParser(description="Fix broken dilemmas in database")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check for broken dilemmas, don't delete",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete broken dilemmas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--regenerate",
        type=int,
        metavar="COUNT",
        help="After deleting, regenerate this many dilemmas",
    )

    args = parser.parse_args()

    if args.check or (not args.delete):
        # Just check
        await check_dilemmas()
        return 0

    if args.delete:
        # Delete
        deleted_count = await delete_broken(dry_run=args.dry_run)

        if args.regenerate and not args.dry_run:
            print(f"\n🔄 Regenerating {args.regenerate} dilemmas...")
            print(f"   Run: uv run python scripts/generate_batch.py {args.regenerate}")

        return 0

    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
