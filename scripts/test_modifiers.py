#!/usr/bin/env python3
"""Test modifier extraction in variable generation."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator


async def main():
    """Test modifier extraction."""
    db = get_database()

    # Clear database
    print("Clearing database...")
    count = 0
    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        dilemmas = result.scalars().all()
        count = len(dilemmas)

        for dilemma in dilemmas:
            await session.delete(dilemma)

        await session.commit()
        break

    print(f"Deleted {count} dilemma(s)\n")

    print("Generating test dilemma with variables and modifiers...")
    gen = DilemmaGenerator()
    dilemma = await gen.generate_random(difficulty=5, add_variables=True)

    print(f"\n{'='*60}")
    print(f"Generated: {dilemma.title}")
    print(f"{'='*60}")

    print(f"\n✓ Variables extracted: {len(dilemma.variables)}")
    if dilemma.variables:
        for var_name, values in list(dilemma.variables.items())[:3]:
            print(f"  • {var_name}: {values[:2]}{'...' if len(values) > 2 else ''}")

    print(f"\n✓ Modifiers extracted: {len(dilemma.modifiers)}")
    if dilemma.modifiers:
        print("\n  Modifiers:")
        for i, mod in enumerate(dilemma.modifiers, 1):
            print(f"    {i}. {mod}")
    else:
        print("  ⚠️  No modifiers extracted!")

    print(f"\nSaving to database...")
    async for session in db.get_session():
        db_dilemma = DilemmaDB.from_domain(dilemma)
        session.add(db_dilemma)
        await session.commit()
        break

    await db.close()
    print(f"✓ Saved! View at: http://localhost:8000/dilemma/{dilemma.id}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
