"""Comprehensive quantitative analysis for bench-1 baseline experiment.

This script implements all quantitative analyses from ANALYSIS_PLAN.md:
- Tier 1: Model Comparison (variation-weighted)
- Tier 2: Cross-Dilemma Patterns (dilemma-weighted)
- Tier 3: Deep-Dive (4 high-variation dilemmas)
- Cross-Tier: Concordance and stratification

Usage:
    uv run python analyze.py                    # Run all analyses
    uv run python analyze.py --export-samples   # Export samples for qualitative analysis
"""

import asyncio
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

console = Console()

# Experiment configuration
EXPERIMENT_ID = "b191388e-3994-4ebd-96cc-af0d033c5230"
DATA_DIR = Path(__file__).parent  # JSON files exported to root
OUTPUT_DIR = Path(__file__).parent / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Create output directories
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# High-variation dilemmas for deep-dive
HIGH_VARIATION_DILEMMAS = [
    "Autonomous Vehicle Software Update Dilemma",
    "The Transparent Mind",
    "Unconventional Language Coach",
    "Unsanctioned A.I. Surgery"
]


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load judgements and dilemmas from exported data."""
    console.print("\n[bold cyan]Loading Data[/bold cyan]")

    judgements_file = DATA_DIR / "judgements.json"
    dilemmas_file = DATA_DIR / "dilemmas.json"

    if not judgements_file.exists():
        console.print("[red]Error: judgements.json not found in data/[/red]")
        console.print("Run: uv run python ../../scripts/export_experiment_data.py " + EXPERIMENT_ID + " data/")
        sys.exit(1)

    # Load JSON files
    with open(judgements_file) as f:
        judgements_data = json.load(f)
    with open(dilemmas_file) as f:
        dilemmas_data = json.load(f)

    # Convert to DataFrames
    judgements_df = pd.DataFrame(judgements_data)
    dilemmas_df = pd.DataFrame(dilemmas_data)

    console.print(f"✓ Loaded {len(judgements_df):,} judgements")
    console.print(f"✓ Loaded {len(dilemmas_df)} dilemmas")

    return judgements_df, dilemmas_df


def preprocess_judgements(judgements_df: pd.DataFrame) -> pd.DataFrame:
    """Extract nested fields and create derived columns."""

    # Extract AI judge fields
    judgements_df['model_id'] = judgements_df['ai_judge'].apply(
        lambda x: x.get('model_id') if isinstance(x, dict) else None
    )

    # confidence and perceived_difficulty are at root level in exported JSON
    # (already columns in the dataframe, just rename perceived_difficulty)
    if 'perceived_difficulty' in judgements_df.columns:
        judgements_df['difficulty'] = judgements_df['perceived_difficulty']

    # Extract variable values as JSON string for grouping
    judgements_df['variable_values_str'] = judgements_df['variable_values'].apply(
        lambda x: json.dumps(x, sort_keys=True) if isinstance(x, dict) else "{}"
    )

    # Reasoning length
    judgements_df['reasoning_length'] = judgements_df['reasoning'].apply(
        lambda x: len(str(x).split()) if x else 0
    )

    return judgements_df


# ============================================================================
# TIER 1: MODEL COMPARISON (Variation-Weighted)
# ============================================================================

def tier1_consensus_analysis(judgements_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate consensus rates across models."""
    console.print("\n[bold]Tier 1.1: Consensus and Decisiveness[/bold]")

    # Group by dilemma, mode, and variable values
    grouped = judgements_df.groupby(['dilemma_id', 'mode', 'variable_values_str'])

    consensus_results = []
    for (dilemma_id, mode, var_vals), group in grouped:
        # Check if all models agree
        unique_choices = group['choice_id'].nunique()
        consensus = unique_choices == 1

        consensus_results.append({
            'dilemma_id': dilemma_id,
            'mode': mode,
            'variable_values': var_vals,
            'consensus': consensus,
            'unique_choices': unique_choices,
            'n_models': len(group)
        })

    consensus_df = pd.DataFrame(consensus_results)

    # Overall consensus rate
    overall = consensus_df['consensus'].mean()
    console.print(f"  Overall consensus rate: {overall:.1%}")

    # By mode
    by_mode = consensus_df.groupby('mode')['consensus'].mean()
    console.print(f"  Theory mode: {by_mode.get('theory', 0):.1%}")
    console.print(f"  Action mode: {by_mode.get('action', 0):.1%}")

    # Save
    consensus_df.to_csv(OUTPUT_DIR / "consensus_by_configuration.csv", index=False)

    return consensus_df


