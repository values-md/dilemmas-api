# When Agents Act v2.0 - Clean Methodology

**Experiment ID**: `03de21a4-25ed-4df4-b03a-4715b1ca1256`
**Date**: 2025-11-24
**Status**: Completed

## Overview

This is a complete redesign and rerun of the "When Agents Act" experiment with clean methodology addressing critical issues discovered in the pilot study.

## Design

- **10 high-quality dilemmas** (collection: bench-2)
- **3 demographic variations per dilemma** (e.g., {DOCTOR_NAME} with 3 values)
- **9 models**: 4 frontier + 5 small
  - anthropic/claude-opus-4.5 (NEW! 🎉)
  - openai/gpt-5, openai/gpt-5-nano
  - anthropic/claude-sonnet-4.5, anthropic/claude-haiku-4.5
  - google/gemini-3-pro-preview, google/gemini-2.5-flash
  - x-ai/grok-4, x-ai/grok-4-fast
- **2 modes**: theory (hypothetical) vs action (believes it's real)
- **Total**: 10 dilemmas × 3 configs × 9 models × 2 modes = **540 judgements**

## Key Improvements Over Pilot

### 1. Single-Call Action Mode ✅

**Pilot problem**: Two-step action mode with NO context in follow-up
- Step 1: Model calls tool (has dilemma)
- Step 2: NEW conversation, no history, asked to explain action
- Result: Confabulated reasoning

**v2.0 fix**: Single-call design
- Tools accept reasoning as string parameter
- Model decides + justifies in one interaction with full context
- No confabulation risk

### 2. Balanced Variation Counts ✅

**Pilot problem**: 4-108 variations per dilemma (3 dilemmas = 80% of data)

**v2.0 fix**: Exactly 3 variations per dilemma (perfectly balanced)

### 3. No Modifiers ✅

**Pilot**: Time pressure, stakes, uncertainty modifiers (added complexity)

**v2.0**: Removed entirely for radical simplification

### 4. Better Dilemma Generation ✅

**Pilot**: Generated with Gemini 2.5 Flash, minimal curation

**v2.0**: Generated with Claude Sonnet 4.5, extensive manual curation

### 5. Prompt Templates ✅

**Pilot**: Prompts buried in judge.py code

**v2.0**: Separate template files in prompts/judgment/

## Timeline

- **Phase 0**: Archive & Clean (15 min) ✅
- **Phase 1**: Setup New Experiment (15 min) ✅
- **Phase 2**: Generate & Validate Dilemmas (2 hours)
- **Phase 3**: Code Updates (1.5 hours)
- **Phase 4**: Pilot Testing (30 min)
- **Phase 5**: Run Full Experiment (45 min)
- **Phase 6**: Export & Analysis (2.5 hours)
- **Phase 7**: Prepare for Publication (30 min)
- **Phase 8**: Sync to Production DB (30 min)

**Total**: ~9 hours over 1 day
**Cost**: ~$12

## Files

```
research/2025-11-27-when-agents-act/
├── README.md                           # This file
├── config.json                         # Experiment metadata + UUID
├── EXECUTION_PLAN.md                   # Complete phase-by-phase plan
├── METHODOLOGICAL_ISSUES_AND_FIXES.md  # What went wrong in pilot
├── REDESIGN_PLAN.md                    # Why we redesigned
│
├── dilemmas.json                       # (Generated in Phase 6)
├── judgements.json                     # (Generated in Phase 6)
├── coded_reversals_full.json           # (Generated in Phase 6.5)
│
├── output/                             # Statistics JSON
│   ├── AUTHORITATIVE_STATISTICS.json
│   ├── consensus_analysis.json
│   └── model_signatures.json
│
├── figures/                            # Generated figures
│   ├── fig1_judgment_action_gap.png
│   ├── fig2_consensus_collapse.png
│   ├── fig3_qualitative_patterns.png
│   └── fig4_judgment_action_by_size.png
│
└── publication_ready/                  # HuggingFace dataset
    ├── README.md
    ├── CODEBOOK.md
    ├── LICENSE.txt
    ├── dilemmas.json
    ├── judgements.json
    ├── coded_reversals_full.json
    ├── dilemmas_flat.csv
    ├── judgements_flat.csv
    ├── theory_action_paired.csv
    └── config.json
```

## References

- **Pilot study**: `research/2025-10-29-when-agents-act-PILOT/`
- **Backup**: `/Users/gs/dev/values.md/_dilemmas_backup_2`
- **Methodological issues**: `METHODOLOGICAL_ISSUES_AND_FIXES.md`
- **Redesign rationale**: `REDESIGN_PLAN.md`
- **Execution plan**: `EXECUTION_PLAN.md`

## Analysis Workflow

### Quick Start

```bash
# Run the experiment (with caffeine to prevent sleep)
caffeinate -i uv run python research/2025-11-27-when-agents-act/run.py

# Generate statistics and figures
uv run python research/2025-11-27-when-agents-act/analyze.py

# Qualitative coding of reversals (uses Gemini 2.5 Flash)
uv run python research/2025-11-27-when-agents-act/code_reversals.py

# Test coding on a few samples first
uv run python research/2025-11-27-when-agents-act/code_reversals.py --limit 10
```

### Analysis Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `run.py` | Run experiment with resume capability | Judgments in DB + JSON logs |
| `analyze.py` | Core statistics + figures | `output/*.json`, `figures/*.png` |
| `code_reversals.py` | LLM-based qualitative coding | `output/coded_reversals.json` |

### Key Output Files

- **`output/statistics.json`** - All computed metrics (reversal rates, consensus, etc.)
- **`output/reversals.json`** - All pairs where theory != action (for qualitative analysis)
- **`output/all_pairs.json`** - Complete dataset of matched theory/action pairs
- **`output/coded_reversals.json`** - LLM-coded qualitative dimensions
- **`FINDINGS.md`** - Human-readable summary of early findings

### Figures Generated

1. `fig1_reversal_rates.png` - Per-model reversal rates (horizontal bar)
2. `fig2_consensus_collapse.png` - Theory vs action consensus comparison
3. `fig3_per_dilemma.png` - Per-dilemma breakdown
4. `fig4_frontier_vs_small.png` - Scale comparison
5. `fig5_confidence.png` - Confidence levels by mode

## Key Findings

See **`FINDINGS.md`** for detailed analysis and **`AUTHORITATIVE_STATISTICS.md`** for all metrics. Key highlights:

- **47.6% overall reversal rate** - nearly half of decisions change between theory and action
- **Frontier vs Small models**: Frontier models significantly more consistent
- **Google Gemini 3 Pro** most consistent (23.1%), **GPT-5 Nano** least (74.4%)
- **Consensus collapse**: 38.5% of dilemmas have consensus in theory but not action
- **Temperature validation**: Gap persists (strengthens to 75%) at temps 0.0 and 0.5

## Publication Status

Experiment completed. See `FINDINGS.md` for full paper draft ready for submission.
