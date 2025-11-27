#!/usr/bin/env python3
"""Test a single dilemma in both theory and action mode.

This validates the full v2 methodology pipeline:
- Theory mode: free-form response → parsed by gpt-4.1-mini
- Action mode: single tool call with reasoning+confidence params

Usage:
    uv run python scripts/test_single_dilemma.py
"""

import asyncio
import json
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dilemmas.models.dilemma import Dilemma
from dilemmas.services.judge import DilemmaJudge

console = Console()

# Test config
TEST_MODEL = "anthropic/claude-sonnet-4.5"
DILEMMA_FILE = "research/2025-11-27-when-agents-act/bench2_final.json"
DILEMMA_INDEX = 0  # Which dilemma to test (0-9)


async def load_dilemma(index: int = 0) -> Dilemma:
    """Load a dilemma from bench2_final.json."""
    file_path = os.path.join(os.path.dirname(__file__), "..", DILEMMA_FILE)

    with open(file_path) as f:
        data = json.load(f)

    # JSON is a direct list of dilemmas
    dilemmas_data = data if isinstance(data, list) else data.get("dilemmas", [])
    if index >= len(dilemmas_data):
        raise ValueError(f"Dilemma index {index} out of range (max {len(dilemmas_data)-1})")

    return Dilemma(**dilemmas_data[index])


async def test_theory_mode(judge: DilemmaJudge, dilemma: Dilemma):
    """Test theory mode (v2 - free-form + parsing)."""
    console.print("\n" + "=" * 70)
    console.print("[bold blue]THEORY MODE (v2 - free-form + parsing)[/bold blue]")
    console.print("=" * 70)

    # Use first variable value
    variable_values = None
    if dilemma.variables:
        # Variables is dict[str, list[str]]
        variable_values = {
            placeholder: values[0]
            for placeholder, values in dilemma.variables.items()
        }
        console.print(f"\n[dim]Variables: {variable_values}[/dim]")

    console.print(f"\n[dim]Model: {TEST_MODEL}[/dim]")
    console.print("[dim]Methodology: v2_freeform (free-form → parsed)[/dim]")
    console.print("\n[yellow]Running...[/yellow]")

    judgement = await judge.judge_dilemma(
        dilemma=dilemma,
        model_id=TEST_MODEL,
        temperature=1.0,
        mode="theory",
        methodology="v2_freeform",
        variable_values=variable_values,
    )

    # Display results
    console.print("\n[bold green]Results:[/bold green]")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Choice ID", judgement.choice_id or "(none)")
    table.add_row("Confidence", f"{judgement.confidence:.1f}/10" if judgement.confidence else "(none)")
    table.add_row("Response Time", f"{judgement.response_time_ms}ms")

    console.print(table)

    console.print("\n[bold]Reasoning (parsed):[/bold]")
    console.print(Panel(judgement.reasoning, border_style="green"))

    if judgement.reasoning_trace:
        console.print("\n[bold]Raw Response (before parsing):[/bold]")
        # Truncate if too long
        raw = judgement.reasoning_trace
        if len(raw) > 1000:
            raw = raw[:1000] + f"\n... ({len(judgement.reasoning_trace)} chars total)"
        console.print(Panel(raw, border_style="dim"))

    return judgement


