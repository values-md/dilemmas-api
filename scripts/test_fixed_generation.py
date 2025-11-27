#!/usr/bin/env python3
"""Test generation with fixed schema and validation."""

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator


async def main():
    """Test generation."""
    print("=" * 80)
    print("Testing Dilemma Generation with Fixed Schema")
    print("=" * 80)
    print()

    # Generate with Gemini (should be concrete, no placeholders)
    print("Step 1: Generating concrete dilemma with Gemini 2.5 Flash...")
    print("-" * 80)

    gen = DilemmaGenerator(model_id="google/gemini-2.5-flash")
    dilemma = await gen.generate_random(difficulty=5, add_variables=False)

    print(f"✓ Generated: {dilemma.title}")
    print(f"\nSituation (first 250 chars):")
    print(dilemma.situation_template[:250] + "...")
    print(f"\nHas placeholders: {'{' in dilemma.situation_template}")
    print(f"Variables populated: {len(dilemma.variables) > 0}")

    # Now extract variables with Kimi K2
    print()
    print("Step 2: Extracting variables with Kimi K2...")
    print("-" * 80)

    dilemma = await gen.variablize_dilemma(dilemma)

    # Check for placeholders
    placeholders = set(re.findall(r"\{([A-Z_]+)\}", dilemma.situation_template))
    has_values = set(key.strip("{}") for key in dilemma.variables.keys())
    missing = placeholders - has_values

    print(f"✓ Extraction complete")
    print(f"\nPlaceholders in template: {len(placeholders)}")
    print(f"Variables with values: {len(has_values)}")
    print(f"Missing values: {len(missing)}")

    if missing:
        print(f"  ⚠️  Missing: {sorted(missing)}")
    else:
        print("  ✓ All placeholders have values!")

    print(f"\nModifiers extracted: {len(dilemma.modifiers)}")
    if dilemma.modifiers:
        for i, mod in enumerate(dilemma.modifiers[:3], 1):
            print(f"  {i}. {mod}")

    # Test rendering
    print()
    print("Step 3: Testing rendering...")
    print("-" * 80)

    rendered = dilemma.render()
    still_has_placeholders = bool(re.findall(r"\{[A-Z_]+\}", rendered))

    print(f"Rendered (first 250 chars):")
    print(rendered[:250] + "...")
    print(f"\nStill has placeholders: {still_has_placeholders}")

    if not still_has_placeholders:
        print("  ✓ All placeholders successfully rendered!")
    else:
        remaining = re.findall(r"\{([A-Z_]+)\}", rendered)
        print(f"  ⚠️  Remaining: {remaining}")

    # Save to database
    print()
    print("Step 4: Saving to database...")
    print("-" * 80)

    db = get_database()
    async for session in db.get_session():
        db_dilemma = DilemmaDB.from_domain(dilemma)
        session.add(db_dilemma)
        await session.commit()
        break

    await db.close()

    print(f"✓ Saved to database")
    print(f"  View at: http://localhost:8000/dilemma/{dilemma.id}")

    print()
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
