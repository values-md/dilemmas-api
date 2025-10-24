#!/usr/bin/env python3
"""Generate a batch of dilemmas and save to database.

Usage:
    uv run python scripts/generate_batch.py 30
    uv run python scripts/generate_batch.py 50 --difficulty-min 4 --difficulty-max 8
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator


async def main():
    """Generate batch of dilemmas."""
    parser = argparse.ArgumentParser(description="Generate batch of ethical dilemmas")
    parser.add_argument(
        "count",
        type=int,
        help="Number of dilemmas to generate",
    )
    parser.add_argument(
        "--difficulty-min",
        type=int,
        default=1,
        choices=range(1, 11),
        help="Minimum difficulty (1-10, default: 1)",
    )
    parser.add_argument(
        "--difficulty-max",
        type=int,
        default=10,
        choices=range(1, 11),
        help="Maximum difficulty (1-10, default: 10)",
    )
    parser.add_argument(
        "--prompt-version",
        type=str,
        default="v2_structured",
        choices=["v1_basic", "v2_structured", "v3_creative", "v4_adversarial", "v5_consequentialist", "v6_relational", "v7_systemic"],
        help="Prompt version to use",
    )

    args = parser.parse_args()

    if args.difficulty_min > args.difficulty_max:
        print("Error: difficulty-min must be <= difficulty-max")
        return 1

    print(f"🎲 Generating {args.count} dilemmas...")
    print(f"   Difficulty range: {args.difficulty_min}-{args.difficulty_max}")
    print(f"   Prompt version: {args.prompt_version}")
    print(f"   Ensuring diversity: Yes\n")

    # Create generator
    generator = DilemmaGenerator(prompt_version=args.prompt_version)

    # Generate batch
    print("Generating dilemmas (this may take a few minutes)...\n")

    dilemmas = await generator.generate_batch(
        count=args.count,
        difficulty_range=(args.difficulty_min, args.difficulty_max),
        ensure_diversity=True,
    )

    print(f"✓ Generated {len(dilemmas)} dilemmas\n")

    # Show success rate if any failed
    if len(dilemmas) < args.count:
        print(f"⚠️  Success rate: {len(dilemmas)}/{args.count} ({len(dilemmas)/args.count*100:.1f}%)")
        print(f"   {args.count - len(dilemmas)} dilemmas failed to generate\n")

    # Save to database
    print("💾 Saving to database...")
    db = get_database()
    saved_count = 0

    async for session in db.get_session():
        for i, dilemma in enumerate(dilemmas, 1):
            db_dilemma = DilemmaDB.from_domain(dilemma)
            session.add(db_dilemma)
            saved_count += 1

            # Progress indicator
            if i % 5 == 0 or i == len(dilemmas):
                print(f"   Saved {i}/{len(dilemmas)}...")

        await session.commit()

    await db.close()

    print(f"\n✓ All {saved_count} dilemmas saved to database!\n")

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Success stats
    print(f"\nGeneration:")
    print(f"  Requested: {args.count}")
    print(f"  Generated: {len(dilemmas)}")
    if len(dilemmas) < args.count:
        print(f"  Failed: {args.count - len(dilemmas)}")
        print(f"  Success rate: {len(dilemmas)/args.count*100:.1f}%")

    difficulty_counts = {}
    for d in dilemmas:
        diff = d.difficulty_intended
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

    print("\nDifficulty distribution:")
    for diff in sorted(difficulty_counts.keys()):
        bar = "█" * difficulty_counts[diff]
        print(f"  {diff:2d}/10: {bar} ({difficulty_counts[diff]})")

    print(f"\nSample titles:")
    for dilemma in dilemmas[:5]:
        print(f"  - {dilemma.title} (difficulty {dilemma.difficulty_intended}/10)")

    print(f"\nView all dilemmas:")
    print(f"  uv run python scripts/explore_db.py")
    print(f"  http://localhost:8001/dilemmas/dilemmas")

    print("\n" + "=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
