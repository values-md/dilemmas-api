#!/usr/bin/env python3
"""Generate research-focused dilemmas.

Forces generation with research-related domains and classifies as research institution type.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import random

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator
from dilemmas.services.seeds import DilemmaSeed, get_seed_library


async def main():
    """Generate research dilemmas."""
    print("🔬 Generating research dilemmas...\n")

    # Research-related domains to use
    research_domains = [
        "research_assistant",
        "plagiarism_detector",
        "curriculum_designer",
    ]

    generator = DilemmaGenerator()
    seed_library = get_seed_library()
    dilemmas = []

    count = 3
    for i in range(count):
        # Pick a research domain
        domain = research_domains[i % len(research_domains)]

        print(f"[{i+1}/{count}] Generating with domain: {domain}")

        # Create seed with research domain (manually construct it)
        difficulty = 6
        num_actors = 3
        num_stakes = 2

        # Calculate constraints
        if difficulty <= 3:
            num_constraints = random.randint(0, 1)
        elif difficulty <= 6:
            num_constraints = random.randint(1, 2)
        else:
            num_constraints = random.randint(2, 4)

        seed = DilemmaSeed(
            domain=domain,  # Force research domain
            actors=[actor.name for actor in random.sample(seed_library.actors, num_actors)],
            conflict=random.choice(seed_library.conflicts),
            constraints=random.sample(seed_library.constraints, min(num_constraints, len(seed_library.constraints))),
            stakes=random.sample(seed_library.stakes, min(num_stakes, len(seed_library.stakes))),
            moral_foundation=random.choice(seed_library.moral_foundations),
            difficulty_target=difficulty,
        )

        try:
            # Generate dilemma
            dilemma = await generator.generate_from_seed(seed)

            # Force institution type to research
            dilemma.institution_type = "research"

            dilemmas.append(dilemma)
            print(f"  ✓ Generated: {dilemma.title[:60]}...")

        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:100]}")
            continue

    if not dilemmas:
        print("\n✗ No dilemmas generated")
        return 1

    # Save to database
    print(f"\n💾 Saving {len(dilemmas)} dilemmas to database...")
    db = get_database()

    async for session in db.get_session():
        for dilemma in dilemmas:
            db_dilemma = DilemmaDB.from_domain(dilemma)
            session.add(db_dilemma)
        await session.commit()

    await db.close()

    print(f"✓ Saved {len(dilemmas)} research dilemmas!\n")

    # Summary
    for dilemma in dilemmas:
        print(f"  - {dilemma.title}")
        print(f"    Institution: {dilemma.institution_type}, Difficulty: {dilemma.difficulty_intended}/10")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
