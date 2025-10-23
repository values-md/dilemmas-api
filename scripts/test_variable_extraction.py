#!/usr/bin/env python3
"""Test variable extraction with different models to debug issues.

This script generates a simple dilemma and tests variable extraction
with different LLMs to see which ones work best.
"""

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dilemmas.services.generator import DilemmaGenerator
from dilemmas.services.seeds import generate_random_seed, get_seed_library

console = Console()


async def test_extraction_model(model_id: str, dilemma_title: str, situation: str):
    """Test variable extraction with a specific model."""

    console.print(f"\n[bold cyan]Testing: {model_id}[/bold cyan]")

    # Create a simple test dilemma
    from dilemmas.models.dilemma import Dilemma, DilemmaChoice

    test_dilemma = Dilemma(
        title=dilemma_title,
        situation_template=situation,
        question="What should you do?",
        choices=[
            DilemmaChoice(id="a", label="Option A", description="Do A"),
            DilemmaChoice(id="b", label="Option B", description="Do B"),
        ],
        action_context="You are an AI system.",
        difficulty_intended=5,
    )

    # Run extraction
    gen = DilemmaGenerator()
    try:
        result = await gen.variablize_dilemma(test_dilemma, model_id=model_id)

        # Analyze results
        placeholders = set(re.findall(r"\{([A-Z_]+)\}", result.situation_template))
        has_values = set(key.strip("{}") for key in result.variables.keys()) if result.variables else set()
        missing = placeholders - has_values

        # Display results
        table = Table(title=f"Results for {model_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Placeholders in situation", str(len(placeholders)))
        table.add_row("Variables with values", str(len(has_values)))
        table.add_row("Missing values", str(len(missing)))
        table.add_row("Modifiers", str(len(result.modifiers)))
        table.add_row("Status", "✓ Complete" if not missing else f"⚠️  Incomplete ({len(missing)} missing)")

        console.print(table)

        if missing:
            console.print(f"[yellow]Missing placeholders:[/yellow] {sorted(missing)}")

        if placeholders:
            console.print(f"\n[dim]Placeholders found:[/dim] {sorted(placeholders)}")

        if has_values:
            console.print(f"[dim]Variables with values:[/dim] {sorted(has_values)}")

        # Show first 200 chars of rewritten situation
        if result.situation_template != situation:
            console.print(f"\n[dim]Rewritten situation (first 200 chars):[/dim]")
            console.print(f"  {result.situation_template[:200]}...")

        return not missing  # True if successful

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


async def main():
    """Test variable extraction with multiple models."""

    console.print(Panel.fit(
        "[bold cyan]Variable Extraction Model Comparison[/bold cyan]\n"
        "Testing different LLMs to find best extraction performance",
        border_style="cyan"
    ))

    # Generate a test dilemma
    console.print("\n[bold]Generating test dilemma...[/bold]")
    gen = DilemmaGenerator()
    seed_library = get_seed_library()
    seed = generate_random_seed(library=seed_library, difficulty=5)

    dilemma = await gen.generate_from_seed(seed)

    console.print(f"  Title: {dilemma.title}")
    console.print(f"  Situation length: {len(dilemma.situation_template)} chars")
    console.print(f"  First 200 chars: {dilemma.situation_template[:200]}...")

    # Models to test
    models_to_test = [
        "moonshotai/kimi-k2-0905",  # Current default
        "google/gemini-2.5-flash",  # Good at structured output
        "anthropic/claude-sonnet-4.5",  # High quality reasoning
        "openai/gpt-4.1-mini",  # Fast and capable
    ]

    console.print(f"\n[bold]Testing {len(models_to_test)} models:[/bold]")

    results = {}
    for model_id in models_to_test:
        success = await test_extraction_model(model_id, dilemma.title, dilemma.situation_template)
        results[model_id] = success

    # Summary
    console.print("\n" + "="*80)
    console.print("[bold]Summary[/bold]")
    console.print("="*80)

    summary_table = Table()
    summary_table.add_column("Model", style="cyan")
    summary_table.add_column("Status", style="green")

    for model_id, success in results.items():
        model_name = model_id.split("/")[1]
        status = "✓ Complete" if success else "⚠️  Incomplete"
        summary_table.add_row(model_name, status)

    console.print(summary_table)

    # Recommendation
    successful_models = [m for m, s in results.items() if s]
    if successful_models:
        console.print(f"\n[bold green]✓ {len(successful_models)} model(s) worked successfully:[/bold green]")
        for model in successful_models:
            console.print(f"  • {model}")
    else:
        console.print("\n[bold red]✗ No models completed extraction successfully[/bold red]")
        console.print("\n[yellow]This suggests an issue with the extraction prompt or model instructions.[/yellow]")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
