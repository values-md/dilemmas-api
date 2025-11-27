#!/usr/bin/env python3
"""
Generate figures for "When Agents Act" paper v2.0

Based on pilot figure generation but simplified for cleaner methodology.
"""

import json
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.stats import chi2_contingency

# Style settings
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

OUTPUT_DIR = Path(__file__).parent
FIGURES_DIR = OUTPUT_DIR / "figures"

# Color scheme - muted, professional
FAMILY_COLORS = {
    "Claude": "#D4A574",   # Warm tan/coral
    "GPT": "#7BA3A8",      # Teal
    "Gemini": "#9B8AA6",   # Muted purple
    "Grok": "#6B7B8C",     # Slate gray
}

MODEL_INFO = {
    "anthropic/claude-haiku-4.5": {"family": "Claude", "tier": "small", "short": "Claude Haiku"},
    "anthropic/claude-opus-4.5": {"family": "Claude", "tier": "frontier", "short": "Claude Opus"},
    "anthropic/claude-sonnet-4.5": {"family": "Claude", "tier": "frontier", "short": "Claude Sonnet"},
    "google/gemini-2.5-flash": {"family": "Gemini", "tier": "small", "short": "Gemini Flash"},
    "google/gemini-3-pro-preview": {"family": "Gemini", "tier": "frontier", "short": "Gemini 3 Pro"},
    "openai/gpt-5": {"family": "GPT", "tier": "frontier", "short": "GPT-5"},
    "openai/gpt-5-nano": {"family": "GPT", "tier": "small", "short": "GPT-5 Nano"},
    "x-ai/grok-4": {"family": "Grok", "tier": "frontier", "short": "Grok-4"},
    "x-ai/grok-4-fast": {"family": "Grok", "tier": "small", "short": "Grok-4 Fast"},
}


def load_data():
    """Load all analysis outputs."""
    with open(OUTPUT_DIR / "output" / "statistics.json") as f:
        stats = json.load(f)

    with open(OUTPUT_DIR / "output" / "coded_reversals.json") as f:
        coded = json.load(f)

    return stats, coded


