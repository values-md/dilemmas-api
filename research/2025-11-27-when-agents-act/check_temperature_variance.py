#!/usr/bin/env python3
"""
Analyze within-mode variance to assess temperature 1.0 stability.

Question: Is temp 1.0 adding noise, or are our mode differences real signal?

Method:
1. For each (model, base_dilemma, mode) combination
2. Check if model made same choice across all demographic variations
3. Calculate within-mode consistency rate
4. Compare to between-mode consistency (our 47.6% reversal rate)

Expected: High within-mode consistency + low between-mode = real effect
Concerning: Low within-mode consistency = temp 1.0 too noisy
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

EXPERIMENT_ID = "03de21a4-25ed-4df4-b03a-4715b1ca1256"

# Model short names
MODEL_NAMES = {
    "anthropic/claude-haiku-4.5": "Claude Haiku 4.5",
    "anthropic/claude-opus-4.5": "Claude Opus 4.5",
    "anthropic/claude-sonnet-4.5": "Claude Sonnet 4.5",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "google/gemini-3-pro-preview": "Gemini 3 Pro",
    "openai/gpt-5": "GPT-5",
    "openai/gpt-5-nano": "GPT-5 Nano",
    "x-ai/grok-4": "Grok-4",
    "x-ai/grok-4-fast": "Grok-4 Fast",
}


@dataclass
class ConsistencyStats:
    """Within-mode consistency statistics."""
    model: str
    total_groups: int  # Number of (base_dilemma, mode) groups
    consistent_groups: int  # Groups where all variations had same choice
    consistency_rate: float  # % of groups that were consistent
    total_variations: int  # Total variation count across all groups


def extract_base_dilemma_id(dilemma_id: str) -> str:
    """
    Extract base dilemma ID without variation suffix.

    Examples:
    - bench2-01-phone-agent-child-v1 -> bench2-01-phone-agent-child
    - bench2-05-surgical-robot-tremor-v2 -> bench2-05-surgical-robot-tremor
    """
    if "-v" in dilemma_id:
        return dilemma_id.rsplit("-v", 1)[0]
    return dilemma_id


async def load_judgments():
    """Load all judgments for this experiment."""
    console.print("[yellow]Loading judgments from database...[/yellow]")

    async for session in get_session():
        result = await session.execute(
            select(JudgementDB).where(JudgementDB.experiment_id == EXPERIMENT_ID)
        )
        db_judgments = result.scalars().all()

        judgments = [j.to_domain() for j in db_judgments]
        console.print(f"[green]Loaded {len(judgments)} judgments[/green]\n")

        return judgments


def analyze_within_mode_consistency(judgments):
    """
    Analyze consistency within each (model, base_dilemma, mode) group.

    Returns dict: model -> ConsistencyStats
    """
    console.print("[yellow]Analyzing within-mode consistency...[/yellow]\n")

    # Group judgments by (model, base_dilemma, mode)
    groups = defaultdict(list)

    for j in judgments:
        # Skip human judgments
        if not j.ai_judge:
            continue

        base_dilemma = extract_base_dilemma_id(j.dilemma_id)
        mode = j.mode  # Mode is a direct field on Judgement
        model_id = j.ai_judge.model_id
        key = (model_id, base_dilemma, mode)
        groups[key].append(j)

    # Calculate consistency per model
    model_stats = {}

    for model in MODEL_NAMES.keys():
        model_groups = [(k, v) for k, v in groups.items() if k[0] == model]

        if not model_groups:
            continue

        total_groups = len(model_groups)
        consistent_groups = 0
        total_variations = 0

        for key, group_judgments in model_groups:
            total_variations += len(group_judgments)

            # Check if all judgments in this group made the same choice
            choices = [j.choice_id for j in group_judgments]
            if len(set(choices)) == 1:
                consistent_groups += 1

        consistency_rate = (consistent_groups / total_groups * 100) if total_groups > 0 else 0

        model_stats[model] = ConsistencyStats(
            model=MODEL_NAMES[model],
            total_groups=total_groups,
            consistent_groups=consistent_groups,
            consistency_rate=consistency_rate,
            total_variations=total_variations,
        )

    return model_stats


def print_consistency_table(model_stats):
    """Print consistency statistics in a table."""

    table = Table(title="Within-Mode Consistency (Temperature 1.0)")
    table.add_column("Model", style="cyan")
    table.add_column("Groups", justify="right")
    table.add_column("Consistent", justify="right")
    table.add_column("Rate", justify="right", style="bold")
    table.add_column("Variations", justify="right")

    # Sort by consistency rate (descending)
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1].consistency_rate, reverse=True)

    for model_id, stats in sorted_models:
        rate_str = f"{stats.consistency_rate:.1f}%"

        # Color code based on rate
        if stats.consistency_rate >= 80:
            rate_style = "green"
        elif stats.consistency_rate >= 60:
            rate_style = "yellow"
        else:
            rate_style = "red"

        table.add_row(
            stats.model,
            str(stats.total_groups),
            str(stats.consistent_groups),
            f"[{rate_style}]{rate_str}[/{rate_style}]",
            str(stats.total_variations),
        )

    console.print(table)


def calculate_overall_stats(model_stats):
    """Calculate overall consistency statistics."""

    total_groups = sum(s.total_groups for s in model_stats.values())
    consistent_groups = sum(s.consistent_groups for s in model_stats.values())
    overall_rate = (consistent_groups / total_groups * 100) if total_groups > 0 else 0

    console.print(f"\n[bold cyan]Overall Statistics:[/bold cyan]")
    console.print(f"  Total (model, dilemma, mode) groups: {total_groups}")
    console.print(f"  Consistent groups: {consistent_groups}")
    console.print(f"  [bold]Overall consistency rate: {overall_rate:.1f}%[/bold]")

    return overall_rate


def interpret_results(overall_consistency, between_mode_consistency=52.4):
    """
    Interpret what the consistency rate means.

    between_mode_consistency = 100 - 47.6 (reversal rate) = 52.4%
    """
    console.print(f"\n[bold cyan]Interpretation:[/bold cyan]")

    console.print(f"  Within-mode consistency:  {overall_consistency:.1f}%")
    console.print(f"  Between-mode consistency: {between_mode_consistency:.1f}%")
    console.print(f"  Difference: {overall_consistency - between_mode_consistency:+.1f}pp")

    if overall_consistency >= 80:
        console.print(f"\n[bold green]✓ EXCELLENT:[/bold green] High within-mode consistency indicates:")
        console.print("  • Temperature 1.0 is NOT adding excessive noise")
        console.print("  • Demographic variations don't change decisions much")
        console.print("  • Mode differences (47.6% reversal) are REAL signal, not noise")
        console.print("  • Our findings are robust")

    elif overall_consistency >= 60:
        console.print(f"\n[bold yellow]⚠ MODERATE:[/bold yellow] Some within-mode variance, but acceptable:")
        console.print("  • Temperature 1.0 adds some variability")
        console.print("  • Still substantially higher than between-mode consistency")
        console.print("  • Consider temp 0 validation for a few dilemmas")

    else:
        console.print(f"\n[bold red]✗ CONCERNING:[/bold red] Low within-mode consistency suggests:")
        console.print("  • Temperature 1.0 may be too noisy")
        console.print("  • Hard to separate signal from noise")
        console.print("  • Should rerun key dilemmas at temp 0")


async def main():
    console.print("\n[bold cyan]Temperature 1.0 Variance Analysis[/bold cyan]")
    console.print("Question: Is temp 1.0 stable enough for our findings?\n")

    # Load data
    judgments = await load_judgments()

    # Analyze consistency
    model_stats = analyze_within_mode_consistency(judgments)

    # Print results
    print_consistency_table(model_stats)
    overall_rate = calculate_overall_stats(model_stats)

    # Interpret
    interpret_results(overall_rate)

    console.print("\n" + "="*70)
    console.print("[bold]Next Steps:[/bold]")
    console.print("  1. If consistency ≥80%: Temperature 1.0 is fine, mention in paper")
    console.print("  2. If consistency 60-80%: Consider small temp 0 validation")
    console.print("  3. If consistency <60%: Rerun key dilemmas at temp 0")
    console.print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