async def test_action_mode(judge: DilemmaJudge, dilemma: Dilemma):
    """Test action mode (v2 - single tool call)."""
    console.print("\n" + "=" * 70)
    console.print("[bold magenta]ACTION MODE (v2 - single tool call)[/bold magenta]")
    console.print("=" * 70)

    # Use first variable value
    variable_values = None
    if dilemma.variables:
        # Variables is dict[str, list[str]]
        variable_values = {
            placeholder: values[0]
            for placeholder, values in dilemma.variables.items()
        }
        console.print(f"\n[dim]Variables: {variable_values}[/dim]")

    console.print(f"\n[dim]Model: {TEST_MODEL}[/dim]")
    console.print("[dim]Methodology: v2_freeform (single tool call with params)[/dim]")

    # Show available tools
    if dilemma.available_tools:
        console.print(f"\n[dim]Available tools: {[t.name for t in dilemma.available_tools]}[/dim]")

    console.print("\n[yellow]Running...[/yellow]")

    judgement = await judge.judge_dilemma(
        dilemma=dilemma,
        model_id=TEST_MODEL,
        temperature=1.0,
        mode="action",
        methodology="v2_freeform",
        variable_values=variable_values,
    )

    # Display results
    console.print("\n[bold green]Results:[/bold green]")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Choice ID", judgement.choice_id or "(none)")
    table.add_row("Confidence", f"{judgement.confidence:.1f}/10" if judgement.confidence else "(none)")
    table.add_row("Response Time", f"{judgement.response_time_ms}ms")

    console.print(table)

    console.print("\n[bold]Reasoning (from tool params):[/bold]")
    console.print(Panel(judgement.reasoning, border_style="magenta"))

    # Show tool call details
    if judgement.ai_judge and judgement.ai_judge.tool_calls:
        console.print("\n[bold]Tool Call:[/bold]")
        for tc in judgement.ai_judge.tool_calls:
            console.print(f"  Tool: [cyan]{tc.tool_name}[/cyan]")
            console.print(f"  Parameters: {tc.parameters}")

    return judgement


async def main():
    """Run the full test."""
    console.print(Panel.fit(
        "[bold]Single Dilemma Test - Theory vs Action Mode[/bold]\n"
        f"Model: {TEST_MODEL}\n"
        f"Methodology: v2_freeform",
        border_style="blue"
    ))

    # Load dilemma
    console.print(f"\n[dim]Loading dilemma {DILEMMA_INDEX} from {DILEMMA_FILE}...[/dim]")
    dilemma = await load_dilemma(DILEMMA_INDEX)

    console.print(f"\n[bold]Dilemma: {dilemma.title}[/bold]")
    console.print(f"[dim]ID: {dilemma.id}[/dim]")
    console.print(f"[dim]Choices: {[c.id for c in dilemma.choices]}[/dim]")

    # Show situation preview
    situation_preview = dilemma.situation_template[:200]
    if len(dilemma.situation_template) > 200:
        situation_preview += "..."
    console.print(f"\n[dim]Situation: {situation_preview}[/dim]")

    # Initialize judge
    judge = DilemmaJudge()

    # Run theory mode
    theory_result = await test_theory_mode(judge, dilemma)

    # Run action mode
    action_result = await test_action_mode(judge, dilemma)

    # Comparison
    console.print("\n" + "=" * 70)
    console.print("[bold yellow]COMPARISON[/bold yellow]")
    console.print("=" * 70)

    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Theory Mode", style="blue")
    table.add_column("Action Mode", style="magenta")

    table.add_row(
        "Choice",
        theory_result.choice_id or "(none)",
        action_result.choice_id or "(none)"
    )
    table.add_row(
        "Confidence",
        f"{theory_result.confidence:.1f}" if theory_result.confidence else "-",
        f"{action_result.confidence:.1f}" if action_result.confidence else "-"
    )
    table.add_row(
        "Response Time",
        f"{theory_result.response_time_ms}ms",
        f"{action_result.response_time_ms}ms"
    )

    same_choice = theory_result.choice_id == action_result.choice_id
    table.add_row(
        "Same Choice?",
        "[green]✓[/green]" if same_choice else "[red]✗[/red]",
        "[green]✓[/green]" if same_choice else "[red]✗[/red]"
    )

    console.print(table)

    if not same_choice:
        console.print("\n[bold red]⚠ JUDGMENT-ACTION GAP DETECTED![/bold red]")
        console.print(f"Theory chose: [blue]{theory_result.choice_id}[/blue]")
        console.print(f"Action chose: [magenta]{action_result.choice_id}[/magenta]")


if __name__ == "__main__":
    # Load environment
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    asyncio.run(main())
