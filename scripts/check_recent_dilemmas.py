"""Check recently generated dilemmas for variable extraction issues."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select
from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def main():
    db = get_database()
    async for session in db.get_session():
        result = await session.execute(select(DilemmaDB))
        dilemmas = [d.to_domain() for d in result.scalars().all()]

        print(f'Total dilemmas: {len(dilemmas)}\n')
        print('=' * 80)

        # Check last 7 generated
        for i, d in enumerate(dilemmas[-7:], 1):
            print(f'\n{i}. {d.title}')
            print(f'   Difficulty: {d.difficulty_intended}/10')
            print(f'   Generator: {d.created_by}')

            # Check variables
            if d.variables:
                print(f'   ✓ Variables: {len(d.variables)} extracted')
                for placeholder, values in d.variables.items():
                    print(f'     - {placeholder}: {len(values)} values')
                    if not values:
                        print(f'       ⚠️  EMPTY VALUES!')
            else:
                print(f'   ✗ Variables: None')

            # Check for placeholders in situation
            has_placeholders = '{' in d.situation_template
            print(f'   Situation has {{placeholders}}: {has_placeholders}')

            if has_placeholders and not d.variables:
                print(f'   ⚠️  WARNING: Has placeholders but no variables!')

            # Show first 200 chars of situation
            print(f'   Situation preview: {d.situation_template[:200]}...')

        print('\n' + '=' * 80)


if __name__ == '__main__':
    asyncio.run(main())
