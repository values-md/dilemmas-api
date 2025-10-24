"""Check and optionally delete the mismatch dilemma."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from dilemmas.models.db import DilemmaDB

async def check():
    engine = create_async_engine("sqlite+aiosqlite:///data/dilemmas.db", echo=False)

    async with AsyncSession(engine) as session:
        result = await session.exec(select(DilemmaDB))
        dilemmas = [db.to_domain() for db in result.all()]

        # Find the mismatch
        mismatches = [
            d for d in dilemmas
            if d.available_tools and len(d.available_tools) != len(d.choices)
        ]

        if not mismatches:
            print("No mismatches found!")
            return

        print(f"Found {len(mismatches)} mismatches:\n")
        for d in mismatches:
            print(f"Title: {d.title}")
            print(f"ID: {d.id}")
            print(f"Tools: {len(d.available_tools)} - {[t.name for t in d.available_tools]}")
            print(f"Choices: {len(d.choices)} - {[c.id for c in d.choices]}")
            print()
            print("Options:")
            print("  1. Delete it (not useful for action mode)")
            print("  2. Keep it (experiments will skip it)")
            print()

            # For now, just report
            print("Recommendation: Delete (3 choices, 4 tools = cannot be fixed)")

asyncio.run(check())
