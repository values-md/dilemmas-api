"""Analyze Theory vs Action Part Two results.

Questions:
1. Is the difficulty drop universal across models?
2. What's the magnitude per model?
3. Which dilemmas show the biggest gaps?
4. Do reasoning models differ from standard models?
5. Does confidence correlate with difficulty?
"""

import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import json
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()

# Load data from JSON
data_dir = Path(__file__).parent
with open(data_dir / "judgements.json") as f:
    judgements = json.load(f)

# Convert to DataFrame
df = pd.DataFrame([
    {
        "judgement_id": j["id"],
        "dilemma_id": j.get("dilemma_id"),
        "model_id": j["ai_judge"]["model_id"],
        "mode": j["mode"],
        "choice_id": j["choice_id"],
        "confidence": j["confidence"],
        "perceived_difficulty": j.get("perceived_difficulty"),
        "repetition_number": j.get("repetition_number", 1),
    }
    for j in judgements
])

# Load dilemmas
with open(data_dir / "dilemmas.json") as f:
    dilemmas = json.load(f)
    id_to_title = {d["id"]: d["title"] for d in dilemmas}

df["dilemma_title"] = df["dilemma_id"].map(id_to_title)
df["model_short"] = df["model_id"].str.split("/").str[-1]

console.print("\n[bold cyan]Theory vs Action Part Two - Analysis[/bold cyan]\n")
console.print(f"Total judgements: {len(df)}")
console.print(f"Models: {df['model_id'].nunique()}")
console.print(f"Dilemmas: {df['dilemma_title'].nunique()}")
console.print(f"Modes: {df['mode'].nunique()}\n")

# ===== 1. DIFFICULTY DROP BY MODEL =====
console.print("[bold]1. Difficulty Drop by Model (PRIMARY FINDING)[/bold]\n")

diff_table = Table(show_header=True, title="Perceived Difficulty by Model & Mode")
diff_table.add_column("Model", style="cyan", width=25)
diff_table.add_column("Theory", style="blue", justify="right")
diff_table.add_column("Action", style="green", justify="right")
diff_table.add_column("Δ", style="yellow", justify="right")
diff_table.add_column("Effect", style="magenta")

for model in df['model_id'].unique():
    model_df = df[df['model_id'] == model]

    theory_diff = model_df[model_df['mode'] == 'theory']['perceived_difficulty'].mean()
    action_diff = model_df[model_df['mode'] == 'action']['perceived_difficulty'].mean()
    delta = action_diff - theory_diff

    # Classify effect size
    if abs(delta) < 0.5:
        effect = "None"
    elif abs(delta) < 1.0:
        effect = "Small"
    elif abs(delta) < 2.0:
        effect = "Medium"
    else:
        effect = "Large"

    delta_str = f"{delta:+.2f}"
    if delta < -0.5:
        delta_str = f"[bold]{delta_str}[/bold]"

    diff_table.add_row(
        model.split('/')[-1],
        f"{theory_diff:.2f}",
        f"{action_diff:.2f}",
        delta_str,
        effect
    )

console.print(diff_table)

# Overall
theory_diff_overall = df[df['mode'] == 'theory']['perceived_difficulty'].mean()
action_diff_overall = df[df['mode'] == 'action']['perceived_difficulty'].mean()
delta_overall = action_diff_overall - theory_diff_overall

console.print(f"\n[cyan]Overall across all models:[/cyan]")
console.print(f"  Theory: {theory_diff_overall:.2f}")
console.print(f"  Action: {action_diff_overall:.2f}")
console.print(f"  Δ: {delta_overall:+.2f}")

# ===== 2. CONFIDENCE BY MODEL =====
console.print("\n\n[bold]2. Confidence by Model[/bold]\n")

conf_table = Table(show_header=True, title="Confidence by Model & Mode")
conf_table.add_column("Model", style="cyan", width=25)
conf_table.add_column("Theory", style="blue", justify="right")
conf_table.add_column("Action", style="green", justify="right")
conf_table.add_column("Δ", style="yellow", justify="right")

