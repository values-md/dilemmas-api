#!/usr/bin/env python3
"""Test database CRUD operations.

This script tests that we can:
- Save dilemmas to the database
- Query them back
- Convert between domain and DB models
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database, get_session
from dilemmas.models.db import DilemmaDB
from dilemmas.models.dilemma import Dilemma, DilemmaChoice


async def main():
    """Test database operations."""
    print("Testing database CRUD operations...\n")

    # Clean up any existing test data first
    db = get_database()
    async for session in db.get_session():
        existing = await session.get(DilemmaDB, "test_db_001")
        if existing:
            await session.delete(existing)
            await session.commit()
            print("Cleaned up existing test data\n")

    # Create a test dilemma
    test_dilemma = Dilemma(
        id="test_db_001",
        title="Test Database Dilemma",
        situation_template="This is a test dilemma with {VARIABLE}.",
        question="Does the database work?",
        choices=[
            DilemmaChoice(id="yes", label="Yes", description="It works!"),
            DilemmaChoice(id="no", label="No", description="It failed"),
        ],
        variables={"{VARIABLE}": ["SQLite", "Postgres"]},
        tags=["test", "database"],
        action_context="You are a test AI.",
        difficulty_intended=1,
        created_by="test_script",
        source="test",
    )

    print(f"Created test dilemma: {test_dilemma.title}")
    print(f"  ID: {test_dilemma.id}")
    print(f"  Tags: {test_dilemma.tags}")
    print(f"  Variables: {list(test_dilemma.variables.keys())}")

    # Get database session
    db = get_database()

    # Test 1: Save to database
    print("\n[1] Testing save...")
    async for session in db.get_session():
        # Convert to DB model and save
        db_dilemma = DilemmaDB.from_domain(test_dilemma)
        session.add(db_dilemma)
        await session.commit()
        print(f"✓ Saved dilemma to database")

    # Test 2: Query by ID
    print("\n[2] Testing query by ID...")
    async for session in db.get_session():
        result = await session.get(DilemmaDB, "test_db_001")
        if result:
            print(f"✓ Found dilemma: {result.title}")
            # Convert back to domain model
            retrieved = result.to_domain()
            print(f"  Domain model title: {retrieved.title}")
            print(f"  Domain model tags: {retrieved.tags}")
            assert retrieved.id == test_dilemma.id
            assert retrieved.title == test_dilemma.title
            assert retrieved.tags == test_dilemma.tags
            print(f"✓ Domain model conversion works!")
        else:
            print("✗ Dilemma not found")
            return 1

    # Test 3: Query by filter
    print("\n[3] Testing query with filters...")
    async for session in db.get_session():
        statement = select(DilemmaDB).where(DilemmaDB.difficulty_intended == 1)
        result = await session.execute(statement)
        dilemmas = result.scalars().all()
        print(f"✓ Found {len(dilemmas)} dilemma(s) with difficulty=1")

    # Test 4: Query by tag (JSON search)
    print("\n[4] Testing tag search...")
    async for session in db.get_session():
        # Note: JSON querying syntax differs between SQLite and Postgres
        # For now, we do client-side filtering (could optimize with JSON functions later)
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        all_dilemmas = result.scalars().all()
        test_tagged = [d for d in all_dilemmas if "test" in d.tags]
        print(f"✓ Found {len(test_tagged)} dilemma(s) tagged 'test'")

    # Test 5: Update
    print("\n[5] Testing update...")
    async for session in db.get_session():
        result = await session.get(DilemmaDB, "test_db_001")
        if result:
            # Modify domain model
            domain = result.to_domain()
            domain.tags.append("updated")

            # Convert back and update
            updated_db = DilemmaDB.from_domain(domain)
            # Update the existing record
            result.data = updated_db.data
            result.tags_json = updated_db.tags_json

            await session.commit()
            print(f"✓ Updated dilemma tags: {result.tags}")

    # Test 6: Delete
    print("\n[6] Testing delete...")
    async for session in db.get_session():
        result = await session.get(DilemmaDB, "test_db_001")
        if result:
            await session.delete(result)
            await session.commit()
            print(f"✓ Deleted dilemma")

    # Verify deletion
    print("\n[7] Verifying deletion...")
    async for session in db.get_session():
        result = await session.get(DilemmaDB, "test_db_001")
        if result is None:
            print(f"✓ Dilemma successfully deleted")
        else:
            print("✗ Dilemma still exists")
            return 1

    await db.close()

    print("\n✓ All database tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
