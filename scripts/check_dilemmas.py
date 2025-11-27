#!/usr/bin/env python3
"""Check dilemmas in database for quality and metadata issues."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def main():
    """Check dilemmas."""
    db = get_database()

    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        dilemmas_db = result.scalars().all()

        print(f"Total dilemmas: {len(dilemmas_db)}\n")
        print("=" * 100)

        for i, db_dilemma in enumerate(dilemmas_db, 1):
            dilemma = db_dilemma.to_domain()

            print(f"\n[{i}] {dilemma.title}")
            print(f"    ID: {dilemma.id}")
            print(f"    Difficulty: {dilemma.difficulty_intended}/10")
            print(f"    Created by: {dilemma.created_by}")
            print(f"    LLM generated: {dilemma.is_llm_generated}")
            print(f"    Generator model: {dilemma.generator_model}")
            print(f"    Prompt version: {dilemma.generator_prompt_version}")
            print(f"    Tags: {', '.join(dilemma.tags[:5]) if dilemma.tags else 'None'}")

            # Show seed components
            if dilemma.seed_components:
                print(f"    Domain: {dilemma.seed_components.get('domain')}")
                print(f"    Conflict: {dilemma.seed_components.get('conflict')}")

            # Show situation (truncated)
            situation = dilemma.situation_template
            if len(situation) > 150:
                situation = situation[:150] + "..."
            print(f"    Situation: {situation}")

            # Show choices
            print(f"    Choices: {len(dilemma.choices)}")
            for choice in dilemma.choices:
                print(f"      - {choice.label}")

            print()

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
