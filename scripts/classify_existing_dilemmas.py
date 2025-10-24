#!/usr/bin/env python3
"""Classify institution_type for all existing dilemmas.

Usage:
    uv run python scripts/classify_existing_dilemmas.py
    uv run python scripts/classify_existing_dilemmas.py --dry-run  # Preview without saving
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.services.institution_classifier import classify_institution


async def main():
    """Classify all existing dilemmas."""
    parser = argparse.ArgumentParser(description="Classify institution type for existing dilemmas")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview classifications without saving to database",
    )
    args = parser.parse_args()

    print("🏛️  Classifying existing dilemmas...\n")
    if args.dry_run:
        print("   DRY RUN MODE - No changes will be saved\n")

    db = get_database()
    classified_count = 0
    skipped_count = 0
    updated = []

    async for session in db.get_session():
        # Load all dilemmas
        statement = select(DilemmaDB).order_by(DilemmaDB.created_at.desc())
        result = await session.execute(statement)
        db_dilemmas = result.scalars().all()

        print(f"📊 Found {len(db_dilemmas)} dilemmas\n")

        for i, db_dilemma in enumerate(db_dilemmas, 1):
            dilemma = db_dilemma.to_domain()

            # Skip if already classified
            if dilemma.institution_type:
                skipped_count += 1
                print(f"  [{i}/{len(db_dilemmas)}] ⏭️  Already classified: {dilemma.title[:50]}...")
                continue

            # Classify
            print(f"  [{i}/{len(db_dilemmas)}] 🔍 Classifying: {dilemma.title[:50]}...")

            institution_type = await classify_institution(dilemma.action_context)
            dilemma.institution_type = institution_type

            print(f"              → {institution_type}")

            # Update database
            if not args.dry_run:
                # Update the JSON data field directly
                db_dilemma.data = dilemma.model_dump_json()
                session.add(db_dilemma)

            classified_count += 1
            updated.append((dilemma.title, institution_type))

        # Commit all changes
        if not args.dry_run:
            await session.commit()
            print("\n💾 Changes committed to database")

    await db.close()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Classified: {classified_count}")
    print(f"⏭️  Skipped (already classified): {skipped_count}")
    print(f"📊 Total: {len(db_dilemmas)}")

    if updated:
        print("\n🏛️  Classifications applied:")
        institution_counts = {}
        for title, inst_type in updated:
            institution_counts[inst_type] = institution_counts.get(inst_type, 0) + 1

        for inst_type, count in sorted(institution_counts.items()):
            print(f"  {inst_type:12s}: {count:2d}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes were saved")
        print("   Run without --dry-run to save classifications")

    print("\n" + "=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