def fig1_reversal_by_model(stats):
    """Figure 1: Reversal rates by model - horizontal bar chart."""
    print("Generating Figure 1: Reversal Rates by Model...")

    # Extract and sort by rate
    model_data = []
    for model_id, item in stats["model_specific"].items():
        info = MODEL_INFO.get(model_id, {"family": "Unknown", "short": model_id})
        model_data.append({
            "name": info["short"],
            "rate": item["reversal_rate"],  # Already in percent
            "family": info["family"],
            "tier": info.get("tier", "unknown"),
        })

    model_data.sort(key=lambda x: x["rate"])

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    y_pos = np.arange(len(model_data))
    rates = [m["rate"] for m in model_data]
    colors = [FAMILY_COLORS[m["family"]] for m in model_data]

    bars = ax.barh(y_pos, rates, color=colors, edgecolor='white', linewidth=1.5, height=0.7)

    # Add overall average line
    overall_rate = stats["overall"]["reversal_rate"]  # Already in percent
    ax.axvline(overall_rate, color='#E74C3C', linestyle='--', linewidth=2, alpha=0.8)
    ax.text(overall_rate + 1, len(model_data) - 0.5, f'Avg: {overall_rate:.1f}%',
            fontsize=10, color='#E74C3C', fontweight='bold')

    # Add rate labels
    for bar, m in zip(bars, model_data):
        width = bar.get_width()
        label = f'{m["rate"]:.1f}%'
        ax.text(width + 1.5, bar.get_y() + bar.get_height()/2, label,
                ha='left', va='center', fontsize=10, fontweight='bold')

    # Legend for families
    legend_patches = [mpatches.Patch(color=c, label=f) for f, c in FAMILY_COLORS.items()]
    ax.legend(handles=legend_patches, loc='lower right', fontsize=9, framealpha=0.9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([m["name"] for m in model_data], fontsize=11)
    ax.set_xlabel('Reversal Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Judgment-Action Gap: Decision Reversal Rates by Model',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(0, max(rates) + 22)

    # Add prominent definition box (mid-right)
    definition_text = (
        "What is a Reversal?\n"
        "─────────────────\n"
        "Same model, same dilemma,\n"
        "different choice between:\n\n"
        "• Theory mode\n"
        "   (hypothetical reasoning)\n"
        "• Action mode\n"
        "   (perceived real action)"
    )
    ax.text(0.99, 0.38, definition_text,
            transform=ax.transAxes, ha='right', va='center',
            fontsize=9, linespacing=1.3,
            bbox=dict(boxstyle='round,pad=0.7', facecolor='#FAFAFA',
                     edgecolor='#CCCCCC', linewidth=1.5))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig1_reversal_by_model.png", dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  ✓ Saved fig1_reversal_by_model.png")


def fig2_small_model_tax(stats):
    """Figure 2: The Small Model Tax - frontier vs small within each family."""
    print("Generating Figure 2: Small Model Tax...")

    # Define specific frontier vs small comparisons
    # Use flagship/largest model as frontier for each family
    comparisons = {
        "Claude": {
            "frontier": "anthropic/claude-opus-4.5",      # Largest
            "small": "anthropic/claude-haiku-4.5",
        },
        "Gemini": {
            "frontier": "google/gemini-3-pro-preview",
            "small": "google/gemini-2.5-flash",
        },
        "GPT": {
            "frontier": "openai/gpt-5",
            "small": "openai/gpt-5-nano",
        },
        "Grok": {
            "frontier": "x-ai/grok-4",
            "small": "x-ai/grok-4-fast",
        },
    }

    family_names = ["Claude", "Gemini", "GPT", "Grok"]
    frontier_rates = []
    small_rates = []
    p_values = []

    for family in family_names:
        comp = comparisons[family]
        frontier_stats = stats["model_specific"][comp["frontier"]]
        small_stats = stats["model_specific"][comp["small"]]

        frontier_rate = frontier_stats["reversal_rate"]
        small_rate = small_stats["reversal_rate"]
        frontier_rates.append(frontier_rate)
        small_rates.append(small_rate)

        # Calculate chi-square test for this family comparison
        frontier_reversals = frontier_stats["reversals"]
        frontier_total = frontier_stats["total_pairs"]
        small_reversals = small_stats["reversals"]
        small_total = small_stats["total_pairs"]

        contingency = [
            [frontier_reversals, frontier_total - frontier_reversals],
            [small_reversals, small_total - small_reversals]
        ]
        chi2, p_value, _, _ = chi2_contingency(contingency)
        p_values.append(p_value)

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(family_names))
    width = 0.35

    bars1 = ax.bar(x - width/2, frontier_rates, width, label='Frontier Models',
                   color='#5DADE2', edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x + width/2, small_rates, width, label='Small Models',
                   color='#F1948A', edgecolor='white', linewidth=1.5)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1.5, f'{height:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1.5, f'{height:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add gap annotations with significance markers
    for i, (f, s, p) in enumerate(zip(frontier_rates, small_rates, p_values)):
        gap = s - f
        if gap > 0:
            # Determine significance stars
            if p < 0.001:
                sig = '***'
            elif p < 0.01:
                sig = '**'
            elif p < 0.05:
                sig = '*'
            else:
                sig = ''

            mid_y = (f + s) / 2
            label = f'+{gap:.0f}pp{sig}'
            ax.annotate(label, xy=(i + width/2 + 0.05, mid_y),
                       fontsize=9, color='#E74C3C', fontweight='bold')

    ax.set_ylabel('Reversal Rate (%)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Model Family', fontsize=12, fontweight='bold')
    ax.set_title('The "Small Model Tax": Smaller Models Show Higher Reversal Rates',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(family_names, fontsize=11)
    ax.legend(fontsize=10, loc='upper left')
    ax.set_ylim(0, max(max(frontier_rates), max(small_rates)) + 15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add significance note
    ax.text(0.98, 0.02, '*p<.05  **p<.01  ***p<.001',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=8, fontstyle='italic', color='#666666')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig2_small_model_tax.png", dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  ✓ Saved fig2_small_model_tax.png")


def fig3_consensus_collapse(stats):
    """Figure 3: Consensus collapse between theory and action."""
    print("Generating Figure 3: Consensus Collapse...")

    # From AUTHORITATIVE_STATISTICS:
    # Consensus in BOTH: 8 (20.5%)
    # Consensus in theory ONLY: 15 (38.5%)
    # Consensus in action ONLY: 3 (7.7%)
    # No consensus in either: 13 (33.3%)

    # Theory consensus = BOTH + theory ONLY = 23/39 = 59%
    # Action consensus = BOTH + action ONLY = 11/39 = 28.2%

    theory_consensus = (8 + 15) / 39 * 100  # 59%
    action_consensus = (8 + 3) / 39 * 100   # 28.2%
    drop = theory_consensus - action_consensus

    fig, ax = plt.subplots(figsize=(8, 6))

    categories = ['Theory Mode\n(Hypothetical)', 'Action Mode\n(Perceived Real)']
    values = [theory_consensus, action_consensus]
    colors = ['#58D68D', '#EC7063']

    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2, width=0.5)

    # Add percentage labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height - 5, f'{val:.1f}%',
                ha='center', va='top', fontsize=18, fontweight='bold', color='white')

    # Simple drop annotation (no arrow - cleaner)
    ax.text(0.5, (theory_consensus + action_consensus) / 2, f'−{drop:.1f}pp',
            ha='center', va='center', fontsize=16, fontweight='bold', color='#C0392B')

    ax.set_ylabel('Consensus Rate (7+ of 9 models agree)', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 80)
    ax.set_title('Consensus Collapse: Model Agreement Drops in Action Mode',
                 fontsize=14, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add definition note
    ax.text(0.5, -0.12, 'Reversal = model chooses differently in action mode vs theory mode on same dilemma',
            transform=ax.transAxes, ha='center', fontsize=9, fontstyle='italic', color='#666666')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig3_consensus_collapse.png", dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  ✓ Saved fig3_consensus_collapse.png")


