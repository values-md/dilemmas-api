#!/usr/bin/env python3
"""Check the Climate Monitor dilemma structure."""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from sqlalchemy import select

async def check():
    db = get_database()

    async for session in db.get_session():
        statement = select(DilemmaDB).where(DilemmaDB.data.like('%Climate Monitor%'))
        result = await session.execute(statement)
        dilemma_db = result.scalars().first()

        if dilemma_db:
            dilemma = dilemma_db.to_domain()

            print("TITLE:", dilemma.title)
            print("\nSITUATION TEMPLATE:")
            print(dilemma.situation_template[:500])
            print("\nVARIABLES:")
            if dilemma.variables:
                for k, v in dilemma.variables.items():
                    print(f"  {k}: {v}")
            else:
                print("  None")

            # Find all placeholders in situation
            import re
            placeholders = set(re.findall(r'\{([A-Z_][A-Z0-9_]*)\}', dilemma.situation_template))
            print("\nPLACEHOLDERS FOUND IN SITUATION:")
            print(f"  {placeholders}")

            # Find name variables
            if dilemma.variables:
                name_vars = [k for k in dilemma.variables.keys() if 'NAME' in k.upper()]
                other_vars = [k for k in dilemma.variables.keys() if 'NAME' not in k.upper()]
                print("\nNAME VARIABLES:")
                print(f"  {name_vars}")
                print("\nOTHER VARIABLES:")
                print(f"  {other_vars}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check())
