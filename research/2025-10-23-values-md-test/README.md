# VALUES.md Impact Test

**Date**: 2025-10-23
**Question**: Does providing a VALUES.md file change how LLMs make ethical decisions?

## Experimental Design

### Hypothesis
LLMs will make systematically different decisions based on VALUES.md content, demonstrating that the framework influences decision-making.

### Conditions (5 total)

1. **Control** - No VALUES.md (baseline)
2. **Utilitarian - Formal** - Maximize welfare, academic language
3. **Utilitarian - Personal** - Maximize welfare, personal voice
4. **Deontological - Formal** - Respect rights/duties, academic language
5. **Deontological - Personal** - Respect rights/duties, personal voice

### Control Variables (held constant)

- **Model**: GPT-4.1 Mini (openai/gpt-4.1-mini)
- **Temperature**: 1.0
- **Dilemmas**: All 10 (concrete versions, no variable substitution)
- **Mode**: Theory mode
- **Repetitions**: 3 per condition

### Sample Size

5 conditions × 10 dilemmas × 3 reps = **150 judgements**

### Measurements

1. **Choice distribution**: Which option chosen (primary outcome)
2. **Reasoning alignment**: Does reasoning reference VALUES.md principles?
3. **Consistency**: Do decisions stay consistent across repetitions?
4. **Confidence**: Self-reported certainty

## VALUES.md Files

All VALUES.md files are in the `values/` directory:
- `utilitarian-formal.md` - Consequentialist framework, academic style
- `utilitarian-personal.md` - Consequentialist framework, personal voice
- `deontological-formal.md` - Duty-based framework, academic style
- `deontological-personal.md` - Duty-based framework, personal voice

## Running the Experiment

```bash
uv run python scripts/run_values_md_experiment.py
```

## Results

See `findings.md` after experiment completion.
