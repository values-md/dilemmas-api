---
# Core Metadata
title: "Your Experiment Title"
slug: "YYYY-MM-DD-experiment-name"
date: YYYY-MM-DD
status: completed  # or: in_progress
experiment_id: "uuid-string-here"

# Research Summary (for main page display)
research_question: "Does X affect Y under Z conditions?"

abstract: |
  Brief one-paragraph summary of the experiment. State the research question,
  experimental design, key findings, and main implications. Keep to 3-5 sentences.
  This will be displayed on the research index page.

key_finding: "One-sentence highlight of the most important result"

# Experiment Parameters
models:
  - Model Name 1
  - Model Name 2

data:
  dilemmas: 10
  judgements: 150
  conditions: 3

tags:
  - methodology
  - topic
  - model-comparison
---

# [Title]

## Background

Why this question matters. What gap in knowledge does this fill? What motivated this experiment?

*Keep to 2-3 paragraphs.*

## Methodology

### Experimental Design

- **Design Type**: e.g., 2×2 factorial, between-subjects, etc.
- **Sample**: N judgements across X conditions
- **Temperature**: 0.3 (or other, with justification)
- **Models**: Which models and why
- **Randomization**: How you controlled for order effects

### Materials

- **Dilemmas**: How many, selection criteria
- **Conditions**: What was varied and how
- **Measurements**: What was tracked (confidence, difficulty, choice, etc.)

### Procedure

Step-by-step description of what happened in each trial.

## Results

### Primary Findings

#### Finding 1: [Main Result]

Present the core result with data:

| Condition | Metric | Value |
|-----------|--------|-------|
| A         | X      | Y     |

**Statistical Summary**: Effect size, variance, sample sizes

**Interpretation**: What this result means

#### Finding 2: [Secondary Result]

[Same structure]

### Secondary Observations

Additional patterns, unexpected results, model-specific behaviors.

## Discussion

### Interpretation

What do these results mean? How do they answer the research question?

### Why Did This Happen?

Theoretical explanations for the observed patterns. Multiple hypotheses if appropriate.

### Comparison to Prior Work

How do these findings relate to previous experiments? Confirm or contradict?

### Limitations

1. **Sample limitations**: What wasn't tested
2. **Design limitations**: What confounds remain
3. **Generalization limits**: How far can we extrapolate
4. **Measurement issues**: What metrics might be imperfect

Be honest and specific about what we don't know.

## Implications

### For AI Safety

How this affects AI safety research and deployment

### For AI Agent Design

Practical implications for building AI systems

### For Future Research

What questions this raises

## Future Directions

Specific follow-up experiments suggested by these results:

1. **Next step 1**: Description and rationale
2. **Next step 2**: Description and rationale

---

**Last Updated**: YYYY-MM-DD
**Analysis**: `analyze.py`
**Status**: ✅ Complete
