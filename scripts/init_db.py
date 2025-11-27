#!/usr/bin/env python3
"""Initialize the database schema.

This script creates all tables needed for the dilemmas project.
Run this once before using the database.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.db.database import init_database, get_database


async def main():
    """Initialize database and show info."""
    print("Initializing database schema...\n")

    # Initialize database (creates tables)
    await init_database()

    db = get_database()
    print(f"✓ Database initialized successfully")
    print(f"  Location: {db.engine.url}")
    print(f"\nTables created:")
    print(f"  - dilemmas")
    print(f"  - judgements")

    # Close connection
    await db.close()

    print("\n✓ Database is ready to use!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
