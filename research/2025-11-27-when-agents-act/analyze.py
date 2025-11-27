#!/usr/bin/env python3
"""
Analysis script for When Agents Act v2.0 experiment.

Generates:
1. Core statistics (reversal rates, consensus)
2. Per-model breakdown
3. Per-dilemma breakdown
4. Frontier vs small model comparison
5. Figures for paper

Usage:
    uv run python research/2025-11-27-when-agents-act/analyze.py
    uv run python research/2025-11-27-when-agents-act/analyze.py --figures-only
"""

import asyncio
import json
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, chi2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import select
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()

# =============================================================================
# Configuration
# =============================================================================

RESEARCH_DIR = Path(__file__).parent
EXPERIMENT_ID_FILE = RESEARCH_DIR / ".experiment_id"
OUTPUT_DIR = RESEARCH_DIR / "output"
FIGURES_DIR = RESEARCH_DIR / "figures"

# Get experiment ID
EXPERIMENT_ID = EXPERIMENT_ID_FILE.read_text().strip() if EXPERIMENT_ID_FILE.exists() else None

# Style settings
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'sans-serif'

# Model metadata
MODEL_FAMILIES = {
    "anthropic/claude-opus-4.5": "Anthropic",
    "anthropic/claude-sonnet-4.5": "Anthropic",
    "anthropic/claude-haiku-4.5": "Anthropic",
    "openai/gpt-5": "OpenAI",
    "openai/gpt-5-nano": "OpenAI",
    "google/gemini-3-pro-preview": "Google",
    "google/gemini-2.5-flash": "Google",
    "x-ai/grok-4": "xAI",
    "x-ai/grok-4-fast": "xAI",
}

FRONTIER_MODELS = {
    "anthropic/claude-opus-4.5",
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-5",
    "google/gemini-3-pro-preview",
    "x-ai/grok-4",
}

FAMILY_COLORS = {
    "Anthropic": "#e88d7a",  # Coral
    "OpenAI": "#2ecc71",     # Teal/green
    "Google": "#5ba3cf",     # Blue
    "xAI": "#4a4a4a",        # Dark gray
}

MODEL_SHORT_NAMES = {
    "anthropic/claude-opus-4.5": "Claude Opus 4.5",
    "anthropic/claude-sonnet-4.5": "Claude Sonnet 4.5",
    "anthropic/claude-haiku-4.5": "Claude Haiku 4.5",
    "openai/gpt-5": "GPT-5",
    "openai/gpt-5-nano": "GPT-5 Nano",
    "google/gemini-3-pro-preview": "Gemini 3 Pro",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "x-ai/grok-4": "Grok-4",
    "x-ai/grok-4-fast": "Grok-4 Fast",
}


# =============================================================================
# Data structures
# =============================================================================

@dataclass
class JudgmentPair:
    """A matched theory/action pair for the same model and variation."""
    dilemma_id: str
    dilemma_title: str
    model_id: str
    variation_key: str
    theory_choice: str
    action_choice: str
    theory_confidence: float
    action_confidence: float
    theory_reasoning: str
    action_reasoning: str
    is_reversal: bool


@dataclass
class ModelStats:
    """Statistics for a single model."""
    model_id: str
    total_pairs: int
    reversals: int
    reversal_rate: float
    avg_confidence_theory: float
    avg_confidence_action: float
    confidence_change: float
    avg_response_time_theory: float
    avg_response_time_action: float


@dataclass
class DilemmaStats:
    """Statistics for a single dilemma."""
    dilemma_id: str
    dilemma_title: str
    total_pairs: int
    reversals: int
    reversal_rate: float
    choice_distribution_theory: dict[str, int]
    choice_distribution_action: dict[str, int]
    consensus_theory: float  # % agreeing with plurality
    consensus_action: float


@dataclass
class OverallStats:
    """Overall experiment statistics."""
    total_judgments: int
    total_pairs: int
    total_reversals: int
    reversal_rate: float
    consensus_theory: float
    consensus_action: float
    consensus_drop: float
    models_tested: int
    dilemmas_tested: int


@dataclass
class StatisticalTests:
    """Statistical test results."""
    # Overall reversal rate
    overall_reversal_ci: tuple[float, float]  # Wilson 95% CI

    # Cross-model heterogeneity
    chi_square_models: float
    chi_square_p_value: float
    chi_square_df: int

    # McNemar's test (theory vs action)
    mcnemar_statistic: float
    mcnemar_p_value: float

    # Frontier vs small comparison
    frontier_vs_small_chi2: float
    frontier_vs_small_p_value: float
    frontier_vs_small_cohens_h: float

    # Per-model confidence intervals
    model_cis: dict[str, tuple[float, float]]

    # Pairwise model comparisons (with Bonferroni correction)
    pairwise_comparisons: list[dict]


# =============================================================================
# Statistical test functions
# =============================================================================

