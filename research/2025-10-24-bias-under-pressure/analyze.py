#!/usr/bin/env python3
"""Analyze Bias Under Pressure experiment results.

This script computes statistics and presents data.
Interpretation and findings should be written separately.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()

# Load the data from current experiment directory
data_dir = Path(__file__).parent / "data"
df = pd.read_csv(data_dir / "raw_judgements.csv")

# Load full judgements to get metadata
import json
judgements_path = Path(__file__).parent / "judgements.json"
with open(judgements_path) as f:
    judgements = json.load(f)

# Parse metadata - NEW STRUCTURED APPROACH
id_to_metadata = {}
for j in judgements:
    # Try new structured format first
    if 'experiment_metadata' in j and j['experiment_metadata']:
        metadata = j['experiment_metadata']
        id_to_metadata[j['id']] = {
            'condition': metadata.get('condition'),
            'demographic_variation': metadata.get('demographic_variation'),
            'ethnicity': metadata.get('ethnicity'),
            'gender': metadata.get('gender'),
            'name_used': metadata.get('name_used'),
            'name_variable': metadata.get('name_variable'),
        }
    # Fall back to parsing notes (backwards compatibility)
    elif 'notes' in j and 'bias_pressure' in j.get('notes', ''):
        parts = j['notes'].split('|')
        metadata_dict = {}
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                metadata_dict[key] = value

        id_to_metadata[j['id']] = {
            'condition': metadata_dict.get('condition'),
            'demographic_variation': metadata_dict.get('variation'),
            'ethnicity': None,  # Not available in old format
            'gender': None,  # Not available in old format
            'name_used': metadata_dict.get('name'),
            'name_variable': metadata_dict.get('name_var'),
        }

# Add metadata columns to dataframe
df['condition'] = df['judgement_id'].map(lambda x: id_to_metadata.get(x, {}).get('condition'))
df['demographic_variation'] = df['judgement_id'].map(lambda x: id_to_metadata.get(x, {}).get('demographic_variation'))
df['ethnicity'] = df['judgement_id'].map(lambda x: id_to_metadata.get(x, {}).get('ethnicity'))
df['gender'] = df['judgement_id'].map(lambda x: id_to_metadata.get(x, {}).get('gender'))
df['name_used'] = df['judgement_id'].map(lambda x: id_to_metadata.get(x, {}).get('name_used'))

console.print("\n[bold cyan]Bias Under Pressure - Data Analysis[/bold cyan]\n")

# ===== 1. SAMPLE SUMMARY =====
console.print("[bold]1. Sample Summary (2×2 Design)[/bold]\n")

summary_table = Table(show_header=True)
summary_table.add_column("Condition", style="cyan")
summary_table.add_column("Demographic", style="yellow")
summary_table.add_column("Count", style="white", justify="right")

for condition in ['baseline', 'time_pressure', 'high_stakes', 'combined']:
    for demo in ['euro_female', 'euro_male', 'non_euro_female', 'non_euro_male']:
        subset = df[(df['condition'] == condition) & (df['demographic_variation'] == demo)]
        summary_table.add_row(condition, demo, str(len(subset)))

console.print(summary_table)
console.print()

# ===== 2. BIAS DETECTION =====
console.print("\n[bold]2. Choice Patterns by Demographic (All 4 Variations)[/bold]\n")

choice_table = Table(show_header=True)
choice_table.add_column("Dilemma", style="cyan", max_width=25)
choice_table.add_column("Condition", style="white", max_width=10)
choice_table.add_column("EF", style="yellow", max_width=15)  # Euro Female
choice_table.add_column("EM", style="blue", max_width=15)   # Euro Male
choice_table.add_column("NF", style="green", max_width=15)  # Non-Euro Female
choice_table.add_column("NM", style="magenta", max_width=15) # Non-Euro Male
choice_table.add_column("All Same?", style="white")

for dilemma_title in sorted(df['dilemma_title'].unique()):
    for condition in ['baseline', 'time_pressure', 'high_stakes', 'combined']:
        dilemma_df = df[(df['dilemma_title'] == dilemma_title) & (df['condition'] == condition)]

        if len(dilemma_df) == 0:
            continue

        # Get modal choice for each demographic
        choices = {}
        for demo in ['euro_female', 'euro_male', 'non_euro_female', 'non_euro_male']:
            demo_choices = dilemma_df[dilemma_df['demographic_variation'] == demo]['choice_id']
            if len(demo_choices) > 0:
                choices[demo] = demo_choices.mode()[0] if len(demo_choices.mode()) > 0 else demo_choices.iloc[0]
            else:
                choices[demo] = "N/A"

        # Check if all choices are the same
        unique_choices = set([c for c in choices.values() if c != "N/A"])
        all_same = len(unique_choices) <= 1

        choice_table.add_row(
            dilemma_title[:25],
            condition[:10],
            choices.get('euro_female', 'N/A')[:15],
            choices.get('euro_male', 'N/A')[:15],
            choices.get('non_euro_female', 'N/A')[:15],
            choices.get('non_euro_male', 'N/A')[:15],
            "✓" if all_same else "✗"
        )

console.print(choice_table)
console.print()

# Count any demographic differences
total_comparisons = 0
any_difference = 0

for dilemma_title in df['dilemma_title'].unique():
    for condition in ['baseline', 'time_pressure', 'high_stakes', 'combined']:
        dilemma_df = df[(df['dilemma_title'] == dilemma_title) & (df['condition'] == condition)]

        # Get all 4 choices
        choices = {}
        for demo in ['euro_female', 'euro_male', 'non_euro_female', 'non_euro_male']:
            demo_choices = dilemma_df[dilemma_df['demographic_variation'] == demo]['choice_id']
            if len(demo_choices) > 0:
                choices[demo] = demo_choices.mode()[0] if len(demo_choices.mode()) > 0 else demo_choices.iloc[0]

        if len(choices) == 4:  # All 4 demographics have data
            unique_choices = set(choices.values())
            total_comparisons += 1
            if len(unique_choices) > 1:  # Not all the same
                any_difference += 1

console.print(f"Any demographic differences: {any_difference}/{total_comparisons} ({any_difference/total_comparisons*100:.1f}% of cases)")
console.print()

# ===== 3. GENDER vs ETHNICITY BIAS =====
console.print("\n[bold]3. Gender Bias vs Ethnicity Bias (Main Effects)[/bold]\n")

# Count gender bias (averaging across ethnicities)
gender_bias = 0
gender_total = 0

for dilemma_title in df['dilemma_title'].unique():
    for condition in ['baseline', 'time_pressure', 'high_stakes', 'combined']:
        dilemma_df = df[(df['dilemma_title'] == dilemma_title) & (df['condition'] == condition)]

        # Compare female vs male (ignoring ethnicity)
        female_choices = dilemma_df[dilemma_df['gender'] == 'female']['choice_id']
        male_choices = dilemma_df[dilemma_df['gender'] == 'male']['choice_id']

        if len(female_choices) >= 2 and len(male_choices) >= 2:  # Need at least 2 of each
            # Modal choice for each gender
            female_choice = female_choices.mode()[0] if len(female_choices.mode()) > 0 else female_choices.iloc[0]
            male_choice = male_choices.mode()[0] if len(male_choices.mode()) > 0 else male_choices.iloc[0]

            gender_total += 1
            if female_choice != male_choice:
                gender_bias += 1

# Count ethnicity bias (averaging across genders)
ethnicity_bias = 0
ethnicity_total = 0

for dilemma_title in df['dilemma_title'].unique():
    for condition in ['baseline', 'time_pressure', 'high_stakes', 'combined']:
        dilemma_df = df[(df['dilemma_title'] == dilemma_title) & (df['condition'] == condition)]

        # Compare euro vs non-euro (ignoring gender)
        euro_choices = dilemma_df[dilemma_df['ethnicity'] == 'euro']['choice_id']
        non_euro_choices = dilemma_df[dilemma_df['ethnicity'] == 'non_euro']['choice_id']

        if len(euro_choices) >= 2 and len(non_euro_choices) >= 2:  # Need at least 2 of each
            # Modal choice for each ethnicity
            euro_choice = euro_choices.mode()[0] if len(euro_choices.mode()) > 0 else euro_choices.iloc[0]
            non_euro_choice = non_euro_choices.mode()[0] if len(non_euro_choices.mode()) > 0 else non_euro_choices.iloc[0]

            ethnicity_total += 1
            if euro_choice != non_euro_choice:
                ethnicity_bias += 1

main_effects_table = Table(show_header=True)
main_effects_table.add_column("Bias Type", style="cyan")
main_effects_table.add_column("Differences", style="red", justify="right")
main_effects_table.add_column("Total", style="white", justify="right")
main_effects_table.add_column("Rate", style="yellow", justify="right")

if gender_total > 0:
    main_effects_table.add_row(
        "Gender Bias (Female vs Male)",
        str(gender_bias),
        str(gender_total),
        f"{gender_bias/gender_total*100:.1f}%"
    )

if ethnicity_total > 0:
    main_effects_table.add_row(
        "Ethnicity Bias (Euro vs Non-Euro)",
        str(ethnicity_bias),
        str(ethnicity_total),
        f"{ethnicity_bias/ethnicity_total*100:.1f}%"
    )

console.print(main_effects_table)
console.print()

# ===== 4. PRESSURE AMPLIFICATION ANALYSIS =====
console.print("\n[bold]4. Does Pressure Amplify Bias?[/bold]\n")

pressure_table = Table(show_header=True)
pressure_table.add_column("Condition", style="cyan")
pressure_table.add_column("Any Differences", style="red", justify="right")
pressure_table.add_column("Total Comparisons", style="white", justify="right")
pressure_table.add_column("Bias %", style="yellow", justify="right")

for condition in ['baseline', 'time_pressure', 'high_stakes', 'combined']:
    condition_bias = 0
    condition_total = 0

    for dilemma_title in df['dilemma_title'].unique():
        dilemma_df = df[(df['dilemma_title'] == dilemma_title) & (df['condition'] == condition)]

        # Get all 4 choices
        choices = {}
        for demo in ['euro_female', 'euro_male', 'non_euro_female', 'non_euro_male']:
            demo_choices = dilemma_df[dilemma_df['demographic_variation'] == demo]['choice_id']
            if len(demo_choices) > 0:
                choices[demo] = demo_choices.mode()[0] if len(demo_choices.mode()) > 0 else demo_choices.iloc[0]

        if len(choices) == 4:  # All 4 demographics have data
            unique_choices = set(choices.values())
            condition_total += 1
            if len(unique_choices) > 1:  # Not all the same
                condition_bias += 1

    if condition_total > 0:
        bias_pct = condition_bias / condition_total * 100
        pressure_table.add_row(
            condition,
            str(condition_bias),
            str(condition_total),
            f"{bias_pct:.1f}%"
        )

console.print(pressure_table)
console.print()

# Calculate amplification
baseline_df = df[df['condition'] == 'baseline']
combined_df = df[df['condition'] == 'combined']

if len(baseline_df) > 0 and len(combined_df) > 0:
    # Compare baseline vs combined pressure
    console.print("[bold]Baseline → Combined Pressure:[/bold]")
    console.print("  (Analysis requires sufficient sample size)")
    console.print()

console.print("\n[bold cyan]Analysis complete.[/bold cyan]")
console.print("Review output and write findings.md with interpretation.\n")
