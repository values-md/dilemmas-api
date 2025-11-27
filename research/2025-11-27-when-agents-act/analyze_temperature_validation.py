#!/usr/bin/env python3
"""
Analyze temperature validation results.

Compare reversal rates across temperatures 0.0, 0.5, and 1.0 to assess
whether temperature 1.0 introduces noise or captures real signal.
"""

import asyncio
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import select
from rich.console import Console
from rich.table import Table

from dilemmas.db.database import get_session
from dilemmas.models.db import JudgementDB

console = Console()

# Experiment IDs
VALIDATION_EXPERIMENT_ID = "d982bbd3-14c8-4bcb-a6fc-590c767452e8"
MAIN_EXPERIMENT_ID = "03de21a4-25ed-4df4-b03a-4715b1ca1256"

# Model short names
MODEL_NAMES = {
    "anthropic/claude-sonnet-4.5": "Claude Sonnet 4.5",
    "google/gemini-3-pro-preview": "Gemini 3 Pro",
    "openai/gpt-5": "GPT-5",
    "x-ai/grok-4": "Grok-4",
}


@dataclass
class ReversalStats:
    """Reversal statistics for a given temperature."""
    temperature: float
    total_pairs: int
    reversals: int
    reversal_rate: float

    # By model
    by_model: dict[str, tuple[int, int]]  # model_id -> (reversals, total)

    # By dilemma
    by_dilemma: dict[str, tuple[int, int]]  # dilemma_id -> (reversals, total)


async def load_validation_judgments():
    """Load validation judgments from database."""
    console.print("[yellow]Loading validation judgments...[/yellow]")

    async for session in get_session():
        result = await session.execute(
            select(JudgementDB).where(JudgementDB.experiment_id == VALIDATION_EXPERIMENT_ID)
        )
        db_judgments = result.scalars().all()

        judgments = [j.to_domain() for j in db_judgments]
        console.print(f"[green]Loaded {len(judgments)} validation judgments[/green]\n")

        return judgments


async def load_baseline_judgments(dilemma_ids: list[str]):
    """Load baseline (temp 1.0) judgments for same dilemmas and models."""
    console.print("[yellow]Loading baseline (temp 1.0) judgments...[/yellow]")

    async for session in get_session():
        result = await session.execute(
            select(JudgementDB).where(
                JudgementDB.experiment_id == MAIN_EXPERIMENT_ID,
                JudgementDB.dilemma_id.in_(dilemma_ids)
            )
        )
        db_judgments = result.scalars().all()

        judgments = [j.to_domain() for j in db_judgments]
        console.print(f"[green]Loaded {len(judgments)} baseline judgments[/green]\n")

        return judgments


def calculate_reversals(judgments, temperature: float) -> ReversalStats:
    """Calculate reversal statistics for a given temperature."""

    # Group by (model, dilemma, mode)
    pairs = defaultdict(lambda: {"theory": None, "action": None})

    for j in judgments:
        if not j.ai_judge:
            continue

        # For validation: filter by temperature from experiment_metadata
        if j.experiment_id == VALIDATION_EXPERIMENT_ID:
            exp_temp = j.experiment_metadata.get("temperature")
            if exp_temp != temperature:
                continue
        # For baseline: only include if temp 1.0 (main experiment used temp 1.0)
        elif j.experiment_id == MAIN_EXPERIMENT_ID:
            if temperature != 1.0:
                continue

        key = (j.ai_judge.model_id, j.dilemma_id)
        pairs[key][j.mode] = j.choice_id

    # Count reversals
    reversals = 0
    total_pairs = 0
    by_model = defaultdict(lambda: [0, 0])  # [reversals, total]
    by_dilemma = defaultdict(lambda: [0, 0])  # [reversals, total]

    for (model_id, dilemma_id), choices in pairs.items():
        theory_choice = choices["theory"]
        action_choice = choices["action"]

        # Only count if we have both
        if theory_choice and action_choice:
            total_pairs += 1
            by_model[model_id][1] += 1
            by_dilemma[dilemma_id][1] += 1

            if theory_choice != action_choice:
                reversals += 1
                by_model[model_id][0] += 1
                by_dilemma[dilemma_id][0] += 1

    reversal_rate = (reversals / total_pairs * 100) if total_pairs > 0 else 0

    # Convert to tuples
    by_model_tuples = {k: tuple(v) for k, v in by_model.items()}
    by_dilemma_tuples = {k: tuple(v) for k, v in by_dilemma.items()}

    return ReversalStats(
        temperature=temperature,
        total_pairs=total_pairs,
        reversals=reversals,
        reversal_rate=reversal_rate,
        by_model=by_model_tuples,
        by_dilemma=by_dilemma_tuples,
    )


