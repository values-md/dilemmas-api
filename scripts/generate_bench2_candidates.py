#!/usr/bin/env python3
"""Generate bench-2-candidates collection for manual curation.

This script generates 20 candidate dilemmas using Claude Sonnet 4.5:
- Framework diversity (deontological vs consequentialist etc.)
- 150-250 words (human-readable)
- Difficulty 6-8 (moderate-hard)
- No validation (too expensive for candidates)
- No variable extraction (manual curation step later)

Usage:
    uv run python scripts/generate_bench2_candidates.py
"""

import asyncio
import random
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from dilemmas.db.database import get_database
from dilemmas.models.config import get_config
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator
from dilemmas.services.seeds import generate_random_seed

console = Console()

# Use Claude Sonnet 4.5 for higher quality
MODEL = "anthropic/claude-sonnet-4.5"

# Use v9_framework_diverse prompt (bench-2 specific)
PROMPT_VERSION = "v9_framework_diverse"

# Bench-2 generation plan: 20 candidates, difficulty 6-8
GENERATION_PLAN = [
    # Difficulty 6: 7 dilemmas
    {"difficulty": 6},
    {"difficulty": 6},
    {"difficulty": 6},
    {"difficulty": 6},
    {"difficulty": 6},
    {"difficulty": 6},
    {"difficulty": 6},

    # Difficulty 7: 8 dilemmas
    {"difficulty": 7},
    {"difficulty": 7},
    {"difficulty": 7},
    {"difficulty": 7},
    {"difficulty": 7},
    {"difficulty": 7},
    {"difficulty": 7},
    {"difficulty": 7},

    # Difficulty 8: 5 dilemmas
    {"difficulty": 8},
    {"difficulty": 8},
    {"difficulty": 8},
    {"difficulty": 8},
    {"difficulty": 8},
]


def print_welcome():
    """Print welcome banner."""
    welcome = Panel.fit(
        "[bold cyan]🎯 bench-2-candidates Generator[/bold cyan]\n"
        "Generating 20 candidate dilemmas for manual curation\n\n"
        "[dim]Model: Claude Sonnet 4.5 | Prompt: v9_framework_diverse[/dim]\n"
        "[dim]Focus: Framework diversity + Human readability[/dim]",
        border_style="cyan",
    )
    console.print(welcome)
    console.print()


def print_plan():
    """Print generation plan."""
    console.print("[bold]Generation Plan:[/bold]")
    console.print(f"  Total candidates: [bold]{len(GENERATION_PLAN)}[/bold]")
    console.print(f"  Target for final bench-2: [bold]10 dilemmas[/bold] (manual selection)")

    # Count by difficulty
    diff_counts = {}
    for item in GENERATION_PLAN:
        diff = item["difficulty"]
        diff_counts[diff] = diff_counts.get(diff, 0) + 1

    console.print("\n  [bold]Difficulty distribution:[/bold]")
    for diff in sorted(diff_counts.keys()):
        console.print(f"    Difficulty {diff}: {diff_counts[diff]} candidates")

    console.print("\n  [bold]Quality requirements:[/bold]")
    console.print("    • Length: 150-250 words (human-readable)")
    console.print("    • Framework diversity: Reveal ethical framework tensions")
    console.print("    • Variable potential: Country, institution, organization, amount, etc.")
    console.print("    • AI-centric framing: Always \"You are an AI system...\"")

    console.print("\n  [bold]Settings:[/bold]")
    console.print(f"    Model: {MODEL}")
    console.print(f"    Prompt: {PROMPT_VERSION}")
    console.print("    ⚠️  Validation disabled (candidates only)")
    console.print("    ⚠️  Variables NOT extracted (manual step later)")

    console.print("\n  [bold]Collection:[/bold] bench-2-candidates")
    console.print()


async def generate_candidates() -> list[DilemmaDB]:
    """Generate bench-2-candidates collection.

    Returns:
        List of saved DilemmaDB instances
    """
    config = get_config()
    db = get_database()
    batch_id = str(uuid.uuid4())
    collection = "bench-2-candidates"

    saved_dilemmas = []
    failed_dilemmas = []

    console.print(f"[dim]Batch ID: {batch_id[:8]}...[/dim]")
    console.print(f"[dim]Experiment: When Agents Act v2.0[/dim]\n")

    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        overall_task = progress.add_task("[cyan]Overall progress", total=len(GENERATION_PLAN))

        for i, plan_item in enumerate(GENERATION_PLAN, 1):
            difficulty = plan_item["difficulty"]

            # Update progress
            progress.update(
                overall_task,
                description=f"[cyan]Generating {i}/{len(GENERATION_PLAN)} (difficulty: {difficulty})",
            )

            # Create generator for this dilemma
            generator = DilemmaGenerator(
                model_id=MODEL,
                prompt_version=PROMPT_VERSION
            )

            # Try with retries
            max_retries = 3
            dilemma = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    # Generate random seed for this difficulty
                    seed = generate_random_seed(
                        library=generator.seed_library,
                        difficulty=difficulty,
                        num_actors=config.generation.num_actors,
                        num_stakes=config.generation.num_stakes,
                    )

                    # Generate WITHOUT validation (too expensive for candidates)
                    # Variables will be extracted manually later
                    # Note: difficulty already embedded in seed
                    dilemma = await generator.generate_from_seed(seed=seed)

                    # Success!
                    break

                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        # All retries exhausted
                        error_msg = str(e)
                        if len(error_msg) > 100:
                            error_msg = error_msg[:100] + "..."

                        console.print(f"[yellow]⚠[/yellow] Skipped candidate {i}/{len(GENERATION_PLAN)}: {error_msg}")
                        failed_dilemmas.append({
                            'index': i,
                            'difficulty': difficulty,
                            'error': error_msg
                        })
                        dilemma = None
                        break
                    continue

            # Skip if generation failed
            if dilemma is None:
                progress.update(overall_task, advance=1)
                continue

            # Apply collection and batch_id
            dilemma.collection = collection
            dilemma.batch_id = batch_id

            # Save to database
            try:
                async for session in db.get_session():
                    db_dilemma = DilemmaDB.from_domain(dilemma)
                    session.add(db_dilemma)
                    await session.commit()
                    saved_dilemmas.append(db_dilemma)

                # Calculate word count for verification
                word_count = len(dilemma.situation_template.split())
                word_status = "✓" if 150 <= word_count <= 250 else "⚠"

                # Print success
                console.print(
                    f"  [green]✓[/green] Generated: [bold]{dilemma.title}[/bold] "
                    f"(diff {dilemma.difficulty_intended}, ID: {dilemma.id[:8]}..., "
                    f"{word_status} {word_count} words)"
                )
            except Exception as e:
                error_msg = str(e)[:100]
                console.print(f"[yellow]⚠[/yellow] Failed to save candidate {i}/{len(GENERATION_PLAN)}: {error_msg}")
                failed_dilemmas.append({
                    'index': i,
                    'difficulty': difficulty,
                    'error': f"DB save error: {error_msg}"
                })

            # Update progress
            progress.update(overall_task, advance=1)

    await db.close()

    # Print failure summary if any
    if failed_dilemmas:
        console.print(f"\n[yellow]⚠ {len(failed_dilemmas)} candidates failed:[/yellow]")
        for failure in failed_dilemmas:
            console.print(
                f"  #{failure['index']}: difficulty {failure['difficulty']} - {failure['error']}"
            )

    return saved_dilemmas


