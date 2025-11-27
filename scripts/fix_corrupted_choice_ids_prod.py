#!/usr/bin/env python3
"""Fix corrupted choice_id values in BOTH the column AND the data blob - PRODUCTION VERSION.

This script connects to the production database and fixes corrupted choice_ids.

Usage:
    # Preview what would be fixed
    uv run python scripts/fix_corrupted_choice_ids_prod.py

    # Apply the fix
    uv run python scripts/fix_corrupted_choice_ids_prod.py --apply
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from dilemmas.models.db import JudgementDB

load_dotenv()

console = Console()


def extract_choice_id(corrupted: str) -> str:
    """Extract actual choice_id from corrupted string.

    Corrupted format examples:
    - "update_immediately</parameter\\n<parameter..."
    - "endorse_unique_expression</parameter -->"

    We want just the part before </parameter or similar markers.
    """
    # Split on common markers and take first part
    markers = [
        "</parameter",  # XML closing tag
        "<parameter",   # XML opening tag
        " >",           # XML tag end
        "\n",           # Newline
        " -->",         # XML comment end
    ]

    result = corrupted
    for marker in markers:
        result = result.split(marker)[0]

    # Clean up any remaining whitespace
    result = result.strip()

    return result


async def main():
    parser = argparse.ArgumentParser(description="Fix corrupted choice_id values in PRODUCTION database")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply the fix (default is dry-run)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=100,
        help="Minimum choice_id length to consider corrupted (default: 100)",
    )

    args = parser.parse_args()

    # Print header
    console.print()
    console.print(Panel.fit(
        "[bold red]🔧 Fix Corrupted choice_id Values - PRODUCTION DATABASE[/bold red]",
        border_style="red",
    ))
    console.print()

    # Get production database URL
    prod_url = os.getenv('PROD_DATABASE_URL')
    if not prod_url:
        console.print("[red]ERROR: PROD_DATABASE_URL not set in environment[/red]")
        console.print("[dim]Set it in .env file or export it:[/dim]")
        console.print("[dim]  export PROD_DATABASE_URL='postgresql://...'[/dim]")
        return 1

    # Clean URL for asyncpg
    prod_url = prod_url.replace('postgresql://', 'postgresql+asyncpg://')
    prod_url = prod_url.replace('sslmode=require', 'ssl=require')
    prod_url = prod_url.replace('&channel_binding=require', '')

    # Mask password in display
    display_url = prod_url.split('@')[1] if '@' in prod_url else prod_url
    console.print(f"[dim]Database: ...@{display_url}[/dim]")
    console.print(f"[dim]Min length: {args.min_length} chars[/dim]\n")

    engine = create_async_engine(prod_url)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_maker() as session:
            # Find corrupted records by checking the data blob
            console.print("[cyan]Finding corrupted records in data blob...[/cyan]")
            stmt = select(JudgementDB)
            result = await session.execute(stmt)
            all_judgements = result.scalars().all()

            # Check the data blob for corrupted choice_id
            corrupted = []
            for j in all_judgements:
                if j.data:
                    data = json.loads(j.data)
                    choice_id = data.get('choice_id')
                    if choice_id and len(choice_id) > args.min_length:
                        corrupted.append(j)

            console.print(f"[yellow]Found {len(corrupted)} corrupted records in data blob[/yellow]\n")

            if not corrupted:
                console.print("[green]✓ No corrupted records found in production![/green]")
                return 0

            # Show summary table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", max_width=20)
            table.add_column("Judge", style="yellow", max_width=20)
            table.add_column("Original Length", style="red", justify="right")
            table.add_column("Extracted choice_id", style="green", max_width=30)
            table.add_column("New Length", style="green", justify="right")

            for j in corrupted[:10]:  # Show first 10
                data = json.loads(j.data)
                corrupted_choice = data.get('choice_id', '')
                extracted = extract_choice_id(corrupted_choice)
                table.add_row(
                    j.id[:17] + "...",
                    j.judge_id,
                    str(len(corrupted_choice)),
                    extracted,
                    str(len(extracted)),
                )

            console.print(table)
            if len(corrupted) > 10:
                console.print(f"[dim]... and {len(corrupted) - 10} more[/dim]\n")

            # Show statistics
            console.print("\n[bold]Statistics:[/bold]")
            original_lens = []
            extracted_lens = []
            for j in corrupted:
                data = json.loads(j.data)
                corrupted_choice = data.get('choice_id', '')
                extracted = extract_choice_id(corrupted_choice)
                original_lens.append(len(corrupted_choice))
                extracted_lens.append(len(extracted))

            console.print(f"  Original length: {min(original_lens)}-{max(original_lens)} chars")
            console.print(f"  Extracted length: {min(extracted_lens)}-{max(extracted_lens)} chars")
            console.print(f"  Average reduction: {sum(original_lens) // len(corrupted)} → {sum(extracted_lens) // len(corrupted)} chars\n")

            # Dry run?
            if not args.apply:
                console.print("[yellow]DRY RUN - No changes will be made to PRODUCTION[/yellow]")
                console.print("[bold red]Run with --apply to fix these records in PRODUCTION[/bold red]")
                console.print("\n[dim]This will fix BOTH:[/dim]")
                console.print("[dim]  1. The indexed choice_id column[/dim]")
                console.print("[dim]  2. The choice_id inside the data JSON blob[/dim]")
                return 0

            # Confirm before applying to production
            console.print("[bold red]⚠️  WARNING: You are about to modify PRODUCTION database[/bold red]")
            console.print(f"[red]This will update {len(corrupted)} records[/red]\n")

            # Apply fixes
            console.print("[cyan]Applying fixes to both column and data blob...[/cyan]")
            fixed_count = 0
            for j in corrupted:
                # Parse the data blob
                data = json.loads(j.data)
                corrupted_choice = data.get('choice_id', '')
                extracted = extract_choice_id(corrupted_choice)

                # Fix 1: Update the indexed column
                j.choice_id = extracted

                # Fix 2: Update the data blob
                data['choice_id'] = extracted
                j.data = json.dumps(data)

                session.add(j)
                fixed_count += 1

            await session.commit()
            console.print(f"[green]✓ Fixed {fixed_count} records in PRODUCTION (both column and data blob)![/green]")

    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
