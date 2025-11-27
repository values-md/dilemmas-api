#!/usr/bin/env python3
"""Export dilemmas from a collection to JSON.

Usage:
    uv run python scripts/export_dilemmas.py --collection <collection_name> --output <output_file.json>
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB


async def export_dilemmas(collection: str, output_path: Path):
    """Export all dilemmas from a collection to JSON.

    Args:
        collection: Collection name to export
        output_path: Output JSON file path
    """
    db = get_database()

    async for session in db.get_session():
        # Load all dilemmas from collection
        statement = select(DilemmaDB).where(DilemmaDB.collection == collection)
        result = await session.execute(statement)
        dilemma_dbs = result.scalars().all()

        if not dilemma_dbs:
            print(f"No dilemmas found in collection: {collection}")
            return

        # Convert to domain objects and serialize
        dilemmas_data = []
        for db_dilemma in dilemma_dbs:
            dilemma = db_dilemma.to_domain()
            dilemmas_data.append(dilemma.model_dump(mode='json'))

        # Sort by created_at for consistency
        dilemmas_data.sort(key=lambda x: x.get('created_at', ''))

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(dilemmas_data, f, indent=2)

        print(f"✓ Exported {len(dilemmas_data)} dilemmas from '{collection}' to {output_path}")
        print(f"\nSample titles:")
        for i, d in enumerate(dilemmas_data[:5], 1):
            word_count = len(d['situation_template'].split())
            print(f"  {i}. {d['title']} ({word_count} words, difficulty {d['difficulty_intended']})")

    await db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Export dilemmas from a collection to JSON')
    parser.add_argument('--collection', required=True, help='Collection name to export')
    parser.add_argument('--output', required=True, help='Output JSON file path')

    args = parser.parse_args()

    output_path = Path(args.output)

    asyncio.run(export_dilemmas(args.collection, output_path))


if __name__ == '__main__':
    main()