def print_results(dilemmas: list[DilemmaDB]):
    """Print generation results summary."""
    console.print("\n" + "=" * 80)
    console.print("[bold green]✓ bench-2-candidates Generation Complete![/bold green]")
    console.print("=" * 80)

    # Success stats
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Target: {len(GENERATION_PLAN)} candidates")
    console.print(f"  Generated: [green]{len(dilemmas)}[/green] dilemmas")
    if len(dilemmas) < len(GENERATION_PLAN):
        console.print(f"  Failed: [yellow]{len(GENERATION_PLAN) - len(dilemmas)}[/yellow]")
        console.print(f"  Success rate: [cyan]{len(dilemmas)/len(GENERATION_PLAN)*100:.1f}%[/cyan]")

    if len(dilemmas) == 0:
        console.print("\n[red]No candidates generated. Check errors above.[/red]")
        return

    # Quality stats
    total_words = 0
    word_compliant = 0
    has_tools = 0
    choice_counts = []

    for db_dilemma in dilemmas:
        dilemma = db_dilemma.to_domain()
        word_count = len(dilemma.situation_template.split())
        total_words += word_count
        if 150 <= word_count <= 250:
            word_compliant += 1
        if dilemma.available_tools:
            has_tools += 1
        choice_counts.append(len(dilemma.choices))

    avg_words = total_words / len(dilemmas)
    avg_choices = sum(choice_counts) / len(choice_counts)

    console.print(f"\n[bold]Quality Stats:[/bold]")
    console.print(f"  Length compliant: [green]{word_compliant}/{len(dilemmas)}[/green] ({word_compliant/len(dilemmas)*100:.1f}% in 150-250 words)")
    console.print(f"  Avg word count: [cyan]{avg_words:.0f} words[/cyan]")
    console.print(f"  Has tools: [cyan]{has_tools}/{len(dilemmas)}[/cyan] ({has_tools/len(dilemmas)*100:.1f}%)")
    console.print(f"  Avg choices: [cyan]{avg_choices:.1f}[/cyan]")

    # Difficulty distribution
    difficulty_counts = {}
    for d in dilemmas:
        dilemma = d.to_domain()
        diff = dilemma.difficulty_intended
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

    console.print("\n[bold]Difficulty Distribution:[/bold]")
    for diff in sorted(difficulty_counts.keys()):
        bar = "█" * difficulty_counts[diff]
        console.print(f"  {diff:2d}/10: [cyan]{bar}[/cyan] ({difficulty_counts[diff]})")

    # Sample titles (first 5)
    console.print("\n[bold]Sample Titles:[/bold]")
    for db_dilemma in dilemmas[:5]:
        dilemma = db_dilemma.to_domain()
        word_count = len(dilemma.situation_template.split())
        console.print(f"  • {dilemma.title} ({word_count} words)")

    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Export candidates:")
    console.print("     [cyan]uv run python scripts/export_dilemmas.py --collection bench-2-candidates --output research/2025-11-27-when-agents-act/candidates.json[/cyan]")
    console.print()
    console.print("  2. Manual curation:")
    console.print("     - Review all 20 candidates in candidates.json")
    console.print("     - Select best 10 using quality checklist")
    console.print("     - Check: framework diversity, length, variable potential")
    console.print()
    console.print("  3. View in browser:")
    console.print("     [cyan]uv run python scripts/serve.py[/cyan]")
    console.print()
    console.print("  4. Filter in database:")
    console.print("     [cyan]SELECT * FROM dilemmas WHERE collection = 'bench-2-candidates'[/cyan]")

    console.print("\n" + "=" * 80 + "\n")


async def main():
    """Main execution flow."""
    try:
        # Welcome
        print_welcome()

        # Show plan
        print_plan()

        # Generate
        saved_dilemmas = await generate_candidates()

        # Print results
        print_results(saved_dilemmas)

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
