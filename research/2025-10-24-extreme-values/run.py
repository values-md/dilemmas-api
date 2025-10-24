#!/usr/bin/env python3
"""Run extreme VALUES.md compliance experiment.

Tests how far different LLMs will follow extreme ethical frameworks.

Experiment Design:
- 10 dilemmas (2 per institution type)
- 6 frameworks (1 baseline + 5 extreme, context-matched)
- 3 models (Claude Sonnet 4.5, GPT-4.1, Gemini 2.5 Pro)
- = 180 judgements total

Usage:
    uv run python research/2025-10-24-extreme-values/run.py
    uv run python research/2025-10-24-extreme-values/run.py --dry-run  # Test with 1 judgement
"""

import asyncio
import random
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import argparse
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.services.judge import DilemmaJudge

console = Console()

# Experiment configuration
MODELS = [
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-4.1",
    "google/gemini-2.5-pro",
]

# VALUES.md frameworks mapped to institution types
FRAMEWORKS = {
    "corporate": [
        ("baseline", None, None),  # No VALUES.md
        ("shareholder_primacy", "corporate_shareholder_primacy.md", "moderate"),
        ("profit_absolutism", "corporate_profit_absolutism.md", "extreme"),
    ],
    "public": [
        ("baseline", None, None),
        ("collectivist_absolutism", "public_collectivist_absolutism.md", "extreme"),
    ],
    "personal": [
        ("baseline", None, None),
        ("owner_absolutism", "personal_owner_absolutism.md", "extreme"),
    ],
    "nonprofit": [
        ("baseline", None, None),
        ("mission_absolutism", "nonprofit_mission_absolutism.md", "extreme"),
    ],
    "research": [
        ("baseline", None, None),
        ("scientific_absolutism", "research_scientific_absolutism.md", "extreme"),
    ],
}


async def load_dilemmas_by_type(num_per_type: int = 2) -> dict[str, list]:
    """Load dilemmas grouped by institution type.

    Args:
        num_per_type: Number of dilemmas to select per institution type

    Returns:
        Dict mapping institution_type -> list of Dilemma objects
    """
    db = get_database()
    dilemmas_by_type = {
        "corporate": [],
        "public": [],
        "personal": [],
        "nonprofit": [],
        "research": [],
    }

    async for session in db.get_session():
        # Load all dilemmas
        statement = select(DilemmaDB)
        result = await session.execute(statement)
        db_dilemmas = result.scalars().all()

        # Convert to domain models and group by institution type
        for db_dilemma in db_dilemmas:
            dilemma = db_dilemma.to_domain()
            inst_type = dilemma.institution_type
            if inst_type in dilemmas_by_type:
                dilemmas_by_type[inst_type].append(dilemma)

    await db.close()

    # Randomly sample from each type
    for inst_type, dilemmas in dilemmas_by_type.items():
        if len(dilemmas) >= num_per_type:
            dilemmas_by_type[inst_type] = random.sample(dilemmas, num_per_type)
        elif len(dilemmas) > 0:
            console.print(f"[yellow]Warning: Only {len(dilemmas)} {inst_type} dilemmas found (needed {num_per_type})[/yellow]")
        else:
            console.print(f"[yellow]Warning: No {inst_type} dilemmas found (needed {num_per_type})[/yellow]")

    return dilemmas_by_type


def load_values_framework(filename: str | None) -> str | None:
    """Load a VALUES.md framework from file.

    Args:
        filename: Name of VALUES.md file (e.g., "corporate_shareholder_primacy.md")

    Returns:
        Contents of VALUES.md file, or None if filename is None
    """
    if filename is None:
        return None

    values_path = Path(__file__).parent / "values" / filename
    return values_path.read_text()


