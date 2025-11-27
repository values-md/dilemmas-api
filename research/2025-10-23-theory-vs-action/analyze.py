"""Analyze Theory vs Action experiment results.

Questions:
1. Do choices differ between theory and action mode?
2. Does confidence differ?
3. Does perceived difficulty differ?
4. Is there a "theory-action gap"?
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import json
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()

# Load data from JSON (has mode field)
data_dir = Path(__file__).parent
with open(data_dir / "judgements.json") as f:
    judgements = json.load(f)

# Convert to DataFrame
df = pd.DataFrame([
    {
        "judgement_id": j["id"],
        "dilemma_title": j.get("dilemma_id", "unknown"),  # We'll map this
        "mode": j["mode"],
        "choice_id": j["choice_id"],
        "confidence": j["confidence"],
        "perceived_difficulty": j.get("perceived_difficulty"),
        "repetition_number": j.get("repetition_number", 1),
    }
    for j in judgements
])

# Load dilemmas to map IDs to titles
with open(data_dir / "dilemmas.json") as f:
    dilemmas = json.load(f)
    id_to_title = {d["id"]: d["title"] for d in dilemmas}

df["dilemma_title"] = df["dilemma_title"].map(id_to_title)

console.print("\n[bold cyan]Theory vs Action Mode Analysis[/bold cyan]\n")
console.print(f"Total judgements: {len(df)}")
console.print(f"Dilemmas: {df['dilemma_title'].nunique()}")
console.print(f"Modes: {df['mode'].nunique()}\n")

# ===== 1. CHOICE COMPARISON BY MODE =====
console.print("[bold]1. Do Choices Differ Between Modes?[/bold]\n")

for dilemma in df['dilemma_title'].unique():
    dilemma_df = df[df['dilemma_title'] == dilemma]

    console.print(f"[yellow]{dilemma}[/yellow]")

    # Theory mode choices
    theory_df = dilemma_df[dilemma_df['mode'] == 'theory']
    theory_choices = theory_df['choice_id'].value_counts()

    # Action mode choices
    action_df = dilemma_df[dilemma_df['mode'] == 'action']
    action_choices = action_df['choice_id'].value_counts()

    table = Table(show_header=True)
    table.add_column("Choice", style="cyan")
    table.add_column("Theory", style="blue", justify="right")
    table.add_column("Action", style="green", justify="right")
    table.add_column("Δ", style="yellow", justify="right")

    all_choices = set(theory_choices.index) | set(action_choices.index)
    for choice in sorted(all_choices):
        theory_count = theory_choices.get(choice, 0)
        action_count = action_choices.get(choice, 0)
        delta = action_count - theory_count

        delta_str = f"+{delta}" if delta > 0 else str(delta)
        if delta != 0:
            delta_str = f"[bold]{delta_str}[/bold]"

        table.add_row(
            choice,
            str(theory_count),
            str(action_count),
            delta_str
        )

    console.print(table)
    console.print()

# ===== 2. CONFIDENCE COMPARISON =====
console.print("\n[bold]2. Does Confidence Differ?[/bold]\n")

conf_table = Table(show_header=True, title="Confidence by Mode")
conf_table.add_column("Dilemma", style="cyan")
conf_table.add_column("Theory", style="blue", justify="right")
conf_table.add_column("Action", style="green", justify="right")
conf_table.add_column("Δ", style="yellow", justify="right")

for dilemma in df['dilemma_title'].unique():
    dilemma_df = df[df['dilemma_title'] == dilemma]

    theory_conf = dilemma_df[dilemma_df['mode'] == 'theory']['confidence'].mean()
    action_conf = dilemma_df[dilemma_df['mode'] == 'action']['confidence'].mean()
    delta = action_conf - theory_conf

    delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

    conf_table.add_row(
        dilemma[:40],
        f"{theory_conf:.2f}",
        f"{action_conf:.2f}",
        delta_str
    )

console.print(conf_table)

# Overall
theory_conf_overall = df[df['mode'] == 'theory']['confidence'].mean()
action_conf_overall = df[df['mode'] == 'action']['confidence'].mean()
console.print(f"\n[cyan]Overall:[/cyan]")
console.print(f"  Theory: {theory_conf_overall:.2f}")
console.print(f"  Action: {action_conf_overall:.2f}")
console.print(f"  Δ: {action_conf_overall - theory_conf_overall:+.2f}")

# ===== 3. DIFFICULTY COMPARISON =====
console.print("\n\n[bold]3. Does Perceived Difficulty Differ?[/bold]\n")

diff_table = Table(show_header=True, title="Perceived Difficulty by Mode")
diff_table.add_column("Dilemma", style="cyan")
diff_table.add_column("Theory", style="blue", justify="right")
diff_table.add_column("Action", style="green", justify="right")
diff_table.add_column("Δ", style="yellow", justify="right")

for dilemma in df['dilemma_title'].unique():
    dilemma_df = df[df['dilemma_title'] == dilemma]

    theory_diff = dilemma_df[dilemma_df['mode'] == 'theory']['perceived_difficulty'].mean()
    action_diff = dilemma_df[dilemma_df['mode'] == 'action']['perceived_difficulty'].mean()
    delta = action_diff - theory_diff

    delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

    diff_table.add_row(
        dilemma[:40],
        f"{theory_diff:.2f}",
        f"{action_diff:.2f}",
        delta_str
    )

console.print(diff_table)

# Overall
theory_diff_overall = df[df['mode'] == 'theory']['perceived_difficulty'].mean()
action_diff_overall = df[df['mode'] == 'action']['perceived_difficulty'].mean()
console.print(f"\n[cyan]Overall:[/cyan]")
console.print(f"  Theory: {theory_diff_overall:.2f}")
console.print(f"  Action: {action_diff_overall:.2f}")
console.print(f"  Δ: {action_diff_overall - theory_diff_overall:+.2f}")

# ===== 4. THEORY-ACTION GAP SUMMARY =====
console.print("\n\n[bold]4. Theory-Action Gap Summary[/bold]\n")

# Count how many dilemmas showed different choices
gap_dilemmas = []
for dilemma in df['dilemma_title'].unique():
    dilemma_df = df[df['dilemma_title'] == dilemma]

    theory_mode = dilemma_df[dilemma_df['mode'] == 'theory']['choice_id'].mode()
    action_mode_choices = dilemma_df[dilemma_df['mode'] == 'action']['choice_id'].mode()

    if len(theory_mode) > 0 and len(action_mode_choices) > 0:
        if theory_mode[0] != action_mode_choices[0]:
            gap_dilemmas.append(dilemma)

console.print(f"[yellow]Dilemmas with different modal choices:[/yellow] {len(gap_dilemmas)}/{df['dilemma_title'].nunique()}")
if gap_dilemmas:
    for d in gap_dilemmas:
        console.print(f"  - {d}")

console.print(f"\n[bold green]✓ Analysis complete![/bold green]")
console.print("\nNext: Write findings to findings.md")
