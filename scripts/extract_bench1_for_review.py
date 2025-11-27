#!/usr/bin/env python3
"""Extract all bench-1 dilemmas as individual JSON files for manual review."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio
import json
from sqlmodel import select
from dilemmas.db.database import Database
from dilemmas.models.db import DilemmaDB

async def extract():
    db = Database()
    output_dir = Path("data/bench1_review")
    output_dir.mkdir(exist_ok=True)

    async for session in db.get_session():
        result = await session.execute(
            select(DilemmaDB)
            .where(DilemmaDB.collection == "bench-1")
            .order_by(DilemmaDB.id)
        )
        dilemmas_db = result.scalars().all()

        print(f"Found {len(dilemmas_db)} dilemmas in bench-1 collection")

        for db_dilemma in dilemmas_db:
            dilemma = db_dilemma.to_domain()

            # Save as JSON
            output_file = output_dir / f"{dilemma.id}.json"
            with open(output_file, "w") as f:
                json.dump(dilemma.model_dump(), f, indent=2, default=str)

            print(f"Saved: {output_file}")

    await db.close()
    print(f"\nAll dilemmas saved to {output_dir}/")

if __name__ == "__main__":
    asyncio.run(extract())
