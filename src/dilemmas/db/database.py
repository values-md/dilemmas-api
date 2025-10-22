"""Database connection and session management.

Supports both SQLite (development/testing) and Postgres (production).
Uses async SQLAlchemy for compatibility with pydantic-ai agents.
"""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from dilemmas.models.db import DilemmaDB, JudgementDB  # noqa: F401 - needed for table creation


class Database:
    """Database connection manager.

    Handles engine creation, session management, and schema initialization.
    """

    def __init__(self, database_url: str | None = None):
        """Initialize database connection.

        Args:
            database_url: Database URL. If None, uses SQLite in data/ directory.
                Examples:
                - SQLite: "sqlite+aiosqlite:///./data/dilemmas.db"
                - Postgres: "postgresql+asyncpg://user:pass@host/db"
        """
        if database_url is None:
            # Default to SQLite in data directory
            db_path = Path(__file__).parent.parent.parent.parent / "data" / "dilemmas.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite+aiosqlite:///{db_path}"

        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            future=True,
        )

        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init_db(self):
        """Initialize database schema (create all tables)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def drop_db(self):
        """Drop all tables (use with caution!)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session.

        Usage:
            async with db.get_session() as session:
                # Use session
                pass

        Or with dependency injection (FastAPI):
            async for session in db.get_session():
                yield session
        """
        async with self.async_session() as session:
            yield session

    async def close(self):
        """Close database connection."""
        await self.engine.dispose()


# Global database instance
_db: Database | None = None


def get_database(database_url: str | None = None) -> Database:
    """Get or create the global database instance.

    Args:
        database_url: Optional database URL. Only used on first call.

    Returns:
        Database instance
    """
    global _db
    if _db is None:
        _db = Database(database_url)
    return _db


async def init_database(database_url: str | None = None):
    """Initialize the database schema.

    Args:
        database_url: Optional database URL
    """
    db = get_database(database_url)
    await db.init_db()


# Convenience function for FastAPI dependency injection
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection.

    Usage in FastAPI:
        @app.get("/dilemmas")
        async def get_dilemmas(session: AsyncSession = Depends(get_session)):
            ...
    """
    db = get_database()
    async for session in db.get_session():
        yield session
