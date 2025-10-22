#!/usr/bin/env python3
"""Interactive batch dilemma generation with real-time progress.

This script provides a better UX for generating multiple dilemmas:
- Interactive input collection with multi-select
- Real-time progress display
- Incremental saving with visual feedback
- Random selection from chosen prompts/models

Usage:
    uv run python scripts/generate_batch_interactive.py
"""

import asyncio
import random
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from dilemmas.db.database import get_database
from dilemmas.models.config import get_config
from dilemmas.models.db import DilemmaDB
from dilemmas.services.generator import DilemmaGenerator

console = Console()


def print_welcome():
    """Print welcome banner."""
    welcome = Panel.fit(
        "[bold cyan]🎲 Interactive Dilemma Batch Generator[/bold cyan]\n"
        "Generate multiple ethical dilemmas with real-time progress tracking",
        border_style="cyan",
    )
    console.print(welcome)
    console.print()


def select_options(options: list[str], option_type: str) -> list[str]:
    """Let user select multiple options from a list.

    Args:
        options: List of available options
        option_type: Type of options (for display)

    Returns:
        List of selected options
    """
    console.print(f"\n[bold]Available {option_type}:[/bold]")

    # Create table showing options
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column(option_type.capitalize(), style="cyan")

    for i, option in enumerate(options, 1):
        table.add_row(str(i), option)

    console.print(table)

    # Get user selection
    console.print(f"\n[yellow]Enter numbers separated by commas (e.g., 1,3,5) or 'all' for all options:[/yellow]")
    selection = Prompt.ask("Your selection").strip().lower()

    if selection == "all":
        return options

    # Parse comma-separated numbers
    try:
        indices = [int(x.strip()) for x in selection.split(",")]
        selected = [options[i - 1] for i in indices if 1 <= i <= len(options)]

        if not selected:
            console.print("[red]No valid options selected. Using all options.[/red]")
            return options

        return selected
    except (ValueError, IndexError):
        console.print("[red]Invalid selection. Using all options.[/red]")
        return options


def get_user_inputs() -> tuple[int, list[str], list[str], tuple[int, int]]:
    """Collect generation parameters from user.

    Returns:
        (count, prompt_versions, models, difficulty_range)
    """
    config = get_config()

    # Number of dilemmas
    console.print("\n[bold]How many dilemmas do you want to generate?[/bold]")
    count = IntPrompt.ask("Count", default=10)

    # Select prompt versions
    prompt_versions = select_options(config.generation.prompt_versions, "prompt versions")

    # Select models
    models = select_options(config.generation.generator_models, "models")

    # Difficulty range
    console.print("\n[bold]Difficulty range (1-10):[/bold]")
    diff_min = IntPrompt.ask("Minimum difficulty", default=1)
    diff_max = IntPrompt.ask("Maximum difficulty", default=10)

    # Validate difficulty range
    diff_min = max(1, min(10, diff_min))
    diff_max = max(diff_min, min(10, diff_max))

    return count, prompt_versions, models, (diff_min, diff_max)


def print_summary(count: int, prompts: list[str], models: list[str], diff_range: tuple[int, int]):
    """Print generation summary."""
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]Generation Summary[/bold cyan]")
    console.print("=" * 80)
    console.print(f"  Dilemmas to generate: [bold]{count}[/bold]")
    console.print(f"  Prompt versions: [cyan]{', '.join(prompts)}[/cyan]")
    console.print(f"  Models: [green]{', '.join(models)}[/green]")
    console.print(f"  Difficulty range: [yellow]{diff_range[0]}-{diff_range[1]}[/yellow]")
    console.print(f"  Diversity: [magenta]Enabled[/magenta]")
    console.print("=" * 80 + "\n")


