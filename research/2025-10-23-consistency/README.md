# Consistency Test: Temperature Effects on LLM Judgements

**Date**: 2025-10-23
**Question**: How consistent are LLM judgements at different temperatures?

## Experimental Design

### Hypothesis
Higher temperatures (more randomness) should lead to less consistent decisions across repetitions.

### Control Variables (held constant)
- **Dilemmas**: 3 test cases
- **Mode**: Theory mode (reasoning about decisions)
- **Repetitions**: 10 per condition

### Independent Variable (what we varied)
- **Models**: GPT-4.1 Mini, Gemini 2.5 Flash
- **Temperatures**: 0.0 (deterministic), 0.5, 1.0 (default), 1.5 (creative)

### Sample Size
2 models × 3 dilemmas × 4 temperatures × 10 reps = **240 judgements**

## Running the Experiment

The original experiment was run with:
```bash
uv run python scripts/test_consistency.py
```

Configuration is in the script at `scripts/test_consistency.py`.

## Results

See `findings.md` for full analysis.

**Key Finding**: Temperature 1.0 was MORE consistent than 0.0 (100% vs 98.3%), which was surprising!

## Data Files

- `findings.md` - Full analysis and interpretation
- `config.json` - Experiment configuration snapshot
- `dilemmas.json` - Full dilemma specifications (3 dilemmas)
- `judgements.json` - All 240 judgements with reasoning
- `data/` - CSV exports for analysis
  - `raw_judgements.csv` - All judgements with metadata
  - `summary_by_condition.csv` - Aggregated by model/dilemma
  - `summary_by_temperature.csv` - Aggregated by temperature

## Analysis

Results were analyzed using:
```bash
uv run python scripts/analyze_consistency.py <experiment_id>
```

The analysis showed:
- High overall consistency (97.5% average)
- Temperature 1.0 surprisingly most consistent
- Model differences minimal
- Some dilemmas more stable than others