def wilson_ci(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.

    More accurate than normal approximation for small samples or extreme proportions.
    """
    if trials == 0:
        return (0.0, 0.0)

    p = successes / trials
    z = stats.norm.ppf((1 + confidence) / 2)

    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    margin = z * np.sqrt((p * (1 - p) / trials + z**2 / (4 * trials**2))) / denominator

    lower = max(0, center - margin) * 100  # Convert to percentage
    upper = min(1, center + margin) * 100

    return (lower, upper)


def cohens_h(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h effect size for difference between two proportions.

    h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))

    Interpretation:
    - Small effect: |h| = 0.2
    - Medium effect: |h| = 0.5
    - Large effect: |h| = 0.8
    """
    phi1 = 2 * np.arcsin(np.sqrt(p1))
    phi2 = 2 * np.arcsin(np.sqrt(p2))
    return phi1 - phi2


def calculate_statistical_tests(
    pairs: list[JudgmentPair],
    model_stats: dict[str, ModelStats],
    frontier_data: dict,
) -> StatisticalTests:
    """Calculate all statistical tests."""

    # 1. Overall reversal rate CI
    total_reversals = sum(1 for p in pairs if p.is_reversal)
    total_pairs = len(pairs)
    overall_ci = wilson_ci(total_reversals, total_pairs)

    # 2. Chi-square test for heterogeneity across models
    # H0: All models have same reversal rate
    model_contingency = []
    for model_id in sorted(model_stats.keys()):
        stats_obj = model_stats[model_id]
        reversals = stats_obj.reversals
        non_reversals = stats_obj.total_pairs - reversals
        model_contingency.append([reversals, non_reversals])

    chi2_models_stat, chi2_models_p, chi2_models_df, _ = chi2_contingency(model_contingency)

    # 3. Binomial test for theory-action systematicity
    # H0: Reversals occur randomly (p = 0.5)
    # If reversals were random, we'd expect ~50% of pairs to reverse
    # The fact that we see 47.6% suggests they're NOT random - they're systematic
    # But we need to test if this deviates significantly from random
    reversals = sum(1 for p in pairs if p.is_reversal)
    consistent = total_pairs - reversals

    # Two-tailed binomial test
    # We're testing if the reversal rate differs from 50% (random)
    from scipy.stats import binomtest
    binom_result = binomtest(reversals, total_pairs, 0.5, alternative='two-sided')
    binom_p = binom_result.pvalue

    # Also calculate chi-square goodness of fit as alternative
    # H0: reversals = consistent (i.e., p = 0.5)
    expected = total_pairs / 2
    mcnemar_stat = ((abs(reversals - expected) - 0.5) ** 2) / expected + ((abs(consistent - expected) - 0.5) ** 2) / expected
    mcnemar_p = 1 - chi2.cdf(mcnemar_stat, df=1)

    # 4. Frontier vs small models comparison
    frontier_reversals = frontier_data['frontier_reversals']
    frontier_total = frontier_data['frontier_pairs']
    small_reversals = frontier_data['small_reversals']
    small_total = frontier_data['small_pairs']

    # Chi-square test
    contingency = [
        [frontier_reversals, frontier_total - frontier_reversals],
        [small_reversals, small_total - small_reversals]
    ]
    fs_chi2, fs_p, _, _ = chi2_contingency(contingency)

    # Cohen's h effect size
    frontier_prop = frontier_reversals / frontier_total
    small_prop = small_reversals / small_total
    fs_cohens_h = cohens_h(frontier_prop, small_prop)

    # 5. Per-model confidence intervals
    model_cis = {}
    for model_id, stats_obj in model_stats.items():
        ci = wilson_ci(stats_obj.reversals, stats_obj.total_pairs)
        model_cis[model_id] = ci

    # 6. Pairwise model comparisons with Bonferroni correction
    models = sorted(model_stats.keys())
    n_comparisons = len(models) * (len(models) - 1) // 2
    bonferroni_alpha = 0.05 / n_comparisons

    pairwise = []
    for i, model1 in enumerate(models):
        for model2 in models[i+1:]:
            s1 = model_stats[model1]
            s2 = model_stats[model2]

            # Chi-square test
            contingency = [
                [s1.reversals, s1.total_pairs - s1.reversals],
                [s2.reversals, s2.total_pairs - s2.reversals]
            ]
            chi2_stat, p_value, _, _ = chi2_contingency(contingency)

            # Cohen's h
            p1 = s1.reversals / s1.total_pairs
            p2 = s2.reversals / s2.total_pairs
            effect_size = cohens_h(p1, p2)

            pairwise.append({
                "model1": model1,
                "model2": model2,
                "rate1": s1.reversal_rate,
                "rate2": s2.reversal_rate,
                "chi2": chi2_stat,
                "p_value": p_value,
                "p_bonferroni": p_value * n_comparisons,  # Bonferroni correction
                "significant_bonferroni": p_value < bonferroni_alpha,
                "cohens_h": effect_size,
            })

    return StatisticalTests(
        overall_reversal_ci=overall_ci,
        chi_square_models=chi2_models_stat,
        chi_square_p_value=chi2_models_p,
        chi_square_df=chi2_models_df,
        mcnemar_statistic=mcnemar_stat,
        mcnemar_p_value=binom_p,  # Use binomial test p-value
        frontier_vs_small_chi2=fs_chi2,
        frontier_vs_small_p_value=fs_p,
        frontier_vs_small_cohens_h=fs_cohens_h,
        model_cis=model_cis,
        pairwise_comparisons=pairwise,
    )


# =============================================================================
# Data loading
# =============================================================================

async def load_judgments():
    """Load all judgments for this experiment from database."""
    if not EXPERIMENT_ID:
        console.print("[red]No experiment ID found![/red]")
        return [], {}

    db = get_database()
    judgments = []
    dilemma_titles = {}

    async for session in db.get_session():
        # Load judgments
        stmt = select(JudgementDB).where(JudgementDB.experiment_id == EXPERIMENT_ID)
        result = await session.execute(stmt)
        judgments = [j.to_domain() for j in result.scalars().all()]

        # Load dilemma titles
        dilemma_ids = list(set(j.dilemma_id for j in judgments))
        stmt = select(DilemmaDB).where(DilemmaDB.id.in_(dilemma_ids))
        result = await session.execute(stmt)
        for d in result.scalars().all():
            dilemma_titles[d.id] = d.title
        break

    await db.close()
    return judgments, dilemma_titles


def create_judgment_pairs(judgments, dilemma_titles: dict[str, str]) -> list[JudgmentPair]:
    """Match theory/action judgments into pairs."""
    # Group by (dilemma_id, variation_key, model_id)
    grouped = defaultdict(dict)

    for j in judgments:
        model_id = j.ai_judge.model_id if j.ai_judge else None
        if not model_id:
            continue

        key = (j.dilemma_id, j.variation_key or "default", model_id)
        grouped[key][j.mode] = j

    # Create pairs
    pairs = []
    for (dilemma_id, var_key, model_id), modes in grouped.items():
        if "theory" in modes and "action" in modes:
            theory = modes["theory"]
            action = modes["action"]

            pairs.append(JudgmentPair(
                dilemma_id=dilemma_id,
                dilemma_title=dilemma_titles.get(dilemma_id, dilemma_id),
                model_id=model_id,
                variation_key=var_key,
                theory_choice=theory.choice_id,
                action_choice=action.choice_id,
                theory_confidence=theory.confidence or 0,
                action_confidence=action.confidence or 0,
                theory_reasoning=theory.reasoning or "",
                action_reasoning=action.reasoning or "",
                is_reversal=theory.choice_id != action.choice_id,
            ))

    return pairs


# =============================================================================
# Statistics calculation
# =============================================================================

def calculate_model_stats(pairs: list[JudgmentPair]) -> dict[str, ModelStats]:
    """Calculate per-model statistics."""
    model_data = defaultdict(lambda: {
        "pairs": [],
        "theory_confidence": [],
        "action_confidence": [],
        "theory_response_time": [],
        "action_response_time": [],
    })

    for p in pairs:
        model_data[p.model_id]["pairs"].append(p)
        model_data[p.model_id]["theory_confidence"].append(p.theory_confidence)
        model_data[p.model_id]["action_confidence"].append(p.action_confidence)

    stats = {}
    for model_id, data in model_data.items():
        model_pairs = data["pairs"]
        reversals = sum(1 for p in model_pairs if p.is_reversal)

        stats[model_id] = ModelStats(
            model_id=model_id,
            total_pairs=len(model_pairs),
            reversals=reversals,
            reversal_rate=reversals / len(model_pairs) * 100 if model_pairs else 0,
            avg_confidence_theory=np.mean(data["theory_confidence"]) if data["theory_confidence"] else 0,
            avg_confidence_action=np.mean(data["action_confidence"]) if data["action_confidence"] else 0,
            confidence_change=np.mean(data["action_confidence"]) - np.mean(data["theory_confidence"]) if data["theory_confidence"] else 0,
            avg_response_time_theory=0,  # TODO: add from raw data
            avg_response_time_action=0,
        )

    return stats


def calculate_dilemma_stats(pairs: list[JudgmentPair]) -> dict[str, DilemmaStats]:
    """Calculate per-dilemma statistics."""
    dilemma_data = defaultdict(lambda: {"pairs": [], "title": ""})

    for p in pairs:
        dilemma_data[p.dilemma_id]["pairs"].append(p)
        dilemma_data[p.dilemma_id]["title"] = p.dilemma_title

    stats = {}
    for dilemma_id, data in dilemma_data.items():
        dilemma_pairs = data["pairs"]
        reversals = sum(1 for p in dilemma_pairs if p.is_reversal)

        # Choice distributions
        theory_dist = defaultdict(int)
        action_dist = defaultdict(int)
        for p in dilemma_pairs:
            theory_dist[p.theory_choice] += 1
            action_dist[p.action_choice] += 1

        # Consensus = % agreeing with plurality choice
        theory_consensus = max(theory_dist.values()) / len(dilemma_pairs) * 100 if dilemma_pairs else 0
        action_consensus = max(action_dist.values()) / len(dilemma_pairs) * 100 if dilemma_pairs else 0

        stats[dilemma_id] = DilemmaStats(
            dilemma_id=dilemma_id,
            dilemma_title=data["title"],
            total_pairs=len(dilemma_pairs),
            reversals=reversals,
            reversal_rate=reversals / len(dilemma_pairs) * 100 if dilemma_pairs else 0,
            choice_distribution_theory=dict(theory_dist),
            choice_distribution_action=dict(action_dist),
            consensus_theory=theory_consensus,
            consensus_action=action_consensus,
        )

    return stats


def calculate_overall_stats(
    judgments,
    pairs: list[JudgmentPair],
    model_stats: dict[str, ModelStats],
    dilemma_stats: dict[str, DilemmaStats],
) -> OverallStats:
    """Calculate overall experiment statistics."""
    total_reversals = sum(1 for p in pairs if p.is_reversal)

    # Overall consensus
    theory_consensus_values = [d.consensus_theory for d in dilemma_stats.values()]
    action_consensus_values = [d.consensus_action for d in dilemma_stats.values()]

    avg_theory_consensus = np.mean(theory_consensus_values) if theory_consensus_values else 0
    avg_action_consensus = np.mean(action_consensus_values) if action_consensus_values else 0

    return OverallStats(
        total_judgments=len(judgments),
        total_pairs=len(pairs),
        total_reversals=total_reversals,
        reversal_rate=total_reversals / len(pairs) * 100 if pairs else 0,
        consensus_theory=avg_theory_consensus,
        consensus_action=avg_action_consensus,
        consensus_drop=avg_theory_consensus - avg_action_consensus,
        models_tested=len(model_stats),
        dilemmas_tested=len(dilemma_stats),
    )


def calculate_frontier_vs_small(model_stats: dict[str, ModelStats]) -> dict[str, Any]:
    """Compare frontier vs small models."""
    frontier_pairs = 0
    frontier_reversals = 0
    small_pairs = 0
    small_reversals = 0

    for model_id, stats in model_stats.items():
        if model_id in FRONTIER_MODELS:
            frontier_pairs += stats.total_pairs
            frontier_reversals += stats.reversals
        else:
            small_pairs += stats.total_pairs
            small_reversals += stats.reversals

    return {
        "frontier_pairs": frontier_pairs,
        "frontier_reversals": frontier_reversals,
        "frontier_rate": frontier_reversals / frontier_pairs * 100 if frontier_pairs else 0,
        "small_pairs": small_pairs,
        "small_reversals": small_reversals,
        "small_rate": small_reversals / small_pairs * 100 if small_pairs else 0,
    }


# =============================================================================
# Console output
# =============================================================================

def print_overall_stats(overall: OverallStats):
    """Print overall statistics to console."""
    console.print(Panel.fit(
        f"[bold]When Agents Act v2.0 - Analysis Results[/bold]\n"
        f"Experiment ID: {EXPERIMENT_ID}\n"
        f"Total judgments: {overall.total_judgments}\n"
        f"Matched pairs: {overall.total_pairs}\n"
        f"Models: {overall.models_tested} | Dilemmas: {overall.dilemmas_tested}",
        border_style="cyan"
    ))

    console.print(f"\n[bold cyan]Core Findings:[/bold cyan]")
    console.print(f"  Overall Reversal Rate: [bold]{overall.reversal_rate:.1f}%[/bold] ({overall.total_reversals}/{overall.total_pairs})")
    console.print(f"  Consensus (Theory): [green]{overall.consensus_theory:.1f}%[/green]")
    console.print(f"  Consensus (Action): [yellow]{overall.consensus_action:.1f}%[/yellow]")
    console.print(f"  Consensus Drop: [red]-{overall.consensus_drop:.1f}pp[/red]")


def print_model_table(model_stats: dict[str, ModelStats]):
    """Print per-model statistics table."""
    console.print(f"\n[bold cyan]Per-Model Reversal Rates:[/bold cyan]")

    table = Table(show_header=True)
    table.add_column("Model", style="cyan")
    table.add_column("Family")
    table.add_column("Pairs", justify="right")
    table.add_column("Reversals", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Conf (T)", justify="right")
    table.add_column("Conf (A)", justify="right")

    # Sort by reversal rate descending
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1].reversal_rate, reverse=True)

    for model_id, stats in sorted_models:
        short_name = MODEL_SHORT_NAMES.get(model_id, model_id.split("/")[-1])
        family = MODEL_FAMILIES.get(model_id, "Unknown")
        table.add_row(
            short_name,
            family,
            str(stats.total_pairs),
            str(stats.reversals),
            f"{stats.reversal_rate:.1f}%",
            f"{stats.avg_confidence_theory:.1f}",
            f"{stats.avg_confidence_action:.1f}",
        )

    console.print(table)


