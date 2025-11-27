#!/usr/bin/env python3
"""Label all existing dilemmas without a collection as 'initial_experiments'."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from sqlmodel import select


async def main():
    """Label all unlabeled dilemmas."""
    db = get_database()

    async for session in db.get_session():
        # Find all dilemmas without a collection
        statement = select(DilemmaDB).where(DilemmaDB.collection.is_(None))
        result = await session.execute(statement)
        dilemmas = result.scalars().all()

        if not dilemmas:
            print("✓ No unlabeled dilemmas found.")
            await db.close()
            return 0

        print(f"Found {len(dilemmas)} unlabeled dilemmas.")
        print("Labeling as 'initial_experiments'...\n")

        for dilemma in dilemmas:
            dilemma.collection = "initial_experiments"
            # Also update the JSON data
            domain_dilemma = dilemma.to_domain()
            domain_dilemma.collection = "initial_experiments"
            dilemma.data = domain_dilemma.model_dump_json()

        await session.commit()
        print(f"✓ Successfully labeled {len(dilemmas)} dilemmas with collection='initial_experiments'!")

    await db.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
