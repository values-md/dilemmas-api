"""Inspect production database contents before cleanup.

Safe read-only script to see what's currently in production.
"""

import asyncio
import sys
import os
from pathlib import Path
from collections import Counter
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()

# Get production database URL from env
PROD_DATABASE_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DATABASE_URL:
    console.print("[red]ERROR: PROD_DATABASE_URL not set in environment[/red]")
    console.print("[yellow]Set it in .env file[/yellow]")
    sys.exit(1)

# Clean URL for asyncpg
if "postgresql://" in PROD_DATABASE_URL:
    PROD_DATABASE_URL = PROD_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
if "sslmode=require" in PROD_DATABASE_URL:
    PROD_DATABASE_URL = PROD_DATABASE_URL.replace("sslmode=require", "ssl=require")
if "channel_binding" in PROD_DATABASE_URL:
    # Remove channel_binding parameter
    import urllib.parse
    parts = urllib.parse.urlparse(PROD_DATABASE_URL)
    query_params = urllib.parse.parse_qs(parts.query)
    query_params.pop("channel_binding", None)
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    PROD_DATABASE_URL = urllib.parse.urlunparse((
        parts.scheme, parts.netloc, parts.path,
        parts.params, new_query, parts.fragment
    ))

engine = create_async_engine(PROD_DATABASE_URL, echo=False)


async def inspect_production():
    """Inspect production database contents."""

    console.print("\n[bold cyan]Production Database Inspection[/bold cyan]")
    console.print(f"[yellow]Database:[/yellow] {PROD_DATABASE_URL.split('@')[1].split('/')[0]}\n")

    async with AsyncSession(engine) as session:
        # Count dilemmas
        result = await session.execute(select(DilemmaDB))
        dilemmas = result.scalars().all()
        console.print(f"[bold]Dilemmas:[/bold] {len(dilemmas)}")

        # Count by collection
        collections = Counter(d.collection for d in dilemmas if d.collection)
        if collections:
            console.print("[dim]Collections:[/dim]")
            for coll, count in sorted(collections.items()):
                console.print(f"  • {coll}: {count}")

        console.print()

        # Count judgements
        result = await session.execute(select(JudgementDB))
        judgements = result.scalars().all()
        console.print(f"[bold]Judgements:[/bold] {len(judgements)}")

        if not judgements:
            console.print("[green]No judgements in production - safe to proceed with sync[/green]")
            return 0

        # Analyze judgements
        console.print()

        # By experiment_id
        exp_ids = Counter(j.experiment_id for j in judgements if j.experiment_id)
        console.print("[bold]By Experiment ID:[/bold]")
        table = Table(show_header=True)
        table.add_column("Experiment ID", style="cyan")
        table.add_column("Count", justify="right", style="yellow")
        table.add_column("Date Range", style="green")

        for exp_id, count in exp_ids.most_common():
            exp_judgements = [j for j in judgements if j.experiment_id == exp_id]
            dates = [j.created_at for j in exp_judgements if j.created_at]
            if dates:
                min_date = min(dates).strftime("%Y-%m-%d")
                max_date = max(dates).strftime("%Y-%m-%d")
                date_range = f"{min_date} to {max_date}" if min_date != max_date else min_date
            else:
                date_range = "N/A"

            table.add_row(exp_id[:36], str(count), date_range)

        console.print(table)
        console.print()

        # By model
        models = Counter()
        for j in judgements:
            domain = j.to_domain()
            if domain.judge_type == "ai" and domain.ai_judge:
                models[domain.ai_judge.model_id] += 1

        if models:
            console.print("[bold]By Model:[/bold]")
            for model, count in sorted(models.items()):
                console.print(f"  • {model}: {count}")
            console.print()

        # Check for UUID collision
        collision_uuid = "b191388e-3994-4ebd-96cc-af0d033c5230"
        collision_judgements = [j for j in judgements if j.experiment_id == collision_uuid]

        if collision_judgements:
            console.print("[bold red]⚠️  UUID COLLISION DETECTED[/bold red]")
            console.print(f"Found {len(collision_judgements)} judgements with collision UUID")

            # Separate by date
            cutoff = datetime(2025, 10, 29)
            old = [j for j in collision_judgements if j.created_at < cutoff]
            new = [j for j in collision_judgements if j.created_at >= cutoff]

            console.print(f"  • Old experiment (< Oct 29): {len(old)} judgements")
            console.print(f"  • bench-1 baseline (>= Oct 29): {len(new)} judgements")
            console.print()
            console.print("[yellow]Recommendation: Reset judgements and resync from local[/yellow]")
        else:
            console.print("[green]✓ No UUID collision detected[/green]")

        console.print()

        # Summary
        console.print("[bold]Summary:[/bold]")
        console.print(f"  • Total dilemmas: {len(dilemmas)}")
        console.print(f"  • Total judgements: {len(judgements)}")
        console.print(f"  • Unique experiments: {len(exp_ids)}")
        console.print(f"  • Unique models: {len(models)}")

    return 0


async def main():
    """Main entry point."""
    try:
        return await inspect_production()
    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
