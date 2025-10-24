"""Review all dilemmas with tools."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from dilemmas.models.db import DilemmaDB

async def review():
    engine = create_async_engine("sqlite+aiosqlite:///data/dilemmas.db", echo=False)
    async with AsyncSession(engine) as session:
        result = await session.exec(select(DilemmaDB))
        dilemmas = [db.to_domain() for db in result.all()]

        valid = [
            d for d in dilemmas
            if d.available_tools and len(d.available_tools) == len(d.choices)
        ]

        print(f"\n{'='*80}")
        print(f"REVIEWING {len(valid)} DILEMMAS WITH TOOLS")
        print(f"{'='*80}\n")

        for i, d in enumerate(valid, 1):
            print(f"{i}. {d.title}")
            print(f"   Tags: {', '.join(d.tags)}")
            print(f"   Action context: {d.action_context[:80]}...")
            print(f"\n   Choices → Tools:")

            all_mapped = True
            for c in d.choices:
                tool = next((t for t in d.available_tools if t.name == c.tool_name), None)
                if tool:
                    print(f"      ✓ {c.id:20} → {c.tool_name}")
                else:
                    print(f"      ✗ {c.id:20} → {c.tool_name} (MISSING!)")
                    all_mapped = False

            if all_mapped:
                print(f"   Status: ✓ All tools mapped correctly")
            else:
                print(f"   Status: ✗ BROKEN MAPPINGS")
            print()

asyncio.run(review())
