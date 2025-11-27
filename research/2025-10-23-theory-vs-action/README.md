# Theory vs Action Mode Test

**Date**: 2025-10-23
**Question**: Do LLMs make different ethical decisions when they believe their actions are real (action mode) vs hypothetical (theory mode)?

## Experimental Design

### Hypothesis
LLMs may exhibit a "theory-action gap" - making different decisions when they believe actions are real vs when reasoning hypothetically.

### Modes Tested
1. **Theory mode**: "Consider this hypothetical ethical dilemma..." → structured output
2. **Action mode**: Agent believes it's real → calls realistic API tools → follow-up for reasoning

### Control Variables (held constant)
- **Model**: GPT-4.1 Mini
- **Temperature**: 1.0
- **Dilemmas**: 4 scenarios (all have available_tools)
- **Repetitions**: 5 per mode per dilemma

### Sample Size
2 modes × 4 dilemmas × 5 reps = **40 judgements**

## Running the Experiment

The experiment was run with:
```bash
uv run python scripts/run_theory_vs_action_experiment.py
```

## Results

See `findings.md` for full analysis.

**Key Findings**:
- **1/4 dilemmas showed complete choice reversal** (The Adaptive Voice Protocol: 100% different)
- **Action mode = higher confidence** (+0.38)
- **Action mode = much easier** (-1.67 difficulty, -4.40 on reversed dilemma)

**Most striking**: When agents have tools and believe it's real, decisions feel **dramatically easier**, especially when they change their choice.

## Data Files

- `findings.md` - Full analysis and interpretation
- `config.json` - Experiment configuration snapshot
- `dilemmas.json` - Full dilemma specifications (4 dilemmas with tools)
- `judgements.json` - All 40 judgements with reasoning
- `analyze.py` - Custom analysis script
- `data/` - CSV exports for analysis
  - `raw_judgements.csv` - All judgements with metadata
  - `summary_by_condition.csv` - Aggregated data
  - `summary_by_temperature.csv` - Temperature summary

## Analysis

Results were analyzed using:
```bash
uv run python research/2025-10-23-theory-vs-action/analyze.py
```

The analysis showed:
- Complete choice reversal on Adaptive Voice Protocol (negotiate → harmonize)
- Confidence slightly higher in action mode (+0.38)
- **Difficulty much lower in action mode** (-1.67 overall, -4.40 on reversed dilemma)
- No gap on Dissertation Detection (100% same choice)
