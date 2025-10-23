"""Analyze consistency of LLM judgements from repetition experiments.

Computes metrics:
1. Choice Consistency: % that picked the same choice
2. Reasoning Similarity: Jaccard similarity of reasoning text
3. Confidence Variation: Standard deviation of confidence scores

Usage:
    uv run python scripts/analyze_consistency.py <experiment_id>
    uv run python scripts/analyze_consistency.py --all  # Analyze all experiments
"""

import asyncio
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import JudgementDB

console = Console()


def jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity between two texts.

    Simple word-level Jaccard: intersection / union of word sets.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score 0.0-1.0
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


async def analyze_experiment(experiment_id: str):
    """Analyze consistency metrics for a single experiment.

    Args:
        experiment_id: Experiment ID to analyze
    """
    console.print(f"\n[bold cyan]Analyzing Experiment: {experiment_id}[/bold cyan]\n")

    db = get_database()
    async for session in db.get_session():
        # Load all judgements for this experiment
        statement = select(JudgementDB).where(JudgementDB.experiment_id == experiment_id)
        result = await session.execute(statement)
        judgement_dbs = result.scalars().all()

        if not judgement_dbs:
            console.print(f"[red]No judgements found for experiment {experiment_id}[/red]")
            return

        judgements = [jdb.to_domain() for jdb in judgement_dbs]
        console.print(f"[green]Found {len(judgements)} judgements[/green]\n")

        # Group by (model, dilemma, temperature)
        groups = defaultdict(list)
        for j in judgements:
            key = (j.get_judge_id(), j.dilemma_id, j.ai_judge.temperature if j.ai_judge else None)
            groups[key].append(j)

        # Compute metrics for each group
        results = []

        for (model_id, dilemma_id, temperature), group_judgements in groups.items():
            if len(group_judgements) < 2:
                continue  # Need at least 2 for comparison

            # Sort by repetition number
            group_judgements.sort(key=lambda j: j.repetition_number or 0)

            # METRIC 1: Choice Consistency
            choices = [j.choice_id for j in group_judgements if j.choice_id]
            if choices:
                choice_counts = Counter(choices)
                most_common_choice, most_common_count = choice_counts.most_common(1)[0]
                choice_consistency = most_common_count / len(choices) * 100
            else:
                most_common_choice = "N/A"
                choice_consistency = 0.0

            # METRIC 2: Reasoning Similarity (pairwise average)
            reasonings = [j.reasoning for j in group_judgements]
            similarities = []
            for i in range(len(reasonings)):
                for j in range(i + 1, len(reasonings)):
                    sim = jaccard_similarity(reasonings[i], reasonings[j])
                    similarities.append(sim)

            avg_similarity = mean(similarities) if similarities else 0.0

            # METRIC 3: Confidence Variation
            confidences = [j.confidence for j in group_judgements if j.confidence is not None]
            if len(confidences) >= 2:
                confidence_mean = mean(confidences)
                confidence_std = stdev(confidences)
            elif len(confidences) == 1:
                confidence_mean = confidences[0]
                confidence_std = 0.0
            else:
                confidence_mean = 0.0
                confidence_std = 0.0

            # Load dilemma title for display
            # (For now, just use dilemma_id - could load from DB)
            results.append({
                "model_id": model_id,
                "dilemma_id": dilemma_id[:12] + "...",  # Truncate for display
                "temperature": temperature,
                "repetitions": len(group_judgements),
                "choice_consistency": choice_consistency,
                "most_common_choice": most_common_choice,
                "reasoning_similarity": avg_similarity * 100,
                "confidence_mean": confidence_mean,
                "confidence_std": confidence_std,
            })

        # Sort by temperature, then model
        results.sort(key=lambda r: (r["temperature"], r["model_id"]))

        # Display results
        table = Table(title="Consistency Analysis Results", show_header=True)
        table.add_column("Model", style="cyan", width=25)
        table.add_column("Dilemma", style="white", width=16)
        table.add_column("Temp", justify="right", style="yellow", width=6)
        table.add_column("Reps", justify="right", style="green", width=6)
        table.add_column("Choice\nConsist%", justify="right", style="magenta", width=10)
        table.add_column("Top\nChoice", style="blue", width=8)
        table.add_column("Reason\nSim%", justify="right", style="cyan", width=10)
        table.add_column("Conf\nMean", justify="right", style="green", width=8)
        table.add_column("Conf\nStdDev", justify="right", style="red", width=8)

        for r in results:
            table.add_row(
                r["model_id"],
                r["dilemma_id"],
                f"{r['temperature']:.1f}",
                str(r["repetitions"]),
                f"{r['choice_consistency']:.0f}%",
                r["most_common_choice"],
                f"{r['reasoning_similarity']:.0f}%",
                f"{r['confidence_mean']:.1f}",
                f"{r['confidence_std']:.2f}",
            )

        console.print(table)

        # Summary statistics
        console.print("\n[bold]Summary by Temperature:[/bold]")

        temp_summary = defaultdict(lambda: {
            "choice_consistency": [],
            "reasoning_similarity": [],
            "confidence_std": []
        })

        for r in results:
            temp = r["temperature"]
            temp_summary[temp]["choice_consistency"].append(r["choice_consistency"])
            temp_summary[temp]["reasoning_similarity"].append(r["reasoning_similarity"])
            temp_summary[temp]["confidence_std"].append(r["confidence_std"])

        summary_table = Table(show_header=True)
        summary_table.add_column("Temperature", style="yellow")
        summary_table.add_column("Avg Choice Consistency", justify="right", style="magenta")
        summary_table.add_column("Avg Reasoning Similarity", justify="right", style="cyan")
        summary_table.add_column("Avg Confidence StdDev", justify="right", style="red")

        for temp in sorted(temp_summary.keys()):
            data = temp_summary[temp]
            summary_table.add_row(
                f"{temp:.1f}",
                f"{mean(data['choice_consistency']):.1f}%",
                f"{mean(data['reasoning_similarity']):.1f}%",
                f"{mean(data['confidence_std']):.2f}",
            )

        console.print(summary_table)

        # Key insights
        console.print("\n[bold green]Key Insights:[/bold green]")

        # Find most/least consistent temperatures
        if temp_summary:
            temp_choice_consistency = {
                temp: mean(data["choice_consistency"])
                for temp, data in temp_summary.items()
            }
            most_consistent_temp = max(temp_choice_consistency.items(), key=lambda x: x[1])
            least_consistent_temp = min(temp_choice_consistency.items(), key=lambda x: x[1])

            console.print(
                f"• Most consistent temperature: [green]{most_consistent_temp[0]:.1f}[/green] "
                f"({most_consistent_temp[1]:.1f}% choice consistency)"
            )
            console.print(
                f"• Least consistent temperature: [red]{least_consistent_temp[0]:.1f}[/red] "
                f"({least_consistent_temp[1]:.1f}% choice consistency)"
            )

            # Check if temp=0 is 100% consistent
            if 0.0 in temp_choice_consistency:
                temp0_consistency = temp_choice_consistency[0.0]
                if temp0_consistency == 100.0:
                    console.print("• [green]✓ Temperature 0.0 is perfectly deterministic![/green]")
                else:
                    console.print(
                        f"• [yellow]⚠ Temperature 0.0 is NOT 100% deterministic "
                        f"({temp0_consistency:.1f}%)[/yellow]"
                    )