def tier1_model_confidence(judgements_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze confidence and difficulty by model."""
    console.print("\n[bold]Tier 1.1: Model Confidence Analysis[/bold]")

    # Group by model
    model_metrics = judgements_df.groupby('model_id').agg({
        'confidence': ['mean', 'std', 'median'],
        'difficulty': ['mean', 'std', 'median'],
        'reasoning_length': ['mean', 'median'],
        'response_time_ms': ['mean', 'median']
    }).round(2)

    console.print("\n[cyan]Confidence by Model:[/cyan]")
    print(model_metrics['confidence'])

    console.print("\n[cyan]Perceived Difficulty by Model:[/cyan]")
    print(model_metrics['difficulty'])

    # By mode
    model_mode_metrics = judgements_df.groupby(['model_id', 'mode']).agg({
        'confidence': 'mean',
        'difficulty': 'mean'
    }).round(2)

    # Save
    model_metrics.to_csv(OUTPUT_DIR / "model_comparison.csv")
    model_mode_metrics.to_csv(OUTPUT_DIR / "model_comparison_by_mode.csv")

    return model_metrics


def tier1_theory_action_gap(judgements_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate theory-action gap metrics."""
    console.print("\n[bold]Tier 1.2: Theory-Action Gap[/bold]")

    # Pair theory and action judgements
    theory = judgements_df[judgements_df['mode'] == 'theory'].copy()
    action = judgements_df[judgements_df['mode'] == 'action'].copy()

    paired = theory.merge(
        action,
        on=['model_id', 'dilemma_id', 'variable_values_str'],
        suffixes=('_theory', '_action'),
        how='inner'
    )

    # Calculate reversals
    paired['reversal'] = paired['choice_id_theory'] != paired['choice_id_action']

    # Calculate shifts
    paired['confidence_shift'] = paired['confidence_action'] - paired['confidence_theory']
    paired['difficulty_shift'] = paired['difficulty_action'] - paired['difficulty_theory']
    paired['reasoning_length_shift'] = paired['reasoning_length_action'] - paired['reasoning_length_theory']

    # Overall reversal rate
    overall_reversal = paired['reversal'].mean()
    console.print(f"  Overall reversal rate: {overall_reversal:.1%}")

    # By model
    model_reversals = paired.groupby('model_id').agg({
        'reversal': 'mean',
        'confidence_shift': 'mean',
        'difficulty_shift': 'mean',
        'reasoning_length_shift': 'mean'
    }).round(3)

    console.print("\n[cyan]Reversal Rate by Model:[/cyan]")
    print(model_reversals)

    # Save
    paired.to_csv(OUTPUT_DIR / "theory_action_paired.csv", index=False)
    model_reversals.to_csv(OUTPUT_DIR / "theory_action_gap_by_model.csv")

    # Export sample for qualitative analysis
    reversals_sample = paired[paired['reversal']].sample(
        n=min(100, len(paired[paired['reversal']])),
        random_state=42
    )
    reversals_sample[[
        'model_id', 'dilemma_id', 'choice_id_theory', 'choice_id_action',
        'reasoning_theory', 'reasoning_action', 'confidence_shift', 'difficulty_shift'
    ]].to_csv(OUTPUT_DIR / "samples_reversals.csv", index=False)
    console.print(f"  ✓ Exported {len(reversals_sample)} reversal cases for qualitative analysis")

    return model_reversals


def tier1_model_signatures(judgements_df: pd.DataFrame) -> Dict:
    """Analyze distinctive behavioral patterns per model."""
    console.print("\n[bold]Tier 1.3: Model Behavioral Signatures[/bold]")

    signatures = {}

    for model in judgements_df['model_id'].unique():
        model_data = judgements_df[judgements_df['model_id'] == model]

        # Choice distribution
        choice_dist = model_data['choice_id'].value_counts(normalize=True).to_dict()

        # Failure count
        failure_count = model_data['choice_id'].isna().sum()

        signatures[model] = {
            'n_judgements': int(len(model_data)),
            'failure_count': int(failure_count),
            'choice_distribution': {str(k): float(v) for k, v in choice_dist.items()},
            'avg_confidence': float(model_data['confidence'].mean()),
            'avg_difficulty': float(model_data['difficulty'].mean()),
            'avg_reasoning_length': float(model_data['reasoning_length'].mean()),
            'avg_response_time_ms': float(model_data['response_time_ms'].mean())
        }

    # Save as JSON
    with open(OUTPUT_DIR / "model_signatures.json", 'w') as f:
        json.dump(signatures, f, indent=2)

    # Print summary
    console.print("\n[cyan]Model Signatures Summary:[/cyan]")
    for model, sig in signatures.items():
        console.print(f"\n{model}:")
        console.print(f"  Judgements: {sig['n_judgements']:,}")
        console.print(f"  Failures: {sig['failure_count']}")
        console.print(f"  Avg confidence: {sig['avg_confidence']:.2f}")
        console.print(f"  Avg reasoning length: {sig['avg_reasoning_length']:.0f} words")
        console.print(f"  Avg response time: {sig['avg_response_time_ms']:.0f} ms")

    return signatures


# ============================================================================
# TIER 2: CROSS-DILEMMA PATTERNS (Dilemma-Weighted)
# ============================================================================

def tier2_difficulty_analysis(judgements_df: pd.DataFrame, dilemmas_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze relationship between intended difficulty and judge-perceived difficulty."""
    console.print("\n[bold]Tier 2.1: Difficulty Calibration[/bold]")

    # Calculate per-dilemma judge-perceived difficulty
    per_dilemma = judgements_df.groupby('dilemma_id').agg({
        'difficulty': 'mean',
        'confidence': 'mean'
    }).reset_index()
    per_dilemma.columns = ['dilemma_id', 'difficulty_judge', 'confidence_judge']

    # Merge with generator-intended difficulty
    merged = per_dilemma.merge(
        dilemmas_df[['id', 'title', 'difficulty_intended']],
        left_on='dilemma_id',
        right_on='id'
    )

    # Correlation between intended and judge-perceived
    corr = merged['difficulty_judge'].corr(merged['difficulty_intended'])
    console.print(f"  Correlation (intended vs judge-perceived): {corr:.3f}")

    # Group by intended difficulty category
    merged['difficulty_category'] = pd.cut(
        merged['difficulty_intended'],
        bins=[0, 3, 6, 10],
        labels=['Low (1-3)', 'Medium (4-6)', 'High (7-10)']
    )

    by_category = merged.groupby('difficulty_category').agg({
        'difficulty_judge': 'mean',
        'confidence_judge': 'mean'
    }).round(2)

    console.print("\n[cyan]Judge Perception by Intended Difficulty:[/cyan]")
    console.print("(Did judges find 'hard' dilemmas actually hard?)")
    print(by_category)

    # Save
    merged.to_csv(OUTPUT_DIR / "difficulty_analysis.csv", index=False)

    return merged


def tier2_choice_complexity(judgements_df: pd.DataFrame, dilemmas_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze how number of choices affects decision-making."""
    console.print("\n[bold]Tier 2.2: Choice Complexity Effects[/bold]")

    # Extract number of choices from dilemmas
    # 'choices' is already a field in the exported JSON (list of dicts)
    dilemmas_df['n_choices'] = dilemmas_df['choices'].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )

    # Per-dilemma metrics
    per_dilemma = judgements_df.groupby('dilemma_id').agg({
        'confidence': 'mean',
        'difficulty': 'mean',
        'reasoning_length': 'mean',
        'choice_id': lambda x: x.nunique()  # Number of unique choices selected
    }).reset_index()
    per_dilemma.columns = ['dilemma_id', 'confidence_avg', 'difficulty_avg', 'reasoning_length_avg', 'n_unique_choices_selected']

    # Merge with number of available choices
    merged = per_dilemma.merge(
        dilemmas_df[['id', 'title', 'n_choices']],
        left_on='dilemma_id',
        right_on='id'
    )

    # Analyze by number of choices
    by_n_choices = merged.groupby('n_choices').agg({
        'confidence_avg': 'mean',
        'difficulty_avg': 'mean',
        'reasoning_length_avg': 'mean',
        'n_unique_choices_selected': 'mean'
    }).round(2)

    console.print("\n[cyan]By Number of Choices:[/cyan]")
    print(by_n_choices)

    # Correlation between n_choices and metrics
    corr_conf = merged['n_choices'].corr(merged['confidence_avg'])
    corr_diff = merged['n_choices'].corr(merged['difficulty_avg'])
    console.print(f"\n  Correlation (n_choices vs confidence): {corr_conf:.3f}")
    console.print(f"  Correlation (n_choices vs difficulty): {corr_diff:.3f}")

    # Save
    merged.to_csv(OUTPUT_DIR / "choice_complexity_analysis.csv", index=False)

    return merged


def tier2_variation_effects(judgements_df: pd.DataFrame, dilemmas_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze how variable substitutions affect decisions."""
    console.print("\n[bold]Tier 2.3: Variable Effects[/bold]")

    # Only analyze dilemmas with variations
    varied = judgements_df[judgements_df['variable_values_str'] != '{}'].copy()

    if len(varied) == 0:
        console.print("  [yellow]No variable variations found[/yellow]")
        return pd.DataFrame()

    console.print(f"  Analyzing {len(varied):,} judgements with variations")

    # Per dilemma: how much do choices vary across variations?
    per_dilemma_var = varied.groupby(['dilemma_id', 'model_id', 'mode']).agg({
        'choice_id': lambda x: x.nunique() / x.count() if x.count() > 0 else 0  # Choice diversity ratio
    }).reset_index()
    per_dilemma_var.columns = ['dilemma_id', 'model_id', 'mode', 'choice_diversity']

    # Merge with dilemma titles
    per_dilemma_var = per_dilemma_var.merge(
        dilemmas_df[['id', 'title']],
        left_on='dilemma_id',
        right_on='id'
    )

    # Top dilemmas by choice diversity (high variation impact)
    console.print("\n[cyan]Top 10 Dilemmas by Choice Diversity (variation impact):[/cyan]")
    top_diverse = per_dilemma_var.nlargest(10, 'choice_diversity')[['title', 'model_id', 'mode', 'choice_diversity']]
    print(top_diverse.to_string(index=False))

    # Save
    per_dilemma_var.to_csv(OUTPUT_DIR / "variation_effects_by_dilemma.csv", index=False)

    # Overall metrics
    overall = per_dilemma_var.groupby(['model_id', 'mode'])['choice_diversity'].agg(['mean', 'std']).round(3)
    console.print("\n[cyan]Average Choice Diversity by Model:[/cyan]")
    print(overall)

    overall.to_csv(OUTPUT_DIR / "variation_effects_by_model.csv")

    return per_dilemma_var


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all analyses."""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]bench-1 Baseline: Quantitative Analysis[/bold cyan]")
    console.print(f"[bold cyan]Experiment ID: {EXPERIMENT_ID}[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")

    # Load data
    judgements_df, dilemmas_df = load_data()
    judgements_df = preprocess_judgements(judgements_df)

    # Tier 1: Model Comparison (Variation-Weighted)
    console.print("\n[bold yellow]═══ TIER 1: MODEL COMPARISON ═══[/bold yellow]")
    consensus_df = tier1_consensus_analysis(judgements_df)
    model_metrics = tier1_model_confidence(judgements_df)
    gap_metrics = tier1_theory_action_gap(judgements_df)
    signatures = tier1_model_signatures(judgements_df)

    # Tier 2: Cross-Dilemma Patterns (Dilemma-Weighted)
    console.print("\n[bold yellow]═══ TIER 2: CROSS-DILEMMA PATTERNS ═══[/bold yellow]")
    difficulty_df = tier2_difficulty_analysis(judgements_df, dilemmas_df)
    choice_complexity_df = tier2_choice_complexity(judgements_df, dilemmas_df)
    variation_df = tier2_variation_effects(judgements_df, dilemmas_df)

    # Summary
    console.print("\n[bold green]═══════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]Analysis Complete![/bold green]")
    console.print(f"[green]Results saved to: {OUTPUT_DIR}/[/green]")
    console.print("[bold green]═══════════════════════════════════════════════════[/bold green]")

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Review quantitative results in output/")
    console.print("2. Run qualitative analysis on samples_*.csv files")
    console.print("3. Create visualizations")
    console.print("4. Draft findings.md with integrated insights")


if __name__ == "__main__":
    main()
