#!/usr/bin/env python3
"""Drop choice_id index from production to allow migration of fixed data."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

console = Console()

async def main():
    prod_url = os.getenv("PROD_DATABASE_URL")

    if not prod_url:
        console.print("[red]ERROR: PROD_DATABASE_URL not set[/red]")
        return 1

    # Clean URL for asyncpg
    if "postgresql://" in prod_url:
        prod_url = prod_url.replace("postgresql://", "postgresql+asyncpg://")
    if "sslmode=" in prod_url:
        prod_url = prod_url.replace("?sslmode=require", "?ssl=require")
        prod_url = prod_url.replace("&sslmode=require", "&ssl=require")

    # Remove channel_binding parameter (asyncpg doesn't support it)
    if "channel_binding=" in prod_url:
        import re
        prod_url = re.sub(r'[&?]channel_binding=[^&]*', '', prod_url)
        prod_url = prod_url.replace('&&', '&').rstrip('?&')

    console.print("[cyan]Dropping choice_id index from production...[/cyan]")
    console.print(f"[dim]Database: {prod_url.split('@')[1].split('/')[0]}[/dim]\n")

    engine = create_async_engine(prod_url)

    try:
        async with engine.begin() as conn:
            # Drop index if exists
            await conn.execute(text(
                "DROP INDEX IF EXISTS ix_judgements_choice_id"
            ))

        console.print("[green]✓ Index dropped successfully[/green]")
        return 0

    finally:
        await engine.dispose()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