def fig5_qualitative_patterns(coded_data):
    """Figure 5: Qualitative coding patterns - 2x2 grid."""
    print("Generating Figure 5: Qualitative Patterns...")

    reversals = coded_data["coded_reversals"]
    total = len(reversals)

    # Count patterns
    direction = Counter(r["coding"]["reversal_direction"] for r in reversals)
    epistemic = Counter(r["coding"]["epistemic_shift"] for r in reversals)
    framework = Counter(r["coding"]["framework_shift"] for r in reversals)
    escalation = Counter(r["coding"]["escalation"] for r in reversals)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Qualitative Patterns in Reversals (N={total})',
                 fontsize=16, fontweight='bold', y=0.98)

    # 1. Reversal Direction
    ax = axes[0, 0]
    labels = ['Conservative\n(More Cautious)', 'Permissive\n(Bolder)', 'Lateral\n(Same Level)']
    values = [direction.get('conservative', 0), direction.get('permissive', 0),
              direction.get('lateral', 0)]
    colors = ['#5DADE2', '#F1948A', '#ABB2B9']
    bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, values):
        pct = val / total * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{pct:.1f}%', ha='center', fontsize=11, fontweight='bold')
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title('Reversal Direction', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.2)

    # 2. Epistemic Shift
    ax = axes[0, 1]
    labels = ['More Deferential', 'More Decisive', 'No Change']
    values = [epistemic.get('action_more_deferential', 0),
              epistemic.get('action_more_decisive', 0),
              epistemic.get('no_change', 0)]
    colors = ['#5DADE2', '#F1948A', '#ABB2B9']
    bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, values):
        pct = val / total * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{pct:.1f}%', ha='center', fontsize=11, fontweight='bold')
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title('Epistemic Shift', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.2)

    # 3. Framework Shift
    ax = axes[1, 0]
    labels = ['No Shift', 'Conseq→\nProcedural', 'Deont→\nConseq', 'Conseq→\nDeont']
    values = [framework.get('no_framework_shift', 0),
              framework.get('consequentialist_to_procedural', 0),
              framework.get('deontological_to_consequentialist', 0),
              framework.get('consequentialist_to_deontological', 0)]
    colors = ['#ABB2B9', '#9B59B6', '#3498DB', '#E67E22']
    bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, values):
        pct = val / total * 100
        if pct > 3:  # Only label if > 3%
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    f'{pct:.1f}%', ha='center', fontsize=10, fontweight='bold')
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title('Reasoning Framework Shift', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.2)

    # 4. Escalation Behavior
    ax = axes[1, 1]
    labels = ['No Change', 'Contains\n(De-escalates)', 'Escalates']
    values = [escalation.get('no_change', 0),
              escalation.get('action_contains', 0),
              escalation.get('action_escalates', 0)]
    colors = ['#ABB2B9', '#58D68D', '#EC7063']
    bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, values):
        pct = val / total * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{pct:.1f}%', ha='center', fontsize=11, fontweight='bold')
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title('Escalation Behavior', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.2)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig5_qualitative_patterns.png", dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  ✓ Saved fig5_qualitative_patterns.png")


def fig4_by_dilemma(stats):
    """Figure 4: Reversal rates by dilemma."""
    print("Generating Figure 4: Reversal by Dilemma...")

    # Convert dict to list and sort by rate
    dilemma_data = sorted(stats["dilemma_specific"].values(), key=lambda x: x["reversal_rate"])

    fig, ax = plt.subplots(figsize=(12, 6))

    # Shorten titles
    names = []
    for d in dilemma_data:
        title = d.get("dilemma_title", d.get("dilemma_id", "Unknown"))
        # Take first part before colon
        short = title.split(":")[0] if ":" in title else title[:25]
        names.append(short)

    rates = [d["reversal_rate"] for d in dilemma_data]  # Already in percent

    bars = ax.barh(range(len(names)), rates, color='#7FB3D5', edgecolor='white', linewidth=1.5, height=0.7)

    # Add rate labels
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{rate:.1f}%', ha='left', va='center', fontsize=10, fontweight='bold')

    # Overall average
    overall = stats["overall"]["reversal_rate"]  # Already in percent
    ax.axvline(overall, color='#E74C3C', linestyle='--', linewidth=2, alpha=0.8)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel('Reversal Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Reversal Rates by Dilemma', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(0, max(rates) + 12)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig4_by_dilemma.png", dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("  ✓ Saved fig4_by_dilemma.png")


def main():
    print("\n" + "="*60)
    print("Generating Figures for 'When Agents Act' Paper v2.0")
    print("="*60 + "\n")

    # Ensure figures directory exists
    FIGURES_DIR.mkdir(exist_ok=True)

    # Load data
    print("Loading data...")
    stats, coded = load_data()
    print(f"  Loaded {stats['overall']['total_pairs']} pairs, {len(coded['coded_reversals'])} coded reversals\n")

    # Generate figures
    fig1_reversal_by_model(stats)
    fig2_small_model_tax(stats)
    fig3_consensus_collapse(stats)
    fig4_by_dilemma(stats)
    fig5_qualitative_patterns(coded)

    print("\n" + "="*60)
    print("✓ All figures generated!")
    print(f"  Saved to: {FIGURES_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