for model in df['model_id'].unique():
    model_df = df[df['model_id'] == model]

    theory_conf = model_df[model_df['mode'] == 'theory']['confidence'].mean()
    action_conf = model_df[model_df['mode'] == 'action']['confidence'].mean()
    delta = action_conf - theory_conf

    delta_str = f"{delta:+.2f}"

    conf_table.add_row(
        model.split('/')[-1],
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

# ===== 3. DILEMMA-LEVEL GAPS =====
console.print("\n\n[bold]3. Which Dilemmas Show Biggest Theory-Action Gaps?[/bold]\n")

dilemma_gaps = []
for dilemma in df['dilemma_title'].unique():
    dilemma_df = df[df['dilemma_title'] == dilemma]

    theory_diff = dilemma_df[dilemma_df['mode'] == 'theory']['perceived_difficulty'].mean()
    action_diff = dilemma_df[dilemma_df['mode'] == 'action']['perceived_difficulty'].mean()
    delta = action_diff - theory_diff

    dilemma_gaps.append({
        'dilemma': dilemma,
        'theory': theory_diff,
        'action': action_diff,
        'delta': delta
    })

# Sort by absolute delta
dilemma_gaps.sort(key=lambda x: abs(x['delta']), reverse=True)

gap_table = Table(show_header=True, title="Dilemmas Ranked by Gap Size")
gap_table.add_column("Dilemma", style="cyan", width=40)
gap_table.add_column("Theory", style="blue", justify="right")
gap_table.add_column("Action", style="green", justify="right")
gap_table.add_column("Δ", style="yellow", justify="right")

for d in dilemma_gaps:
    delta_str = f"{d['delta']:+.2f}"
    if abs(d['delta']) > 2.0:
        delta_str = f"[bold]{delta_str}[/bold]"

    gap_table.add_row(
        d['dilemma'][:40],
        f"{d['theory']:.2f}",
        f"{d['action']:.2f}",
        delta_str
    )

console.print(gap_table)

# ===== 4. CHOICE REVERSALS =====
console.print("\n\n[bold]4. Choice Reversals Across All Models[/bold]\n")

reversals = []
for dilemma in df['dilemma_title'].unique():
    for model in df['model_id'].unique():
        subset = df[(df['dilemma_title'] == dilemma) & (df['model_id'] == model)]

        theory_mode_choice = subset[subset['mode'] == 'theory']['choice_id'].mode()
        action_mode_choice = subset[subset['mode'] == 'action']['choice_id'].mode()

        if len(theory_mode_choice) > 0 and len(action_mode_choice) > 0:
            if theory_mode_choice[0] != action_mode_choice[0]:
                reversals.append({
                    'model': model.split('/')[-1],
                    'dilemma': dilemma[:40],
                    'theory_choice': theory_mode_choice[0],
                    'action_choice': action_mode_choice[0]
                })

if reversals:
    console.print(f"[yellow]Found {len(reversals)} model-dilemma pairs with choice reversals:[/yellow]\n")
    for r in reversals[:10]:  # Show first 10
        console.print(f"  {r['model']:20} | {r['dilemma']:40} | {r['theory_choice']:15} → {r['action_choice']:15}")
else:
    console.print("[green]No choice reversals detected[/green]")

# ===== 5. MODEL CLUSTERING =====
console.print("\n\n[bold]5. Model Clustering by Behavior[/bold]\n")

# Group models by difficulty drop magnitude
small_drop = []
medium_drop = []
large_drop = []

for model in df['model_id'].unique():
    model_df = df[df['model_id'] == model]
    theory_diff = model_df[model_df['mode'] == 'theory']['perceived_difficulty'].mean()
    action_diff = model_df[model_df['mode'] == 'action']['perceived_difficulty'].mean()
    delta = action_diff - theory_diff

    if delta > -0.5:
        small_drop.append((model.split('/')[-1], delta))
    elif delta > -1.5:
        medium_drop.append((model.split('/')[-1], delta))
    else:
        large_drop.append((model.split('/')[-1], delta))

if large_drop:
    console.print(f"[red]Large difficulty drop[/red] (Δ < -1.5):")
    for m, d in large_drop:
        console.print(f"  - {m:25} ({d:+.2f})")

if medium_drop:
    console.print(f"\n[yellow]Medium difficulty drop[/yellow] (-1.5 ≤ Δ < -0.5):")
    for m, d in medium_drop:
        console.print(f"  - {m:25} ({d:+.2f})")

if small_drop:
    console.print(f"\n[green]Small/no difficulty drop[/green] (Δ ≥ -0.5):")
    for m, d in small_drop:
        console.print(f"  - {m:25} ({d:+.2f})")

console.print(f"\n[bold green]✓ Analysis complete![/bold green]")
console.print("\nNext: Write findings to findings.md")
