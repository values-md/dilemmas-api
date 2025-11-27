#!/usr/bin/env python3
"""Analyze variables and modifiers in our dilemma dataset."""

import sys
from pathlib import Path
from collections import Counter, defaultdict
import re

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from sqlalchemy import select

async def analyze():
    db = get_database()

    variable_names = []
    modifier_texts = []

    # Categorize variables by type
    name_vars = []  # Variables containing names (potential demographic bias)
    amount_vars = []  # Numeric amounts (potential wealth bias)
    descriptor_vars = []  # Descriptive attributes

    async for session in db.get_session():
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        dilemmas = result.scalars().all()

        for db_dilemma in dilemmas:
            dilemma = db_dilemma.to_domain()

            if dilemma.variables:
                for var_name, values in dilemma.variables.items():
                    variable_names.append(var_name)

                    # Categorize by type
                    if 'NAME' in var_name:
                        name_vars.append((var_name, values))
                    elif 'AMOUNT' in var_name or 'NUM' in var_name or any(v.replace('.','').replace(',','').isdigit() for v in values):
                        amount_vars.append((var_name, values))
                    else:
                        descriptor_vars.append((var_name, values))

            if dilemma.modifiers:
                modifier_texts.extend(dilemma.modifiers)

    # Print analysis
    print("\n=== VARIABLE ANALYSIS ===\n")
    print(f"Total dilemmas with variables: {len(dilemmas)}")
    print(f"Total variable instances: {len(variable_names)}\n")

    print("Most common variable types:")
    counter = Counter(variable_names)
    for name, count in counter.most_common(15):
        print(f"  {name}: {count}")

    print("\n\n=== NAME VARIABLES (Demographic Bias Potential) ===\n")
    print(f"Count: {len(name_vars)}\n")
    for var_name, values in name_vars[:5]:
        print(f"{var_name}:")
        for v in values[:4]:
            print(f"  - {v}")
        print()

    print("\n=== AMOUNT VARIABLES (Wealth/Scale Bias Potential) ===\n")
    print(f"Count: {len(amount_vars)}\n")
    for var_name, values in amount_vars[:5]:
        print(f"{var_name}:")
        for v in values[:4]:
            print(f"  - {v}")
        print()

    print("\n=== DESCRIPTOR VARIABLES ===\n")
    print(f"Count: {len(descriptor_vars)}\n")
    for var_name, values in descriptor_vars[:5]:
        print(f"{var_name}:")
        for v in values[:4]:
            print(f"  - {v}")
        print()

    print("\n=== MODIFIER ANALYSIS ===\n")
    print(f"Total modifier instances: {len(modifier_texts)}\n")

    # Categorize modifiers
    time_pressure = [m for m in modifier_texts if 'second' in m.lower() or 'minute' in m.lower() or 'hour' in m.lower()]
    stakes = [m for m in modifier_texts if 'million' in m.lower() or 'lives' in m.lower() or 'depend' in m.lower()]
    uncertainty = [m for m in modifier_texts if 'uncertain' in m.lower() or '%' in m or 'incomplete' in m.lower()]
    irreversibility = [m for m in modifier_texts if 'cannot' in m.lower() or 'reverse' in m.lower() or 'undo' in m.lower()]
    visibility = [m for m in modifier_texts if 'public' in m.lower() or 'visible' in m.lower()]

    print("Modifier categories:")
    print(f"  Time pressure: {len(time_pressure)} ({len(time_pressure)/len(modifier_texts)*100:.1f}%)")
    print(f"  High stakes: {len(stakes)} ({len(stakes)/len(modifier_texts)*100:.1f}%)")
    print(f"  Uncertainty: {len(uncertainty)} ({len(uncertainty)/len(modifier_texts)*100:.1f}%)")
    print(f"  Irreversibility: {len(irreversibility)} ({len(irreversibility)/len(modifier_texts)*100:.1f}%)")
    print(f"  Visibility: {len(visibility)} ({len(visibility)/len(modifier_texts)*100:.1f}%)")

    print("\n\nSample modifiers:")
    for mod in set(modifier_texts[:10]):
        print(f"  - {mod}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(analyze())
