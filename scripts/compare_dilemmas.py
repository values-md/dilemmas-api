#!/usr/bin/env python3
"""Compare two dilemmas to understand differences."""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from sqlalchemy import select

async def compare():
    db = get_database()

    # IDs from user
    id1 = "72b83ad5-46fe-4830-95cf-ede291bec644"  # No variables
    id2 = "23ce4f57-ab67-4cab-8bfc-a34658f3a351"  # Has variables

    async for session in db.get_session():
        d1_db = await session.get(DilemmaDB, id1)
        d2_db = await session.get(DilemmaDB, id2)

        d1 = d1_db.to_domain() if d1_db else None
        d2 = d2_db.to_domain() if d2_db else None

    if not d1 or not d2:
        print("One or both dilemmas not found")
        return

    print("=" * 80)
    print("DILEMMA 1 (NO VARIABLES)")
    print("=" * 80)
    print(f"Title: {d1.title}")
    print(f"Created by: {d1.created_by}")
    print(f"LLM Generated: {d1.is_llm_generated}")
    print(f"Generator Model: {d1.generator_model}")
    print(f"Prompt Version: {d1.generator_prompt_version}")
    print(f"\nVariables: {d1.variables}")
    print(f"Modifiers: {d1.modifiers}")
    print(f"Available Tools: {len(d1.available_tools)} tools")
    for tool in d1.available_tools:
        print(f"  - {tool.name}")

    print("\n" + "=" * 80)
    print("DILEMMA 2 (HAS VARIABLES)")
    print("=" * 80)
    print(f"Title: {d2.title}")
    print(f"Created by: {d2.created_by}")
    print(f"LLM Generated: {d2.is_llm_generated}")
    print(f"Generator Model: {d2.generator_model}")
    print(f"Prompt Version: {d2.generator_prompt_version}")
    print(f"\nVariables: {d2.variables}")
    print(f"Modifiers: {len(d2.modifiers) if d2.modifiers else 0} modifiers")
    print(f"Available Tools: {len(d2.available_tools)} tools")
    for tool in d2.available_tools:
        print(f"  - {tool.name}")

    print("\n" + "=" * 80)
    print("KEY DIFFERENCES")
    print("=" * 80)
    print(f"Variables: D1={bool(d1.variables)}, D2={bool(d2.variables)}")
    print(f"Modifiers: D1={bool(d1.modifiers)}, D2={bool(d2.modifiers)}")
    print(f"Tools: D1={len(d1.available_tools)}, D2={len(d2.available_tools)}")

    # Check generation settings
    print(f"\nGeneration Settings D1: {d1.generator_settings}")
    print(f"Generation Settings D2: {d2.generator_settings}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(compare())