async def generate_and_save_incrementally(
    count: int,
    prompt_versions: list[str],
    models: list[str],
    difficulty_range: tuple[int, int],
) -> list[DilemmaDB]:
    """Generate dilemmas one by one with incremental saving and progress display.

    Args:
        count: Number of dilemmas to generate
        prompt_versions: List of prompt versions to randomly choose from
        models: List of models to randomly choose from
        difficulty_range: (min, max) difficulty range

    Returns:
        List of saved DilemmaDB instances
    """
    db = get_database()
    saved_dilemmas = []

    # Track used combinations for diversity
    used_combos = set()

    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        # Overall progress
        overall_task = progress.add_task("[cyan]Overall progress", total=count)

        for i in range(count):
            # Pick random difficulty, prompt, and model
            difficulty = random.randint(difficulty_range[0], difficulty_range[1])
            prompt_version = random.choice(prompt_versions)
            model = random.choice(models)

            # Update progress description
            progress.update(
                overall_task,
                description=f"[cyan]Generating {i+1}/{count} (model: {model}, prompt: {prompt_version}, difficulty: {difficulty})",
            )

            # Create generator for this dilemma
            generator = DilemmaGenerator(model_id=model, prompt_version=prompt_version)

            # Try to ensure diversity
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    dilemma = await generator.generate_random(difficulty=difficulty)

                    # Check diversity
                    if dilemma.seed_components:
                        combo = (
                            dilemma.seed_components.get("domain"),
                            dilemma.seed_components.get("conflict"),
                        )
                        if combo in used_combos and attempt < max_retries - 1:
                            continue  # Try again
                        used_combos.add(combo)

                    # Success!
                    break

                except Exception as e:
                    if attempt == max_retries - 1:
                        console.print(f"[red]Error generating dilemma {i+1}: {e}[/red]")
                        raise
                    continue

            # Save to database
            async for session in db.get_session():
                db_dilemma = DilemmaDB.from_domain(dilemma)
                session.add(db_dilemma)
                await session.commit()
                saved_dilemmas.append(db_dilemma)

            # Print success
            console.print(
                f"  [green]✓[/green] Generated: [bold]{dilemma.title}[/bold] "
                f"(difficulty {dilemma.difficulty_intended}/10, ID: {dilemma.id[:8]}...)"
            )

            # Update progress
            progress.update(overall_task, advance=1)

    await db.close()
    return saved_dilemmas


def print_results(dilemmas: list[DilemmaDB]):
    """Print generation results summary."""
    console.print("\n" + "=" * 80)
    console.print("[bold green]✓ Generation Complete![/bold green]")
    console.print("=" * 80)

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

    # Sample titles
    console.print("\n[bold]Sample Titles:[/bold]")
    for db_dilemma in dilemmas[:5]:
        dilemma = db_dilemma.to_domain()
        console.print(f"  • {dilemma.title} (difficulty {dilemma.difficulty_intended}/10)")

    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  • Explore database: [cyan]uv run python scripts/explore_db.py[/cyan]")
    console.print("  • View in browser: [cyan]http://localhost:8001/dilemmas/dilemmas[/cyan]")
    console.print("  • Test database: [cyan]uv run python scripts/test_db.py[/cyan]")

    console.print("\n" + "=" * 80 + "\n")


async def main():
    """Main interactive flow."""
    try:
        # Welcome
        print_welcome()

        # Get user inputs
        count, prompt_versions, models, difficulty_range = get_user_inputs()

        # Print summary
        print_summary(count, prompt_versions, models, difficulty_range)

        # Confirm
        console.print("[yellow]Ready to start generation?[/yellow]")
        confirm = Prompt.ask("Continue", choices=["y", "n"], default="y")

        if confirm.lower() != "y":
            console.print("[yellow]Cancelled.[/yellow]")
            return 0

        console.print()

        # Generate and save
        saved_dilemmas = await generate_and_save_incrementally(
            count=count,
            prompt_versions=prompt_versions,
            models=models,
            difficulty_range=difficulty_range,
        )

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