async def run_experiment(dry_run: bool = False):
    """Run the full experiment.

    Args:
        dry_run: If True, only run 1 judgement for testing
    """
    console.print("\n[bold cyan]🔥 Extreme VALUES.md Compliance Experiment[/bold cyan]")
    console.print("=" * 80)

    # Generate experiment ID
    experiment_id = str(uuid.uuid4())
    console.print(f"\n[green]Experiment ID:[/green] {experiment_id}")

    # Load dilemmas
    console.print("\n[cyan]Loading dilemmas...[/cyan]")
    dilemmas_by_type = await load_dilemmas_by_type(num_per_type=2)

    total_dilemmas = sum(len(d) for d in dilemmas_by_type.values())
    console.print(f"✓ Loaded {total_dilemmas} dilemmas:")
    for inst_type, dilemmas in dilemmas_by_type.items():
        console.print(f"  {inst_type:12s}: {len(dilemmas)}")

    # Build experiment plan
    console.print("\n[cyan]Building experiment plan...[/cyan]")
    experiment_plan = []

    for inst_type, dilemmas in dilemmas_by_type.items():
        frameworks = FRAMEWORKS.get(inst_type, [])

        for dilemma in dilemmas:
            for framework_name, values_file, extremity in frameworks:
                for model in MODELS:
                    experiment_plan.append({
                        "dilemma": dilemma,
                        "model": model,
                        "framework_name": framework_name,
                        "values_file": values_file,
                        "extremity": extremity,
                        "institution_type": inst_type,
                    })

    if dry_run:
        experiment_plan = experiment_plan[:1]  # Only first judgement
        console.print(f"\n[yellow]DRY RUN: Running only 1 judgement for testing[/yellow]")

    console.print(f"✓ Plan: {len(experiment_plan)} judgements")
    console.print(f"  Dilemmas: {total_dilemmas}")
    console.print(f"  Frameworks: {len(set(p['framework_name'] for p in experiment_plan))}")
    console.print(f"  Models: {len(MODELS)}")

    # Confirm
    if not dry_run:
        console.print("\n[yellow]Ready to run experiment. This will take ~30-45 minutes.[/yellow]")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            console.print("[yellow]Cancelled.[/yellow]")
            return 1

    # Run experiment
    console.print("\n[cyan]Running experiment...[/cyan]")
    judge = DilemmaJudge()
    db = get_database()
    judgements = []
    failed = []

    start_time = datetime.now()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Collecting judgements", total=len(experiment_plan))

        for i, plan in enumerate(experiment_plan):
            dilemma = plan["dilemma"]
            model = plan["model"]
            framework_name = plan["framework_name"]
            values_file = plan["values_file"]
            extremity = plan["extremity"]

            # Update progress
            progress.update(
                task,
                description=f"[cyan]{i+1}/{len(experiment_plan)}: {model.split('/')[-1]} on {dilemma.title[:30]}... ({framework_name})",
            )

            try:
                # Load VALUES.md content
                values_content = load_values_framework(values_file)

                # Run judgement
                judgement = await judge.judge_dilemma(
                    dilemma=dilemma,
                    model_id=model,
                    temperature=1.0,
                    mode="theory",
                    system_prompt=values_content,
                    system_prompt_type="custom_values" if values_content else "none",
                    values_file_name=values_file,
                )

                # Add experiment metadata
                judgement.experiment_id = experiment_id
                judgement.notes = f"extreme_values_experiment|framework={framework_name}|extremity={extremity or 'baseline'}|institution={plan['institution_type']}"

                judgements.append(judgement)

                # Save to database immediately
                async for session in db.get_session():
                    db_judgement = JudgementDB.from_domain(judgement)
                    session.add(db_judgement)
                    await session.commit()

                console.print(
                    f"  [green]✓[/green] {framework_name:20s} → choice={judgement.choice_id}, "
                    f"confidence={judgement.confidence:.1f}, difficulty={judgement.perceived_difficulty:.1f}"
                )

            except Exception as e:
                error_msg = str(e)[:100]
                console.print(f"  [red]✗[/red] Failed: {error_msg}")
                failed.append({
                    "dilemma_id": dilemma.id,
                    "model": model,
                    "framework": framework_name,
                    "error": error_msg,
                })

            progress.update(task, advance=1)

    await db.close()

    elapsed = (datetime.now() - start_time).total_seconds()

    # Summary
    console.print("\n" + "=" * 80)
    console.print("[bold green]✓ Experiment Complete![/bold green]")
    console.print("=" * 80)

    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Total: {len(experiment_plan)}")
    console.print(f"  Succeeded: [green]{len(judgements)}[/green]")
    if failed:
        console.print(f"  Failed: [red]{len(failed)}[/red]")
    console.print(f"  Time: {elapsed/60:.1f} minutes")

    if failed:
        console.print(f"\n[yellow]Failed judgements:[/yellow]")
        for f in failed[:10]:
            console.print(f"  {f['model'].split('/')[-1]} on {f['dilemma_id'][:8]}... ({f['framework']}): {f['error']}")

    console.print(f"\n[bold]Experiment ID:[/bold] [cyan]{experiment_id}[/cyan]")

    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Export data: [cyan]uv run python scripts/export_experiment_data.py {experiment_id} research/2025-10-24-extreme-values/data[/cyan]")
    console.print(f"  2. Analyze: [cyan]uv run python research/2025-10-24-extreme-values/analyze.py[/cyan]")
    console.print(f"  3. View in browser: [cyan]http://localhost:8000/judgements[/cyan]")

    console.print("\n" + "=" * 80 + "\n")

    return 0


async def main():
    parser = argparse.ArgumentParser(description="Run extreme VALUES.md experiment")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test with only 1 judgement",
    )
    args = parser.parse_args()

    return await run_experiment(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
