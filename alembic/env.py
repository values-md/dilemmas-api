"""Alembic environment configuration for async SQLModel.

This module configures Alembic to work with our SQLModel models and async database.
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy.engine import Connection

from alembic import context

# Add src to path so we can import our models
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import SQLModel and our models
from sqlmodel import SQLModel
from dilemmas.models.db import DilemmaDB, JudgementDB  # noqa: F401 - needed for metadata registration

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata from SQLModel
# This tells Alembic which models to track for autogenerate
target_metadata = SQLModel.metadata

# Configure database URL from our database module
# This ensures we use the same database as the application
from dilemmas.db.database import get_database

db = get_database()
database_url = str(db.engine.url)

# For SQLite async, we need to convert aiosqlite to sqlite for offline mode
if database_url.startswith("sqlite+aiosqlite"):
    offline_url = database_url.replace("sqlite+aiosqlite", "sqlite")
else:
    offline_url = database_url

# Override the sqlalchemy.url config
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url=offline_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    In this scenario we need to create an async Engine
    and associate a connection with the context.
    """
    # Use the engine from our database instance
    connectable = db.engine

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    For async engines, we use asyncio to run the async migration function.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