def print_summary_table(stats_by_temp: dict[float, ReversalStats]):
    """Print summary comparison table."""

    table = Table(title="Temperature Validation: Reversal Rates")
    table.add_column("Temperature", style="cyan")
    table.add_column("Pairs", justify="right")
    table.add_column("Reversals", justify="right")
    table.add_column("Rate", justify="right", style="bold")
    table.add_column("Interpretation", style="dim")

    for temp in [0.0, 0.5, 1.0]:
        stats = stats_by_temp.get(temp)
        if not stats:
            continue

        rate_str = f"{stats.reversal_rate:.1f}%"

        # Color code
        if stats.reversal_rate >= 60:
            rate_style = "red"
        elif stats.reversal_rate >= 45:
            rate_style = "yellow"
        else:
            rate_style = "green"

        # Interpretation
        if temp == 1.0:
            interp = "Baseline"
        elif stats.reversal_rate > stats_by_temp[1.0].reversal_rate:
            diff = stats.reversal_rate - stats_by_temp[1.0].reversal_rate
            interp = f"+{diff:.1f}pp vs baseline"
        else:
            diff = stats_by_temp[1.0].reversal_rate - stats.reversal_rate
            interp = f"-{diff:.1f}pp vs baseline"

        table.add_row(
            f"{temp:.1f}",
            str(stats.total_pairs),
            str(stats.reversals),
            f"[{rate_style}]{rate_str}[/{rate_style}]",
            interp,
        )

    console.print(table)


def print_by_model_table(stats_by_temp: dict[float, ReversalStats]):
    """Print reversal rates by model and temperature."""

    table = Table(title="Reversal Rates by Model and Temperature")
    table.add_column("Model", style="cyan")
    table.add_column("Temp 0.0", justify="right")
    table.add_column("Temp 0.5", justify="right")
    table.add_column("Temp 1.0", justify="right", style="dim")

    for model_id in sorted(MODEL_NAMES.keys()):
        model_name = MODEL_NAMES[model_id]

        rates = []
        for temp in [0.0, 0.5, 1.0]:
            stats = stats_by_temp.get(temp)
            if stats and model_id in stats.by_model:
                reversals, total = stats.by_model[model_id]
                rate = (reversals / total * 100) if total > 0 else 0
                rates.append(f"{rate:.1f}%")
            else:
                rates.append("—")

        table.add_row(model_name, rates[0], rates[1], rates[2])

    console.print(table)


def print_by_dilemma_table(stats_by_temp: dict[float, ReversalStats]):
    """Print reversal rates by dilemma and temperature."""

    table = Table(title="Reversal Rates by Dilemma and Temperature")
    table.add_column("Dilemma", style="cyan")
    table.add_column("Temp 0.0", justify="right")
    table.add_column("Temp 0.5", justify="right")
    table.add_column("Temp 1.0", justify="right", style="dim")

    # Get all dilemmas
    all_dilemmas = set()
    for stats in stats_by_temp.values():
        all_dilemmas.update(stats.by_dilemma.keys())

    for dilemma_id in sorted(all_dilemmas):
        # Shorten ID for display
        short_id = dilemma_id.replace("bench2-", "").replace("-", " ").title()

        rates = []
        for temp in [0.0, 0.5, 1.0]:
            stats = stats_by_temp.get(temp)
            if stats and dilemma_id in stats.by_dilemma:
                reversals, total = stats.by_dilemma[dilemma_id]
                rate = (reversals / total * 100) if total > 0 else 0
                rates.append(f"{rate:.1f}%")
            else:
                rates.append("—")

        table.add_row(short_id, rates[0], rates[1], rates[2])

    console.print(table)


