#!/usr/bin/env python3
"""Fix the indexed experiment_id column for extreme values judgements.

The JSON data already has experiment_id, but the indexed column wasn't updated.
This script extracts experiment_id from JSON and updates the indexed column.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import JudgementDB

console = Console()


async def fix_indexed_columns():
    """Fix experiment_id indexed column for all extreme values judgements."""

    console.print(f"\n[cyan]Fixing indexed experiment_id column...[/cyan]")

    db = get_database()
    updated_count = 0
    experiment_id = None

    async for session in db.get_session():
        # Find all extreme values judgements
        statement = select(JudgementDB)
        result = await session.execute(statement)
        all_judgements = result.scalars().all()

        for db_judgement in all_judgements:
            # Check if this is an extreme values judgement
            if 'extreme_values_experiment' in db_judgement.data:
                # Convert to domain model to get experiment_id from JSON
                judgement = db_judgement.to_domain()

                # Update the indexed column if it has an experiment_id in JSON
                if judgement.experiment_id and not db_judgement.experiment_id:
                    db_judgement.experiment_id = judgement.experiment_id
                    session.add(db_judgement)
                    updated_count += 1

                    # Track the experiment_id
                    if not experiment_id:
                        experiment_id = judgement.experiment_id

        await session.commit()

    await db.close()

    console.print(f"\n[green]✓ Updated {updated_count} judgements[/green]")

    if experiment_id:
        console.print(f"\n[bold]Experiment ID:[/bold] [cyan]{experiment_id}[/cyan]")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  1. Export data: [cyan]uv run python scripts/export_experiment_data.py {experiment_id} research/2025-10-24-extreme-values/data[/cyan]")
        console.print(f"  2. Analyze: [cyan]uv run python research/2025-10-24-extreme-values/analyze.py[/cyan]")
    console.print()


if __name__ == "__main__":
    asyncio.run(fix_indexed_columns())