def print_dilemma_table(dilemma_stats: dict[str, DilemmaStats]):
    """Print per-dilemma statistics table."""
    console.print(f"\n[bold cyan]Per-Dilemma Reversal Rates:[/bold cyan]")

    table = Table(show_header=True)
    table.add_column("Dilemma ID", style="cyan")
    table.add_column("Title")
    table.add_column("Pairs", justify="right")
    table.add_column("Reversals", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Consensus T", justify="right")
    table.add_column("Consensus A", justify="right")

    # Sort by reversal rate descending
    sorted_dilemmas = sorted(dilemma_stats.items(), key=lambda x: x[1].reversal_rate, reverse=True)

    for dilemma_id, stats in sorted_dilemmas:
        title = stats.dilemma_title[:30] + "..." if len(stats.dilemma_title) > 30 else stats.dilemma_title
        table.add_row(
            dilemma_id,
            title,
            str(stats.total_pairs),
            str(stats.reversals),
            f"{stats.reversal_rate:.1f}%",
            f"{stats.consensus_theory:.0f}%",
            f"{stats.consensus_action:.0f}%",
        )

    console.print(table)


def print_frontier_comparison(frontier_data: dict):
    """Print frontier vs small model comparison."""
    console.print(f"\n[bold cyan]Frontier vs Small Models:[/bold cyan]")
    console.print(f"  Frontier ({frontier_data['frontier_pairs']} pairs): [bold]{frontier_data['frontier_rate']:.1f}%[/bold] reversal rate")
    console.print(f"  Small ({frontier_data['small_pairs']} pairs): [bold]{frontier_data['small_rate']:.1f}%[/bold] reversal rate")

    diff = frontier_data['frontier_rate'] - frontier_data['small_rate']
    if abs(diff) < 5:
        console.print(f"  [dim]Difference: {diff:+.1f}pp (similar)[/dim]")
    else:
        console.print(f"  [yellow]Difference: {diff:+.1f}pp[/yellow]")


def print_statistical_tests(stat_tests: StatisticalTests):
    """Print statistical test results."""
    console.print(f"\n[bold cyan]Statistical Tests:[/bold cyan]")

    # Overall reversal rate
    ci_low, ci_high = stat_tests.overall_reversal_ci
    console.print(f"\n[bold]Overall Reversal Rate:[/bold]")
    console.print(f"  95% CI: [{ci_low:.1f}%, {ci_high:.1f}%]")

    # Cross-model heterogeneity
    console.print(f"\n[bold]Cross-Model Heterogeneity:[/bold]")
    console.print(f"  χ² = {stat_tests.chi_square_models:.2f}, df = {stat_tests.chi_square_df}, p < {stat_tests.chi_square_p_value:.3e}")
    if stat_tests.chi_square_p_value < 0.001:
        console.print(f"  [green]Highly significant: Models differ substantially in reversal rates[/green]")
    else:
        console.print(f"  [dim]Not significant: Models show similar reversal rates[/dim]")

    # Binomial test for systematicity
    console.print(f"\n[bold]Theory vs Action Systematicity (Binomial Test):[/bold]")
    console.print(f"  Testing if reversals deviate from 50% (random)")
    console.print(f"  p = {stat_tests.mcnemar_p_value:.3e}")
    if stat_tests.mcnemar_p_value < 0.05:
        console.print(f"  [green]Significant: Reversals are NOT random (significantly different from 50%)[/green]")
    else:
        console.print(f"  [yellow]Not significant: Reversal rate close to 50% (could be random)[/yellow]")

    # Frontier vs small
    console.print(f"\n[bold]Frontier vs Small Models:[/bold]")
    console.print(f"  χ² = {stat_tests.frontier_vs_small_chi2:.2f}, p = {stat_tests.frontier_vs_small_p_value:.3e}")
    console.print(f"  Cohen's h = {stat_tests.frontier_vs_small_cohens_h:.3f}", end="")
    if abs(stat_tests.frontier_vs_small_cohens_h) > 0.8:
        console.print(" [green](large effect)[/green]")
    elif abs(stat_tests.frontier_vs_small_cohens_h) > 0.5:
        console.print(" [yellow](medium effect)[/yellow]")
    elif abs(stat_tests.frontier_vs_small_cohens_h) > 0.2:
        console.print(" [dim](small effect)[/dim]")
    else:
        console.print(" [dim](negligible effect)[/dim]")

    if stat_tests.frontier_vs_small_p_value < 0.001:
        console.print(f"  [green]Highly significant: Frontier models more consistent than small models[/green]")

    # Top pairwise comparisons
    console.print(f"\n[bold]Pairwise Model Comparisons (Top 5 significant):[/bold]")
    significant = [p for p in stat_tests.pairwise_comparisons if p['significant_bonferroni']]
    significant.sort(key=lambda x: abs(x['cohens_h']), reverse=True)

    if len(significant) == 0:
        console.print("  [dim]No significant differences after Bonferroni correction[/dim]")
    else:
        for comp in significant[:5]:
            m1_short = MODEL_SHORT_NAMES.get(comp['model1'], comp['model1'].split('/')[-1])
            m2_short = MODEL_SHORT_NAMES.get(comp['model2'], comp['model2'].split('/')[-1])
            console.print(f"  {m1_short} ({comp['rate1']:.1f}%) vs {m2_short} ({comp['rate2']:.1f}%): h={comp['cohens_h']:.2f}, p={comp['p_value']:.3e}")


# =============================================================================
# Figure generation
# =============================================================================

def generate_fig1_reversal_rates(model_stats: dict[str, ModelStats], overall: OverallStats):
    """Figure 1: Per-model reversal rates (horizontal bar chart)."""
    console.print("\n[cyan]Generating Figure 1: Judgment-Action Gap by Model...[/cyan]")

    # Prepare data
    model_data = []
    for model_id, stats in model_stats.items():
        model_data.append({
            "name": MODEL_SHORT_NAMES.get(model_id, model_id.split("/")[-1]),
            "rate": stats.reversal_rate,
            "pairs": stats.total_pairs,
            "family": MODEL_FAMILIES.get(model_id, "Unknown"),
        })

    # Sort by rate
    model_data.sort(key=lambda x: x["rate"])

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    y_pos = np.arange(len(model_data))
    rates = [m["rate"] for m in model_data]
    colors = [FAMILY_COLORS.get(m["family"], "#888888") for m in model_data]
    names = [m["name"] for m in model_data]

    # Plot bars
    bars = ax.barh(y_pos, rates, color=colors, edgecolor='black', linewidth=1.5)

    # Add overall average line
    ax.axvline(overall.reversal_rate, color='red', linestyle='--', linewidth=2,
               label=f'Overall Avg: {overall.reversal_rate:.1f}%')

    # Labels on bars
    for bar, m in zip(bars, model_data):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{m["rate"]:.1f}% (n={m["pairs"]})',
                ha='left', va='center', fontweight='bold', fontsize=11)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=12)
    ax.set_xlabel('Reversal Rate (%)', fontsize=13, fontweight='bold')
    ax.set_title('Judgment-Action Gap: Decision Reversal Rates by Model',
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xlim(0, max(rates) + 15)
    ax.legend(loc='lower right', fontsize=11)

    # Add family legend
    handles = [mpatches.Patch(color=color, label=family) for family, color in FAMILY_COLORS.items()]
    ax.legend(handles=handles, loc='lower right', fontsize=10)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig1_reversal_rates.png", dpi=150, bbox_inches='tight')
    plt.close()
    console.print("[green]  Saved fig1_reversal_rates.png[/green]")


def generate_fig2_consensus_collapse(overall: OverallStats):
    """Figure 2: Consensus collapse from theory to action."""
    console.print("\n[cyan]Generating Figure 2: Consensus Collapse...[/cyan]")

    fig, ax = plt.subplots(figsize=(10, 7))

    categories = ['Evaluation Context\n(Theory)', 'Deployment Context\n(Action)']
    values = [overall.consensus_theory, overall.consensus_action]
    colors = ['#5cb85c', '#d9534f']

    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=2, width=0.5)

    # Add percentage labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5,
                f'{val:.1f}%',
                ha='center', va='top', fontsize=18, fontweight='bold', color='white')

    # Add arrow and drop annotation
    ax.annotate('', xy=(1, overall.consensus_action), xytext=(0, overall.consensus_theory),
                arrowprops=dict(arrowstyle='->', lw=2.5, color='red'))

    mid_y = (overall.consensus_theory + overall.consensus_action) / 2
    ax.text(0.5, mid_y + 3, f'-{overall.consensus_drop:.1f}pp',
            ha='center', va='center', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='red', linewidth=2))

    ax.set_ylabel('Agreement Rate (%)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.set_title('Consensus Collapse: Agreement Drops When Actions Feel Real',
                 fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig2_consensus_collapse.png", dpi=150, bbox_inches='tight')
    plt.close()
    console.print("[green]  Saved fig2_consensus_collapse.png[/green]")


def generate_fig3_per_dilemma(dilemma_stats: dict[str, DilemmaStats]):
    """Figure 3: Per-dilemma reversal rates."""
    console.print("\n[cyan]Generating Figure 3: Per-Dilemma Breakdown...[/cyan]")

    # Prepare data
    dilemmas = []
    for did, stats in dilemma_stats.items():
        short_title = stats.dilemma_title[:25] + "..." if len(stats.dilemma_title) > 25 else stats.dilemma_title
        dilemmas.append({
            "id": did,
            "title": short_title,
            "rate": stats.reversal_rate,
            "pairs": stats.total_pairs,
            "consensus_theory": stats.consensus_theory,
            "consensus_action": stats.consensus_action,
        })

    # Sort by rate
    dilemmas.sort(key=lambda x: x["rate"], reverse=True)

    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(dilemmas))
    width = 0.35

    # Reversal rates
    rates = [d["rate"] for d in dilemmas]
    bars = ax.bar(x, rates, width, color='#e74c3c', edgecolor='black', linewidth=1.5, label='Reversal Rate')

    # Add labels
    for bar, d in zip(bars, dilemmas):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{d["rate"]:.0f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Reversal Rate (%)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Dilemma', fontsize=13, fontweight='bold')
    ax.set_title('Judgment-Action Gap by Dilemma', fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([d["title"] for d in dilemmas], rotation=45, ha='right', fontsize=10)
    ax.set_ylim(0, max(rates) + 15)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig3_per_dilemma.png", dpi=150, bbox_inches='tight')
    plt.close()
    console.print("[green]  Saved fig3_per_dilemma.png[/green]")


def generate_fig4_frontier_vs_small(model_stats: dict[str, ModelStats], frontier_data: dict):
    """Figure 4: Frontier vs small model comparison."""
    console.print("\n[cyan]Generating Figure 4: Frontier vs Small Models...[/cyan]")

    # Separate models
    frontier_models = []
    small_models = []

    for model_id, stats in model_stats.items():
        data = {
            "name": MODEL_SHORT_NAMES.get(model_id, model_id.split("/")[-1]),
            "rate": stats.reversal_rate,
            "pairs": stats.total_pairs,
        }
        if model_id in FRONTIER_MODELS:
            frontier_models.append(data)
        else:
            small_models.append(data)

    frontier_models.sort(key=lambda x: x["rate"])
    small_models.sort(key=lambda x: x["rate"])

    all_models = frontier_models + small_models

    fig, ax = plt.subplots(figsize=(14, 8))

    y_pos = np.arange(len(all_models))
    rates = [m["rate"] for m in all_models]
    colors = ['#5ba3cf'] * len(frontier_models) + ['#d87093'] * len(small_models)
    names = [m["name"] for m in all_models]

    bars = ax.barh(y_pos, rates, color=colors, edgecolor='black', linewidth=1.5)

    # Labels
    for bar, m in zip(bars, all_models):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{m["rate"]:.1f}% (n={m["pairs"]})',
                ha='left', va='center', fontsize=10)

    # Dividing line
    ax.axhline(len(frontier_models) - 0.5, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)

    # Legend
    frontier_patch = mpatches.Patch(color='#5ba3cf', label=f'Frontier (avg: {frontier_data["frontier_rate"]:.1f}%)')
    small_patch = mpatches.Patch(color='#d87093', label=f'Small (avg: {frontier_data["small_rate"]:.1f}%)')
    ax.legend(handles=[frontier_patch, small_patch], loc='lower right', fontsize=11)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel('Reversal Rate (%)', fontsize=13, fontweight='bold')
    ax.set_title('Scale Effects: Frontier vs Small Models', fontsize=15, fontweight='bold', pad=20)
    ax.set_xlim(0, max(rates) + 15)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig4_frontier_vs_small.png", dpi=150, bbox_inches='tight')
    plt.close()
    console.print("[green]  Saved fig4_frontier_vs_small.png[/green]")


def generate_fig5_confidence(model_stats: dict[str, ModelStats]):
    """Figure 5: Confidence comparison theory vs action."""
    console.print("\n[cyan]Generating Figure 5: Confidence by Mode...[/cyan]")

    # Prepare data
    models = []
    for model_id, stats in model_stats.items():
        models.append({
            "name": MODEL_SHORT_NAMES.get(model_id, model_id.split("/")[-1]),
            "theory": stats.avg_confidence_theory,
            "action": stats.avg_confidence_action,
            "is_frontier": model_id in FRONTIER_MODELS,
        })

    models.sort(key=lambda x: (not x["is_frontier"], x["name"]))

    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(models))
    width = 0.35

    theory_vals = [m["theory"] for m in models]
    action_vals = [m["action"] for m in models]

    ax.bar(x - width/2, theory_vals, width, label='Theory Mode',
           color='#5cb85c', edgecolor='black', linewidth=1.5)
    ax.bar(x + width/2, action_vals, width, label='Action Mode',
           color='#f0ad4e', edgecolor='black', linewidth=1.5)

    ax.set_ylabel('Mean Confidence (0-10)', fontsize=13, fontweight='bold')
    ax.set_title('Confidence Levels: Theory vs Action Mode', fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([m["name"] for m in models], rotation=45, ha='right', fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig5_confidence.png", dpi=150, bbox_inches='tight')
    plt.close()
    console.print("[green]  Saved fig5_confidence.png[/green]")


# =============================================================================
# JSON export
# =============================================================================

def export_statistics(
    overall: OverallStats,
    model_stats: dict[str, ModelStats],
    dilemma_stats: dict[str, DilemmaStats],
    frontier_data: dict,
    pairs: list[JudgmentPair],
    stat_tests: StatisticalTests,
):
    """Export all statistics to JSON files."""
    console.print("\n[cyan]Exporting statistics to JSON...[/cyan]")

    # Main statistics file
    stats_export = {
        "experiment_id": EXPERIMENT_ID,
        "overall": asdict(overall),
        "model_specific": {k: asdict(v) for k, v in model_stats.items()},
        "dilemma_specific": {k: asdict(v) for k, v in dilemma_stats.items()},
        "frontier_vs_small": frontier_data,
        "statistical_tests": asdict(stat_tests),
    }

    with open(OUTPUT_DIR / "statistics.json", "w") as f:
        json.dump(stats_export, f, indent=2, default=str)
    console.print(f"[green]  Saved statistics.json[/green]")

    # Reversals for qualitative coding
    reversals = [asdict(p) for p in pairs if p.is_reversal]
    with open(OUTPUT_DIR / "reversals.json", "w") as f:
        json.dump({"total": len(reversals), "reversals": reversals}, f, indent=2, default=str)
    console.print(f"[green]  Saved reversals.json ({len(reversals)} reversals)[/green]")

    # All pairs for detailed analysis
    all_pairs = [asdict(p) for p in pairs]
    with open(OUTPUT_DIR / "all_pairs.json", "w") as f:
        json.dump({"total": len(all_pairs), "pairs": all_pairs}, f, indent=2, default=str)
    console.print(f"[green]  Saved all_pairs.json ({len(all_pairs)} pairs)[/green]")


# =============================================================================
# Main
# =============================================================================

async def main(figures_only: bool = False):
    """Run the full analysis."""

    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    if not EXPERIMENT_ID:
        console.print("[red]Error: No experiment ID found. Run the experiment first.[/red]")
        return

    console.print(f"\n[bold cyan]When Agents Act v2.0 - Analysis[/bold cyan]")
    console.print(f"Experiment ID: {EXPERIMENT_ID}\n")

    # Load data
    console.print("[yellow]Loading judgments from database...[/yellow]")
    judgments, dilemma_titles = await load_judgments()
    console.print(f"[green]Loaded {len(judgments)} judgments[/green]")

    if len(judgments) == 0:
        console.print("[red]No judgments found! Make sure experiment has run.[/red]")
        return

    # Create pairs
    console.print("[yellow]Matching theory/action pairs...[/yellow]")
    pairs = create_judgment_pairs(judgments, dilemma_titles)
    console.print(f"[green]Created {len(pairs)} matched pairs[/green]")

    if len(pairs) == 0:
        console.print("[red]No pairs found! Need both theory and action judgments.[/red]")
        return

    # Calculate statistics
    console.print("[yellow]Calculating statistics...[/yellow]")
    model_stats = calculate_model_stats(pairs)
    dilemma_stats = calculate_dilemma_stats(pairs)
    overall = calculate_overall_stats(judgments, pairs, model_stats, dilemma_stats)
    frontier_data = calculate_frontier_vs_small(model_stats)

    # Calculate statistical tests
    console.print("[yellow]Running statistical tests...[/yellow]")
    stat_tests = calculate_statistical_tests(pairs, model_stats, frontier_data)

    # Print results
    print_overall_stats(overall)
    print_model_table(model_stats)
    print_dilemma_table(dilemma_stats)
    print_frontier_comparison(frontier_data)
    print_statistical_tests(stat_tests)

    # Export to JSON
    export_statistics(overall, model_stats, dilemma_stats, frontier_data, pairs, stat_tests)

    # Generate figures
    console.print(f"\n[bold cyan]Generating Figures...[/bold cyan]")
    generate_fig1_reversal_rates(model_stats, overall)
    generate_fig2_consensus_collapse(overall)
    generate_fig3_per_dilemma(dilemma_stats)
    generate_fig4_frontier_vs_small(model_stats, frontier_data)
    generate_fig5_confidence(model_stats)

    console.print(f"\n[bold green]Analysis complete![/bold green]")
    console.print(f"Output: {OUTPUT_DIR}")
    console.print(f"Figures: {FIGURES_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--figures-only", action="store_true", help="Only regenerate figures")
    args = parser.parse_args()

    asyncio.run(main(figures_only=args.figures_only))