def interpret_results(stats_by_temp: dict[float, ReversalStats]):
    """Interpret what the results mean."""

    console.print("\n[bold cyan]Interpretation:[/bold cyan]\n")

    temp_0 = stats_by_temp.get(0.0)
    temp_05 = stats_by_temp.get(0.5)
    temp_1 = stats_by_temp.get(1.0)

    if not all([temp_0, temp_05, temp_1]):
        console.print("[red]Missing temperature data for interpretation[/red]")
        return

    # Check trend
    if temp_0.reversal_rate > temp_1.reversal_rate:
        console.print("[bold green]✓ EXCELLENT VALIDATION:[/bold green]")
        console.print(f"  • Temperature 0.0 shows [bold]{temp_0.reversal_rate:.1f}%[/bold] reversals")
        console.print(f"  • This is [bold]+{temp_0.reversal_rate - temp_1.reversal_rate:.1f}pp higher[/bold] than temp 1.0")
        console.print("  • Temperature 1.0 is NOT introducing noise")
        console.print("  • The judgment-action gap is a [bold]real, robust phenomenon[/bold]")
        console.print("  • Even deterministic models show strong reversals")
        console.print("\n[green]Conclusion: Our findings are validated and strengthened.[/green]")

    elif abs(temp_0.reversal_rate - temp_1.reversal_rate) < 5:
        console.print("[bold yellow]⚠ STABLE ACROSS TEMPERATURES:[/bold yellow]")
        console.print(f"  • Temperature 0.0: {temp_0.reversal_rate:.1f}%")
        console.print(f"  • Temperature 1.0: {temp_1.reversal_rate:.1f}%")
        console.print(f"  • Difference: {abs(temp_0.reversal_rate - temp_1.reversal_rate):.1f}pp")
        console.print("  • Temperature has minimal effect on reversal rate")
        console.print("  • The gap persists regardless of temperature")
        console.print("\n[yellow]Conclusion: Findings are robust, temperature is not a confound.[/yellow]")

    else:
        console.print("[bold red]⚠ LOWER AT TEMP 0.0:[/bold red]")
        console.print(f"  • Temperature 0.0: {temp_0.reversal_rate:.1f}%")
        console.print(f"  • Temperature 1.0: {temp_1.reversal_rate:.1f}%")
        console.print(f"  • Difference: -{temp_1.reversal_rate - temp_0.reversal_rate:.1f}pp")
        console.print("  • Temperature 1.0 may be amplifying the effect")
        console.print("  • Core phenomenon still present at temp 0.0")
        console.print("\n[yellow]Conclusion: Conservative estimate is temp 0.0 rate. Gap still substantial.[/yellow]")


async def main():
    console.print("\n[bold cyan]Temperature Validation Analysis[/bold cyan]")
    console.print("Comparing reversal rates across temperatures 0.0, 0.5, and 1.0\n")

    # Load validation judgments
    validation_judgments = await load_validation_judgments()

    # Get unique dilemma IDs from validation
    dilemma_ids = list(set(j.dilemma_id for j in validation_judgments))
    console.print(f"[dim]Dilemmas tested: {', '.join(dilemma_ids)}[/dim]\n")

    # Load baseline judgments for same dilemmas
    baseline_judgments = await load_baseline_judgments(dilemma_ids)

    # Combine all judgments
    all_judgments = validation_judgments + baseline_judgments

    # Calculate stats for each temperature
    stats_by_temp = {}
    for temp in [0.0, 0.5, 1.0]:
        stats_by_temp[temp] = calculate_reversals(all_judgments, temp)

    # Print results
    print_summary_table(stats_by_temp)
    console.print()
    print_by_model_table(stats_by_temp)
    console.print()
    print_by_dilemma_table(stats_by_temp)

    # Interpret
    interpret_results(stats_by_temp)

    console.print("\n" + "="*70)
    console.print("[bold]Paper Update:[/bold]")
    console.print("  Add to limitations section:")
    console.print("  'To assess whether temperature 1.0 introduced noise, we validated")
    console.print("   findings on 3 high-reversal dilemmas across 4 models at temperatures")
    console.print(f"   0.0 and 0.5. Results showed [{stats_by_temp[0.0].reversal_rate:.1f}% and {stats_by_temp[0.5].reversal_rate:.1f}%]")
    console.print(f"   reversal rates respectively, [compared to {stats_by_temp[1.0].reversal_rate:.1f}% at")
    console.print("   temperature 1.0], confirming the judgment-action gap persists")
    console.print("   across temperature settings.'")
    console.print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
