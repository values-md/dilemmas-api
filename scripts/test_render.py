#!/usr/bin/env python3
"""Test rendering of dilemmas."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def main():
    """Test rendering."""
    db = get_database()

    async for session in db.get_session():
        # Get first Claude dilemma
        statement = select(DilemmaDB).where(DilemmaDB.created_by.like("%claude%")).limit(1)
        result = await session.execute(statement)
        db_d = result.scalar_one()
        d = db_d.to_domain()

        print(f"Title: {d.title}")
        print(f"\n{'='*80}")
        print("STORED TEMPLATE (first 300 chars):")
        print(f"{'='*80}")
        print(d.situation_template[:300] + "...")

        print(f"\n{'='*80}")
        print("RENDERED OUTPUT (first 300 chars):")
        print(f"{'='*80}")
        rendered = d.render()
        print(rendered[:300] + "...")

        print(f"\n{'='*80}")
        print("COMPARISON:")
        print(f"{'='*80}")
        if d.situation_template == rendered:
            print("⚠️  Template and rendered are IDENTICAL - no substitution happened!")
        else:
            print("✓ Template and rendered are DIFFERENT - substitution worked")

        print(f"\nVariables available: {len(d.variables)}")
        if d.variables:
            print("First variable:")
            first_key = list(d.variables.keys())[0]
            print(f"  {first_key}: {d.variables[first_key]}")

        break

    await db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
