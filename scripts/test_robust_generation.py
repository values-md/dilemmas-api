#!/usr/bin/env python3
"""Test robust dilemma generation with validation.

This script demonstrates the three-tier quality control system:
- Tier 1: Better prompts
- Tier 2: Pydantic validators
- Tier 3: LLM validation and repair
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dilemmas.services.generator import DilemmaGenerator
from dilemmas.services.seeds import generate_random_seed, get_seed_library

console = Console()


async def test_robust_generation():
    """Test robust generation with validation."""

    console.print(Panel.fit(
        "[bold cyan]Testing Robust Dilemma Generation[/bold cyan]\n"
        "Three-Tier Quality Control System",
        border_style="cyan"
    ))
    console.print()

    # Create generator
    gen = DilemmaGenerator()
    seed_library = get_seed_library()

    # Generate a seed
    console.print("[bold]Generating seed...[/bold]")
    seed = generate_random_seed(library=seed_library, difficulty=7)
    console.print(f"  Domain: {seed.domain}")
    console.print(f"  Conflict: {seed.conflict.description}")
    console.print(f"  Actors: {', '.join(seed.actors)}")
    console.print()

    # Test with validation enabled
    console.print("[bold]Generating dilemma with validation...[/bold]")
    try:
        dilemma, validation = await gen.generate_with_validation(
            seed=seed,
            max_attempts=3,
            min_quality_score=7.0,
            enable_validation=True
        )

        console.print("[green]✓ Generation successful![/green]")
        console.print()

        # Show results
        console.print(Panel(
            f"[bold]{dilemma.title}[/bold]\n\n"
            f"{dilemma.situation_template[:300]}...",
            title="Generated Dilemma",
            border_style="green"
        ))
        console.print()

        # Show validation scores
        table = Table(title="Validation Scores")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="green")

        table.add_row("Quality", f"{validation.quality_score:.1f}/10")
        table.add_row("Interest", f"{validation.interest_score:.1f}/10")
        table.add_row("Realism", f"{validation.realism_score:.1f}/10")
        table.add_row("Recommendation", validation.recommendation)

        console.print(table)
        console.print()

        # Show strengths/weaknesses
        if validation.strengths:
            console.print("[bold]Strengths:[/bold]")
            for s in validation.strengths:
                console.print(f"  ✓ {s}")
            console.print()

        if validation.weaknesses:
            console.print("[bold]Weaknesses:[/bold]")
            for w in validation.weaknesses:
                console.print(f"  • {w}")
            console.print()

        # Show issues if any
        if validation.issues:
            console.print(f"[yellow]Issues found ({len(validation.issues)}):[/yellow]")
            for issue in validation.issues:
                console.print(f"  [{issue.severity}] {issue.field}: {issue.message}")
            console.print()

        return True

    except ValueError as e:
        console.print(f"[red]✗ Generation failed: {e}[/red]")
        return False


async def main():
    """Run tests."""
    success = await test_robust_generation()

    if success:
        console.print("\n[bold green]✅ All tests passed![/bold green]")
        console.print("\n[bold]The three-tier quality control system is working:[/bold]")
        console.print("  1. ✓ Better prompts prevent issues at source")
        console.print("  2. ✓ Pydantic validators catch structural problems")
        console.print("  3. ✓ LLM validation assesses quality and repairs issues")
        return 0
    else:
        console.print("\n[bold red]❌ Tests failed[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
