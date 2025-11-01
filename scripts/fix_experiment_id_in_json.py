#!/usr/bin/env python3
"""Fix experiment_id mismatch between indexed column and JSON blob.

Some judgements have the correct experiment_id in the indexed column but still
have the old (duplicate) experiment_id in the JSON data blob. This causes issues
during sync when to_domain() reads from JSON.

Usage:
    # Preview what will be fixed
    uv run python scripts/fix_experiment_id_in_json.py

    # Actually fix
    uv run python scripts/fix_experiment_id_in_json.py --fix
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import JudgementDB

console = Console()

# Local database
LOCAL_DB_PATH = Path(__file__).parent.parent / "data" / "dilemmas.db"
LOCAL_DB_URL = f"sqlite+aiosqlite:///{LOCAL_DB_PATH}"


async def fix_experiment_ids():
    """Fix experiment_id in JSON blob to match indexed column."""

    console.print("\n[bold cyan]🔧 Fix Experiment ID Mismatch in JSON Blob[/bold cyan]")
    console.print("=" * 70)

    engine = create_async_engine(LOCAL_DB_URL, echo=False)

    try:
        async with AsyncSession(engine) as session:
            # Get all judgements
            result = await session.execute(select(JudgementDB))
            all_judgements = result.scalars().all()

            console.print(f"\n[cyan]Checking {len(all_judgements)} judgements...[/cyan]")

            # Find mismatches
            mismatches = []
            for j in all_judgements:
                # Convert to domain to check what's in JSON
                domain_judgement = j.to_domain()

                # Compare indexed column vs JSON
                if j.experiment_id != domain_judgement.experiment_id:
                    mismatches.append({
                        'id': j.id,
                        'indexed_exp_id': j.experiment_id,
                        'json_exp_id': domain_judgement.experiment_id,
                        'judgement_db': j,
                        'judgement_domain': domain_judgement,
                    })

            console.print(f"\n[yellow]Found {len(mismatches)} judgements with mismatch[/yellow]")

            if not mismatches:
                console.print("[green]✓ No mismatches found - all clean![/green]")
                return 0

            # Show preview
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Judgement ID", style="cyan", max_width=20)
            table.add_column("Indexed Exp ID", style="green", max_width=20)
            table.add_column("JSON Exp ID", style="red", max_width=20)

            for m in mismatches[:10]:
                table.add_row(
                    m['id'][:17] + "...",
                    (m['indexed_exp_id'] or "")[:17] + "..." if m['indexed_exp_id'] else "(null)",
                    (m['json_exp_id'] or "")[:17] + "..." if m['json_exp_id'] else "(null)",
                )

            console.print(table)
            if len(mismatches) > 10:
                console.print(f"[dim]... and {len(mismatches) - 10} more[/dim]")

            # Group by experiment IDs
            from collections import Counter
            indexed_counts = Counter(m['indexed_exp_id'] for m in mismatches)
            json_counts = Counter(m['json_exp_id'] for m in mismatches)

            console.print("\n[bold]Indexed column experiment IDs:[/bold]")
            for exp_id, count in indexed_counts.most_common():
                console.print(f"  • {exp_id or '(null)'}: {count}")

            console.print("\n[bold]JSON blob experiment IDs:[/bold]")
            for exp_id, count in json_counts.most_common():
                console.print(f"  • {exp_id or '(null)'}: {count}")

            # Check if --fix flag
            if "--fix" not in sys.argv:
                console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
                console.print("Run with --fix to actually update the JSON blobs:")
                console.print("[dim]uv run python scripts/fix_experiment_id_in_json.py --fix[/dim]")
                return 0

            # Fix them
            console.print(f"\n[bold]Fixing {len(mismatches)} judgements...[/bold]")

            for i, m in enumerate(mismatches, 1):
                # Update the domain object with correct experiment_id
                domain_judgement = m['judgement_domain']
                domain_judgement.experiment_id = m['indexed_exp_id']

                # Convert back to DB model (this updates the JSON blob)
                fixed_db = JudgementDB.from_domain(domain_judgement)

                # Update the existing record
                m['judgement_db'].data = fixed_db.data
                session.add(m['judgement_db'])

                if i % 100 == 0:
                    console.print(f"  Fixed {i}/{len(mismatches)}...")

            await session.commit()
            console.print(f"[green]✓ Fixed {len(mismatches)} judgements[/green]")

            # Verify
            console.print("\n[bold]Verifying fix...[/bold]")
            result = await session.execute(select(JudgementDB))
            all_judgements = result.scalars().all()

            still_broken = []
            for j in all_judgements:
                domain_judgement = j.to_domain()
                if j.experiment_id != domain_judgement.experiment_id:
                    still_broken.append(j)

            if still_broken:
                console.print(f"[red]✗ Still have {len(still_broken)} mismatches![/red]")
                return 1

            console.print(f"[green]✓ All {len(all_judgements)} judgements verified - no mismatches[/green]")

    finally:
        await engine.dispose()

    console.print("\n[bold green]✅ Fix Complete![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Reset production: [cyan]uv run python scripts/reset_prod_completely.py --confirm[/cyan]")
    console.print("2. Re-sync: [cyan]uv run python scripts/sync_all_to_prod.py[/cyan]")
    console.print()

    return 0


async def main():
    """Main entry point."""
    try:
        return await fix_experiment_ids()
    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
