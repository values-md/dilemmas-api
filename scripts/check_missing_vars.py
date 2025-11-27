#!/usr/bin/env python3
"""Check for missing variables in Claude dilemmas."""

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def main():
    """Check missing variables."""
    db = get_database()

    async for session in db.get_session():
        # Get Claude dilemmas
        statement = select(DilemmaDB).where(DilemmaDB.created_by.like("%claude%"))
        result = await session.execute(statement)
        dilemmas = result.scalars().all()

        for db_d in dilemmas:
            d = db_d.to_domain()

            # Find all placeholders in template
            placeholders = set(re.findall(r'\{([A-Z_]+)\}', d.situation_template))

            # Get variables that have values
            has_values = set(key.strip('{}') for key in d.variables.keys())

            # Find missing
            missing = placeholders - has_values

            print(f"\n{'='*80}")
            print(f"Title: {d.title}")
            print(f"{'='*80}")
            print(f"Placeholders in template: {len(placeholders)}")
            print(f"  {sorted(placeholders)}")
            print(f"\nVariables with values: {len(has_values)}")
            print(f"  {sorted(has_values)}")
            print(f"\n⚠️  MISSING VALUES: {len(missing)}")
            if missing:
                print(f"  {sorted(missing)}")

        break

    await db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
