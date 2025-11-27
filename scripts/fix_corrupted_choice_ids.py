#!/usr/bin/env python3
"""Fix corrupted choice_id values in judgements.

Some judgements (all from x-ai/grok-4) have the entire LLM response stored
in choice_id instead of just the choice identifier. This script:
1. Identifies affected records (choice_id > 500 chars)
2. Extracts the actual choice_id from the beginning of the string
3. Updates the records (or dry-run to preview)

Usage:
    # Preview what would be fixed
    uv run python scripts/fix_corrupted_choice_ids.py

    # Apply the fix
    uv run python scripts/fix_corrupted_choice_ids.py --apply
"""

import argparse
import asyncio
import re
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
    parser = argparse.ArgumentParser(description="Fix corrupted choice_id values")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply the fix (default is dry-run)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=500,
        help="Minimum choice_id length to consider corrupted (default: 500)",
    )

    args = parser.parse_args()

    # Print header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔧 Fix Corrupted choice_id Values[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    # Connect to local database
    db_path = Path(__file__).parent.parent / "data" / "dilemmas.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    console.print(f"[dim]Database: {db_url}[/dim]")
    console.print(f"[dim]Min length: {args.min_length} chars[/dim]\n")

    engine = create_async_engine(db_url)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_maker() as session:
            # Find corrupted records
            console.print("[cyan]Finding corrupted records...[/cyan]")
            stmt = select(JudgementDB).where(
                JudgementDB.choice_id.isnot(None)
            )
            result = await session.execute(stmt)
            all_judgements = result.scalars().all()

            # Filter by length in Python (SQLite doesn't have length() in WHERE)
            corrupted = [
                j for j in all_judgements
                if j.choice_id and len(j.choice_id) > args.min_length
            ]

            console.print(f"[yellow]Found {len(corrupted)} corrupted records[/yellow]\n")

            if not corrupted:
                console.print("[green]✓ No corrupted records found![/green]")
                return 0

            # Show summary table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", max_width=20)
            table.add_column("Judge", style="yellow", max_width=20)
            table.add_column("Original Length", style="red", justify="right")
            table.add_column("Extracted choice_id", style="green", max_width=30)
            table.add_column("New Length", style="green", justify="right")

            fixes = []
            for j in corrupted[:10]:  # Show first 10
                extracted = extract_choice_id(j.choice_id)
                fixes.append((j, extracted))
                table.add_row(
                    j.id[:17] + "...",
                    j.judge_id,
                    str(len(j.choice_id)),
                    extracted,
                    str(len(extracted)),
                )

            console.print(table)
            if len(corrupted) > 10:
                console.print(f"[dim]... and {len(corrupted) - 10} more[/dim]\n")

            # Show statistics
            console.print("\n[bold]Statistics:[/bold]")
            original_lens = [len(j.choice_id) for j in corrupted]
            extracted_lens = [len(extract_choice_id(j.choice_id)) for j in corrupted]
            console.print(f"  Original length: {min(original_lens)}-{max(original_lens)} chars")
            console.print(f"  Extracted length: {min(extracted_lens)}-{max(extracted_lens)} chars")
            console.print(f"  Average reduction: {sum(original_lens) // len(corrupted)} → {sum(extracted_lens) // len(corrupted)} chars\n")

            # Dry run?
            if not args.apply:
                console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
                console.print("Run with --apply to fix these records.")
                return 0

            # Apply fixes
            console.print("[cyan]Applying fixes...[/cyan]")
            for j in corrupted:
                extracted = extract_choice_id(j.choice_id)
                j.choice_id = extracted
                session.add(j)

            await session.commit()
            console.print(f"[green]✓ Fixed {len(corrupted)} records![/green]")

    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