async def list_all_experiments():
    """List all experiment IDs in the database."""
    console.print("\n[bold cyan]All Experiments in Database[/bold cyan]\n")

    db = get_database()
    async for session in db.get_session():
        # Get distinct experiment IDs
        statement = select(JudgementDB.experiment_id).distinct()
        result = await session.execute(statement)
        experiment_ids = [row[0] for row in result.all() if row[0] is not None]

        if not experiment_ids:
            console.print("[yellow]No experiments found in database[/yellow]")
            return

        console.print(f"[green]Found {len(experiment_ids)} experiments:[/green]\n")

        for exp_id in experiment_ids:
            # Count judgements for this experiment
            count_stmt = select(JudgementDB).where(JudgementDB.experiment_id == exp_id)
            count_result = await session.execute(count_stmt)
            count = len(count_result.scalars().all())

            console.print(f"  {exp_id} ({count} judgements)")

        console.print("\n[bold]To analyze:[/bold]")
        console.print(f"  [cyan]uv run python scripts/analyze_consistency.py {experiment_ids[0]}[/cyan]")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[yellow]Usage:[/yellow]")
        console.print("  [cyan]uv run python scripts/analyze_consistency.py <experiment_id>[/cyan]")
        console.print("  [cyan]uv run python scripts/analyze_consistency.py --list[/cyan]")
        console.print()
        await list_all_experiments()
        return

    arg = sys.argv[1]

    if arg == "--list":
        await list_all_experiments()
    else:
        await analyze_experiment(arg)


if __name__ == "__main__":
    asyncio.run(main())
