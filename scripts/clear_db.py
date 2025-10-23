#!/usr/bin/env python3
"""Clear all dilemmas and judgements from the database.

Usage:
    uv run python scripts/clear_db.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB


async def main():
    """Clear all dilemmas and judgements from database."""
    db = get_database()

    # Count current records
    async for session in db.get_session():
        dilemma_result = await session.execute(select(DilemmaDB))
        dilemmas = dilemma_result.scalars().all()
        dilemma_count = len(dilemmas)

        judgement_result = await session.execute(select(JudgementDB))
        judgements = judgement_result.scalars().all()
        judgement_count = len(judgements)

    if dilemma_count == 0 and judgement_count == 0:
        print("Database is already empty.")
        await db.close()
        return 0

    print(f"Found {dilemma_count} dilemma(s) and {judgement_count} judgement(s) in database.")
    confirm = input(f"Delete all records? [y/N]: ").strip().lower()

    if confirm != "y":
        print("Cancelled.")
        await db.close()
        return 0

    # Delete all (delete judgements first due to foreign key)
    async for session in db.get_session():
        # Delete judgements first
        if judgement_count > 0:
            judgement_result = await session.execute(select(JudgementDB))
            judgements = judgement_result.scalars().all()
            for judgement in judgements:
                await session.delete(judgement)
            await session.commit()
            print(f"✓ Deleted {judgement_count} judgement(s).")

        # Then delete dilemmas
        if dilemma_count > 0:
            dilemma_result = await session.execute(select(DilemmaDB))
            dilemmas = dilemma_result.scalars().all()
            for dilemma in dilemmas:
                await session.delete(dilemma)
            await session.commit()
            print(f"✓ Deleted {dilemma_count} dilemma(s).")

    await db.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
