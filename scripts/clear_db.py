#!/usr/bin/env python3
"""Clear all dilemmas from the database.

Usage:
    uv run python scripts/clear_db.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def main():
    """Clear all dilemmas from database."""
    db = get_database()

    # Count current dilemmas
    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        dilemmas = result.scalars().all()
        count = len(dilemmas)

    if count == 0:
        print("Database is already empty.")
        await db.close()
        return 0

    print(f"Found {count} dilemma(s) in database.")
    confirm = input(f"Delete all {count} dilemma(s)? [y/N]: ").strip().lower()

    if confirm != "y":
        print("Cancelled.")
        await db.close()
        return 0

    # Delete all
    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        dilemmas = result.scalars().all()

        for dilemma in dilemmas:
            await session.delete(dilemma)

        await session.commit()

    await db.close()

    print(f"✓ Deleted {count} dilemma(s).")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
