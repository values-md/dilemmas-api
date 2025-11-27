#!/usr/bin/env python3
"""Add experiment_id to existing extreme values judgements.

Since we forgot to set experiment_id when we ran the experiment,
this script retroactively adds it to all extreme_values_experiment judgements.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import JudgementDB

console = Console()


async def fix_experiment_ids():
    """Add experiment_id to all extreme values judgements."""

    # Generate a single experiment_id for all of them
    experiment_id = str(uuid.uuid4())

    console.print(f"\n[cyan]Adding experiment_id to extreme values judgements...[/cyan]")
    console.print(f"[green]Experiment ID:[/green] {experiment_id}")

    db = get_database()
    updated_count = 0

    async for session in db.get_session():
        # Find all extreme values judgements
        statement = select(JudgementDB)
        result = await session.execute(statement)
        all_judgements = result.scalars().all()

        for db_judgement in all_judgements:
            # Check if this is an extreme values judgement
            if 'extreme_values_experiment' in db_judgement.data:
                # Convert to domain model
                judgement = db_judgement.to_domain()

                # Add experiment_id if not already set
                if not judgement.experiment_id:
                    judgement.experiment_id = experiment_id

                    # Update database - both JSON data AND indexed column
                    updated_db_judgement = JudgementDB.from_domain(judgement)
                    db_judgement.data = updated_db_judgement.data
                    db_judgement.experiment_id = updated_db_judgement.experiment_id  # Update indexed column!
                    session.add(db_judgement)
                    updated_count += 1

        await session.commit()

    await db.close()

    console.print(f"\n[green]✓ Updated {updated_count} judgements[/green]")
    console.print(f"\n[bold]Experiment ID:[/bold] [cyan]{experiment_id}[/cyan]")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Export data: [cyan]uv run python scripts/export_experiment_data.py {experiment_id} research/2025-10-24-extreme-values/data[/cyan]")
    console.print(f"  2. Analyze: [cyan]uv run python research/2025-10-24-extreme-values/analyze.py[/cyan]")
    console.print()


if __name__ == "__main__":
    asyncio.run(fix_experiment_ids())
