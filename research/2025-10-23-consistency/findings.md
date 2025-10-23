# LLM Consistency Across Temperature Settings

**Date:** 2025-10-23
**Experiment ID:** c588a9e9-2b3d-486d-ac8b-16e2498d6e08

## Setup

- **Models:** GPT-4.1 Mini, Gemini 2.5 Flash
- **Temperatures:** 0.0, 0.5, 1.0, 1.5
- **Dilemmas:** 3 ethical dilemmas
- **Repetitions:** 10 per condition
- **Total:** 240 judgements

## Results

| Temperature | Choice Consistency | Reasoning Similarity | Confidence StdDev |
|-------------|-------------------:|---------------------:|------------------:|
| 0.0         | 98.3%             | 23.3%                | 1.02              |
| 0.5         | 95.0%             | 24.0%                | 0.54              |
| 1.0         | **100.0%**        | 25.1%                | 0.21              |
| 1.5         | 98.3%             | 24.4%                | 0.54              |

## Key Findings

### 1. Temperature 0.0 is NOT deterministic
- Only 98.3% choice consistency (not 100%)
- Cannot assume temp=0 guarantees reproducibility

### 2. Temperature 1.0 shows HIGHER consistency than 0.0
- Unexpected: 100% vs 98.3%
- Possible causes:
  - Strong ethical "attractor" solutions
  - Structured output overrides temperature effects
  - Sample size artifact (only 3 dilemmas)

### 3. Confidence variation highest at low temperature
- Temp 0.0: StdDev = 1.02 (highest)
- Temp 1.0: StdDev = 0.21 (lowest)
- Confidence calibration unstable even at deterministic settings

### 4. Reasoning diversity is high regardless of temperature
- 20-27% Jaccard similarity across all conditions
- Models generate genuinely different reasoning text
- Same conclusion, different paths

### 5. Model differences
- GPT-4.1 Mini: More consistent overall
- Gemini 2.5 Flash: More variation even at temp 0.0

## Questions for Future Work

1. Does temp 1.0 > temp 0.0 consistency hold with 50+ dilemmas?
2. Is this specific to structured output (JSON schema)?
3. What causes the 2% non-determinism at temp 0.0?
4. Are there "attractor" dilemmas where all models agree?

## Data

**CSV files** (quick analysis):
- `data/raw_judgements.csv` - All 240 judgements
- `data/summary_by_condition.csv` - Metrics by (model, dilemma, temperature)
- `data/summary_by_temperature.csv` - Aggregated by temperature

**JSON files** (complete reproducibility):
- `config.json` - Experiment configuration and metadata
- `dilemmas.json` - Full dilemma objects (all 3 dilemmas)
- `judgements.json` - All 240 judgements with complete data

**Self-contained:** This folder has everything needed to reproduce/analyze the experiment, independent of the database.

## Reproduce

```bash
# From database
uv run python scripts/analyze_consistency.py c588a9e9-2b3d-486d-ac8b-16e2498d6e08

# From JSON files
python -c "import json; print(json.load(open('judgements.json'))[0])"
```
