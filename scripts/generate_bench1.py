#!/usr/bin/env python3
"""Generate bench-1 collection with precise diversity strategy.

This script generates 20 high-quality dilemmas for the bench-1 benchmark collection:
- 50% concise (v8_concise) for human reviewability
- Multi-dimensional diversity (prompts, difficulty, models, seeds)
- Quality validation enabled (min_quality_score: 7.0)
- Variables extracted for future bias testing

Usage:
    uv run python scripts/generate_bench1.py
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
from rich.prompt import Confirm

from dilemmas.db.database import get_database
from dilemmas.models.config import get_config
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator
from dilemmas.services.seeds import generate_random_seed

console = Console()

# Using only Gemini 2.5 Flash for bench-1
TOP_TIER_MODELS = [
    "google/gemini-2.5-flash",  # Gemini 2.5 Flash - fast and reliable
]

# Lower quality threshold for more flexibility (5.0 instead of 7.0)
MIN_QUALITY_SCORE = 5.0

# Bench-1 generation plan (v8_concise only for now - other prompts need tool guidance updates)
GENERATION_PLAN = [
    # Easy (1-3): 4 dilemmas
    {"difficulty": 1, "prompt": "v8_concise"},
    {"difficulty": 2, "prompt": "v8_concise"},
    {"difficulty": 3, "prompt": "v8_concise"},
    {"difficulty": 3, "prompt": "v8_concise"},

    # Medium (4-6): 8 dilemmas
    {"difficulty": 4, "prompt": "v8_concise"},
    {"difficulty": 4, "prompt": "v8_concise"},
    {"difficulty": 5, "prompt": "v8_concise"},
    {"difficulty": 5, "prompt": "v8_concise"},
    {"difficulty": 5, "prompt": "v8_concise"},
    {"difficulty": 6, "prompt": "v8_concise"},
    {"difficulty": 6, "prompt": "v8_concise"},
    {"difficulty": 6, "prompt": "v8_concise"},

    # Hard (7-9): 6 dilemmas
    {"difficulty": 7, "prompt": "v8_concise"},
    {"difficulty": 7, "prompt": "v8_concise"},
    {"difficulty": 8, "prompt": "v8_concise"},
    {"difficulty": 8, "prompt": "v8_concise"},
    {"difficulty": 9, "prompt": "v8_concise"},
    {"difficulty": 9, "prompt": "v8_concise"},

    # Extreme (10): 2 dilemmas
    {"difficulty": 10, "prompt": "v8_concise"},
    {"difficulty": 10, "prompt": "v8_concise"},
]


def print_welcome():
    """Print welcome banner."""
    welcome = Panel.fit(
        "[bold cyan]🎯 bench-1 Collection Generator[/bold cyan]\n"
        "Generating 20 high-quality ethical dilemmas with validation\n\n"
        "[dim]Strategy: 100% v8_concise (only prompt with tool guidance)[/dim]",
        border_style="cyan",
    )
    console.print(welcome)
    console.print()


def print_plan():
    """Print generation plan."""
    console.print("[bold]Generation Plan:[/bold]")
    console.print(f"  Total dilemmas: [bold]{len(GENERATION_PLAN)}[/bold]")

    # Count by difficulty
    diff_counts = {}
    for item in GENERATION_PLAN:
        diff = item["difficulty"]
        diff_counts[diff] = diff_counts.get(diff, 0) + 1

    console.print("\n  [bold]Difficulty distribution:[/bold]")
    console.print(f"    Easy (1-3): {sum(diff_counts.get(d, 0) for d in [1, 2, 3])} dilemmas")
    console.print(f"    Medium (4-6): {sum(diff_counts.get(d, 0) for d in [4, 5, 6])} dilemmas")
    console.print(f"    Hard (7-9): {sum(diff_counts.get(d, 0) for d in [7, 8, 9])} dilemmas")
    console.print(f"    Extreme (10): {diff_counts.get(10, 0)} dilemmas")

    # Count by prompt
    prompt_counts = {}
    for item in GENERATION_PLAN:
        prompt = item["prompt"]
        prompt_counts[prompt] = prompt_counts.get(prompt, 0) + 1

    console.print("\n  [bold]Prompt distribution:[/bold]")
    for prompt, count in sorted(prompt_counts.items()):
        pct = count / len(GENERATION_PLAN) * 100
        console.print(f"    {prompt}: {count} ({pct:.0f}%)")

    console.print("\n  [bold]Quality settings:[/bold]")
    console.print(f"    ✅ Validation enabled (min_quality_score: {MIN_QUALITY_SCORE})")
    console.print("    ✅ Variable extraction enabled")
    console.print("    ✅ Diversity tracking enabled")

    console.print("\n  [bold]Models (top-tier only):[/bold]")
    for model in TOP_TIER_MODELS:
        console.print(f"    • {model}")

    console.print("\n  [bold]Collection:[/bold] bench-1")
    console.print()


async def generate_bench1() -> list[DilemmaDB]:
    """Generate bench-1 collection with validation and diversity tracking.

    Returns:
        List of saved DilemmaDB instances
    """
    config = get_config()
    db = get_database()
    batch_id = str(uuid.uuid4())
    collection = "bench-1"

    saved_dilemmas = []
    failed_dilemmas = []

    # Track diversity
    used_combos = set()

    # Use top-tier models only
    available_models = TOP_TIER_MODELS

    console.print(f"[dim]Batch ID: {batch_id[:8]}...[/dim]")
    console.print(f"[dim]Using top-tier models: {len(available_models)}[/dim]\n")

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
            prompt_version = plan_item["prompt"]

            # Randomly select model for diversity
            model = random.choice(available_models)

            # Update progress
            progress.update(
                overall_task,
                description=f"[cyan]Generating {i}/{len(GENERATION_PLAN)} (diff: {difficulty}, prompt: {prompt_version}, model: {model})",
            )

            # Create generator for this dilemma
            generator = DilemmaGenerator(
                model_id=model,
                prompt_version=prompt_version
            )

            # Try to ensure diversity
            max_retries = 5
            dilemma = None
            validation = None
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

                    # Generate with validation (using lower quality threshold)
                    dilemma, validation = await generator.generate_with_validation(
                        seed=seed,
                        max_attempts=3,
                        min_quality_score=MIN_QUALITY_SCORE,
                        enable_validation=config.generation.enable_validation,
                    )

                    # Check diversity
                    if dilemma.seed_components:
                        combo = (
                            dilemma.seed_components.get("domain"),
                            dilemma.seed_components.get("conflict"),
                        )
                        if combo in used_combos and attempt < max_retries - 1:
                            console.print(f"  [yellow]⚠[/yellow] Duplicate combo, retrying... (attempt {attempt + 1})")
                            continue  # Try again
                        used_combos.add(combo)

                    # Success!
                    break

                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        # All retries exhausted
                        error_msg = str(e)
                        if len(error_msg) > 100:
                            error_msg = error_msg[:100] + "..."

                        console.print(f"[yellow]⚠[/yellow] Skipped dilemma {i}/{len(GENERATION_PLAN)}: {error_msg}")
                        failed_dilemmas.append({
                            'index': i,
                            'difficulty': difficulty,
                            'prompt_version': prompt_version,
                            'model': model,
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

                # Print success with quality info
                quality_icons = []
                if dilemma.variables:
                    quality_icons.append(f"📊×{len(dilemma.variables)}")
                if dilemma.modifiers:
                    quality_icons.append(f"⚙️×{len(dilemma.modifiers)}")
                if dilemma.available_tools:
                    quality_icons.append(f"🔧×{len(dilemma.available_tools)}")

                quality_str = " ".join(quality_icons) if quality_icons else "[dim](no extras)[/dim]"

                # Show validation scores if available
                val_str = ""
                if validation:
                    val_str = f" [dim](quality: {validation.quality_score:.1f}/10, interest: {validation.interest_score:.1f}/10)[/dim]"

                console.print(
                    f"  [green]✓[/green] Generated: [bold]{dilemma.title}[/bold] "
                    f"(difficulty {dilemma.difficulty_intended}/10, ID: {dilemma.id[:8]}...) "
                    f"{quality_str}{val_str}"
                )
            except Exception as e:
                error_msg = str(e)[:100]
                console.print(f"[yellow]⚠[/yellow] Failed to save dilemma {i}/{len(GENERATION_PLAN)}: {error_msg}")
                failed_dilemmas.append({
                    'index': i,
                    'difficulty': difficulty,
                    'prompt_version': prompt_version,
                    'model': model,
                    'error': f"DB save error: {error_msg}"
                })

            # Update progress
            progress.update(overall_task, advance=1)

    await db.close()

    # Print failure summary if any
    if failed_dilemmas:
        console.print(f"\n[yellow]⚠ {len(failed_dilemmas)} dilemmas failed:[/yellow]")
        for failure in failed_dilemmas:
            console.print(
                f"  #{failure['index']}: {failure['model']} / {failure['prompt_version']} "
                f"(diff {failure['difficulty']}) - {failure['error']}"
            )

    return saved_dilemmas


def print_results(dilemmas: list[DilemmaDB]):
    """Print generation results summary."""
    console.print("\n" + "=" * 80)
    console.print("[bold green]✓ bench-1 Generation Complete![/bold green]")
    console.print("=" * 80)

    # Success stats
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Target: {len(GENERATION_PLAN)} dilemmas")
    console.print(f"  Generated: [green]{len(dilemmas)}[/green] dilemmas")
    if len(dilemmas) < len(GENERATION_PLAN):
        console.print(f"  Failed: [yellow]{len(GENERATION_PLAN) - len(dilemmas)}[/yellow]")
        console.print(f"  Success rate: [cyan]{len(dilemmas)/len(GENERATION_PLAN)*100:.1f}%[/cyan]")

    if len(dilemmas) == 0:
        console.print("\n[red]No dilemmas generated. Check errors above.[/red]")
        return

    # Quality stats
    quality_stats = {
        'has_variables': 0,
        'has_modifiers': 0,
        'has_tools': 0,
        'complete': 0,
    }

    total_chars = 0

    for db_dilemma in dilemmas:
        dilemma = db_dilemma.to_domain()
        if dilemma.variables:
            quality_stats['has_variables'] += 1
        if dilemma.modifiers:
            quality_stats['has_modifiers'] += 1
        if dilemma.available_tools:
            quality_stats['has_tools'] += 1
        if dilemma.variables and dilemma.modifiers and dilemma.available_tools:
            quality_stats['complete'] += 1
        total_chars += len(dilemma.situation_template)

    avg_chars = total_chars / len(dilemmas)

    console.print(f"\n[bold]Quality Stats:[/bold]")
    console.print(f"  Variables: [green]{quality_stats['has_variables']}/{len(dilemmas)}[/green] ({quality_stats['has_variables']/len(dilemmas)*100:.1f}%)")
    console.print(f"  Modifiers: [green]{quality_stats['has_modifiers']}/{len(dilemmas)}[/green] ({quality_stats['has_modifiers']/len(dilemmas)*100:.1f}%)")
    console.print(f"  Tools: [cyan]{quality_stats['has_tools']}/{len(dilemmas)}[/cyan] ({quality_stats['has_tools']/len(dilemmas)*100:.1f}%)")
    console.print(f"  Complete: [yellow]{quality_stats['complete']}/{len(dilemmas)}[/yellow] ({quality_stats['complete']/len(dilemmas)*100:.1f}%)")
    console.print(f"  Avg length: [cyan]{avg_chars:.0f} chars[/cyan]")

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
        console.print(f"  • {dilemma.title} (difficulty {dilemma.difficulty_intended}/10)")

    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  • View in browser: [cyan]uv run python scripts/serve.py[/cyan]")
    console.print("  • Explore database: [cyan]uv run python scripts/explore_db.py[/cyan]")
    console.print("  • Filter by collection: [cyan]SELECT * FROM dilemma WHERE collection = 'bench-1'[/cyan]")

    console.print("\n" + "=" * 80 + "\n")


async def main():
    """Main execution flow."""
    try:
        # Welcome
        print_welcome()

        # Show plan
        print_plan()

        # Skip confirmation when running in background
        # if not Confirm.ask("[yellow]Ready to generate bench-1 collection?[/yellow]", default=True):
        #     console.print("[yellow]Cancelled.[/yellow]")
        #     return 0

        console.print()

        # Generate
        saved_dilemmas = await generate_bench1()

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
