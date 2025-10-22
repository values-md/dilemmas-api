#!/usr/bin/env python3
"""Check Claude-generated dilemmas in the database."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def main():
    """Check Claude dilemmas."""
    db = get_database()

    async for session in db.get_session():
        # Get Claude Sonnet dilemmas
        statement = select(DilemmaDB).where(DilemmaDB.created_by.like("%claude%"))
        result = await session.execute(statement)
        dilemmas = result.scalars().all()

        print(f"Found {len(dilemmas)} Claude dilemmas\n")

        for db_d in dilemmas[:5]:
            d = db_d.to_domain()
            print(f"=" * 80)
            print(f"Title: {d.title}")
            print(f"ID: {d.id}")
            print(f"Has variables: {len(d.variables) > 0} ({len(d.variables)} variables)")
            print(f"\nSituation (first 200 chars):")
            print(d.situation_template[:200] + "...")
            print(f"\nContains {{PLACEHOLDERS}}: {'{' in d.situation_template}")

            if d.variables:
                print(f"\nVariables found:")
                for var_name in list(d.variables.keys())[:3]:
                    print(f"  - {var_name}")
            print()

        break

    await db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
