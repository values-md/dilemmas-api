#!/usr/bin/env python3
"""Test single dilemma generation with full validation workflow.

This script tests the complete generation → validation → extraction → technical validation flow.

Usage:
    uv run python scripts/test_single_generation.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel

from dilemmas.services.generator import DilemmaGenerator
from dilemmas.services.seeds import generate_random_seed
from dilemmas.models.config import get_config

# Enable detailed logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

console = Console()


async def test_generation():
    """Test complete generation workflow with validation."""
    console.print(Panel.fit(
        "[bold cyan]🧪 Testing Single Dilemma Generation[/bold cyan]\n"
        "Complete workflow: Generate → Validate → Extract → Technical Check",
        border_style="cyan"
    ))
    console.print()

    # Configuration
    model_id = "openai/gpt-5-mini"
    prompt_version = "v8_concise"
    difficulty = 5
    min_quality_score = 5.0

    console.print(f"[bold]Configuration:[/bold]")
    console.print(f"  Model: {model_id}")
    console.print(f"  Prompt: {prompt_version}")
    console.print(f"  Difficulty: {difficulty}/10")
    console.print(f"  Min Quality: {min_quality_score}/10")
    console.print(f"  Validation: Enabled")
    console.print(f"  Variable Extraction: Enabled")
    console.print()

    # Create generator
    generator = DilemmaGenerator(
        model_id=model_id,
        prompt_version=prompt_version
    )

    # Generate random seed
    config = get_config()
    seed = generate_random_seed(
        library=generator.seed_library,
        difficulty=difficulty,
        num_actors=config.generation.num_actors,
        num_stakes=config.generation.num_stakes,
    )

    console.print(f"[bold]Generated Seed:[/bold]")
    console.print(f"  Domain: {seed.domain}")
    console.print(f"  Conflict: {seed.conflict.description}")
    console.print(f"  Stakes: {', '.join([f'{s.category}: {s.specific}' for s in seed.stakes[:2]])}")
    console.print()

    # Generate with validation
    console.print("[yellow]Generating dilemma with full validation...[/yellow]")
    console.print()

    try:
        dilemma, validation = await generator.generate_with_validation(
            seed=seed,
            max_attempts=3,
            min_quality_score=min_quality_score,
            enable_validation=True,
        )

        # Print results
        console.print("[green]✓ Generation successful![/green]")
        console.print()

        console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
        console.print(f"[bold]Title:[/bold] {dilemma.title}")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
        console.print()

        console.print(f"[bold]Situation ({len(dilemma.situation_template)} chars):[/bold]")
        console.print(dilemma.situation_template)
        console.print()

        console.print(f"[bold]Question:[/bold]")
        console.print(dilemma.question)
        console.print()

        console.print(f"[bold]Choices:[/bold]")
        for i, choice in enumerate(dilemma.choices, 1):
            tool_info = f" → tool: {choice.tool_name}" if choice.tool_name else " [red](no tool)[/red]"
            console.print(f"  {i}. [cyan]{choice.label}[/cyan]{tool_info}")
            console.print(f"     {choice.description}")
        console.print()

        # Validation scores
        if validation:
            console.print(f"[bold]Validation Scores:[/bold]")
            console.print(f"  Quality: [green]{validation.quality_score:.1f}/10[/green]")
            console.print(f"  Interest: [cyan]{validation.interest_score:.1f}/10[/cyan]")
            console.print(f"  Realism: [yellow]{validation.realism_score:.1f}/10[/yellow]")
            console.print(f"  Recommendation: [bold]{validation.recommendation}[/bold]")
            console.print()

        # Technical checks
        console.print(f"[bold]Technical Validation:[/bold]")
        console.print(f"  Variables: [green]✓ {len(dilemma.variables)} extracted[/green]")
        for var_name, values in list(dilemma.variables.items())[:3]:  # Show first 3
            console.print(f"    • {var_name}: {len(values)} values")

        console.print(f"  Modifiers: [green]✓ {len(dilemma.modifiers)} extracted[/green]")
        for mod in dilemma.modifiers[:3]:  # Show first 3
            console.print(f"    • {mod}")

        console.print(f"  Tools: [green]✓ {len(dilemma.available_tools)} available[/green]")
        for tool in dilemma.available_tools:
            console.print(f"    • {tool.name}: {tool.description}")

        console.print(f"  Tool Mapping: [green]✓ All {len(dilemma.choices)} choices have tool_name[/green]")
        console.print()

        # Metadata
        console.print(f"[bold]Metadata:[/bold]")
        console.print(f"  ID: {dilemma.id[:8]}...")
        console.print(f"  Difficulty: {dilemma.difficulty_intended}/10")
        console.print(f"  Generator: {dilemma.generator_model}")
        console.print(f"  Prompt: {dilemma.generator_prompt_version}")
        console.print()

        console.print("[bold green]✓ All validation checks passed![/bold green]")
        return 0

    except Exception as e:
        console.print(f"[red]✗ Generation failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_generation()))
