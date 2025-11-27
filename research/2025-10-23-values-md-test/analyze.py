"""Analyze VALUES.md experiment results.

Questions we want to answer:
1. Do different VALUES.md files lead to different choices?
2. Does style (formal vs personal) matter?
3. Does ethical framework (utilitarian vs deontological) matter?
4. How consistent are decisions within each condition?
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()

# Load the data from current experiment directory
data_dir = Path(__file__).parent
df = pd.read_csv(data_dir / "raw_judgements.csv")

# Load full judgements to get values_file_name
import json
judgements_path = data_dir / "judgements.json"
with open(judgements_path) as f:
    judgements = json.load(f)

# Create mapping of judgement_id to values_file_name
id_to_condition = {}
for j in judgements:
    if j.get('experiment_id') == '54998c5e-5eae-4202-b3f3-3a94df407e82':
        values_file = j.get('ai_judge', {}).get('values_file_name')
        condition = values_file if values_file else "control"
        id_to_condition[j['id']] = condition

# Add condition column to dataframe
df['condition'] = df['judgement_id'].map(id_to_condition)

console.print("\n[bold cyan]VALUES.md Impact Analysis[/bold cyan]\n")

# ===== 1. CHOICE DISTRIBUTION BY CONDITION =====
console.print("[bold]1. Choice Distribution by Condition[/bold]")
console.print("Does VALUES.md content change which choices are selected?\n")

for dilemma_title in df['dilemma_title'].unique():
    dilemma_df = df[df['dilemma_title'] == dilemma_title]

    console.print(f"[yellow]{dilemma_title}[/yellow]")

    table = Table(show_header=True)
    table.add_column("Condition", style="cyan")
    table.add_column("Most Common Choice", style="green")
    table.add_column("Frequency", style="yellow", justify="right")
    table.add_column("Consistency %", style="magenta", justify="right")

    for condition in ['control', 'utilitarian-formal.md', 'utilitarian-personal.md',
                       'deontological-formal.md', 'deontological-personal.md']:
        cond_df = dilemma_df[dilemma_df['condition'] == condition]
        if len(cond_df) == 0:
            continue

        choices = cond_df['choice_id'].value_counts()
        most_common = choices.index[0]
        count = choices.iloc[0]
        total = len(cond_df)
        consistency_pct = (count / total) * 100

        condition_name = condition.replace('.md', '').replace('-', ' ').title() if condition != 'control' else 'Control'
        table.add_row(
            condition_name,
            most_common,
            f"{count}/{total}",
            f"{consistency_pct:.1f}%"
        )

    console.print(table)
    console.print()

# ===== 2. CROSS-CONDITION COMPARISON =====
console.print("\n[bold]2. Overall Condition Summary[/bold]\n")

summary_table = Table(show_header=True, title="Condition Performance")
summary_table.add_column("Condition", style="cyan")
summary_table.add_column("Avg Confidence", style="yellow", justify="right")
summary_table.add_column("Avg Consistency", style="green", justify="right")
summary_table.add_column("Unique Choices", style="magenta", justify="right")

for condition in ['control', 'utilitarian-formal.md', 'utilitarian-personal.md',
                   'deontological-formal.md', 'deontological-personal.md']:
    cond_df = df[df['condition'] == condition]
    if len(cond_df) == 0:
        continue

    avg_confidence = cond_df['confidence'].mean()

    # Calculate average consistency across dilemmas
    consistencies = []
    for dilemma_title in cond_df['dilemma_title'].unique():
        dilemma_cond_df = cond_df[cond_df['dilemma_title'] == dilemma_title]
        choices = dilemma_cond_df['choice_id'].value_counts()
        consistency = (choices.iloc[0] / len(dilemma_cond_df)) * 100
        consistencies.append(consistency)
    avg_consistency = sum(consistencies) / len(consistencies)

    # Count unique choices made
    unique_choices = len(cond_df['choice_id'].unique())

    condition_name = condition.replace('.md', '').replace('-', ' ').title() if condition != 'control' else 'Control'
    summary_table.add_row(
        condition_name,
        f"{avg_confidence:.2f}",
        f"{avg_consistency:.1f}%",
        str(unique_choices)
    )

console.print(summary_table)

# ===== 3. FRAMEWORK COMPARISON =====
console.print("\n[bold]3. Framework Comparison (Utilitarian vs Deontological)[/bold]\n")

util_df = df[df['condition'].str.contains('utilitarian', na=False)]
deon_df = df[df['condition'].str.contains('deontological', na=False)]

framework_table = Table(show_header=True)
framework_table.add_column("Framework", style="cyan")
framework_table.add_column("Avg Confidence", style="yellow")
framework_table.add_column("Avg Consistency", style="green")
framework_table.add_column("Sample Size", style="white")

for name, framework_df in [("Utilitarian", util_df), ("Deontological", deon_df)]:
    if len(framework_df) == 0:
        continue

    avg_conf = framework_df['confidence'].mean()

    consistencies = []
    for dilemma_title in framework_df['dilemma_title'].unique():
        dilemma_df = framework_df[framework_df['dilemma_title'] == dilemma_title]
        choices = dilemma_df['choice_id'].value_counts()
        consistency = (choices.iloc[0] / len(dilemma_df)) * 100
        consistencies.append(consistency)
    avg_consistency = sum(consistencies) / len(consistencies)

    framework_table.add_row(
        name,
        f"{avg_conf:.2f}",
        f"{avg_consistency:.1f}%",
        str(len(framework_df))
    )

console.print(framework_table)

# ===== 4. STYLE COMPARISON =====
console.print("\n[bold]4. Style Comparison (Formal vs Personal)[/bold]\n")

formal_df = df[df['condition'].str.contains('formal', na=False)]
personal_df = df[df['condition'].str.contains('personal', na=False)]

style_table = Table(show_header=True)
style_table.add_column("Style", style="cyan")
style_table.add_column("Avg Confidence", style="yellow")
style_table.add_column("Avg Consistency", style="green")
style_table.add_column("Sample Size", style="white")

for name, style_df in [("Formal", formal_df), ("Personal", personal_df)]:
    if len(style_df) == 0:
        continue

    avg_conf = style_df['confidence'].mean()

    consistencies = []
    for dilemma_title in style_df['dilemma_title'].unique():
        dilemma_df = style_df[style_df['dilemma_title'] == dilemma_title]
        choices = dilemma_df['choice_id'].value_counts()
        consistency = (choices.iloc[0] / len(dilemma_df)) * 100
        consistencies.append(consistency)
    avg_consistency = sum(consistencies) / len(consistencies)

    style_table.add_row(
        name,
        f"{avg_conf:.2f}",
        f"{avg_consistency:.1f}%",
        str(len(style_df))
    )

console.print(style_table)

console.print("\n[bold green]Analysis complete![/bold green]")
console.print("Next: Review findings and update research/2025-10-23-values-md-test/findings.md")
