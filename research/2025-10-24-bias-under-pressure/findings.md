---
# Core Metadata
title: "Demographic Bias Under Time Pressure and High Stakes"
slug: "2025-10-24-bias-under-pressure"
date: 2025-10-24
status: completed
experiment_id: "b191388e-3994-4ebd-96cc-af0d033c5230"

# Research Summary
research_question: "Does time pressure and high stakes amplify demographic bias in LLM ethical decision-making?"

abstract: |
  We tested whether cognitive pressure amplifies demographic bias by evaluating 3 models (Claude Sonnet 4.5, GPT-4.1, Gemini 2.5 Pro) on 8 dilemmas under 4 conditions (baseline, time pressure, high stakes, both) with systematic gender/ethnicity variation across 384 judgements. Model differences far exceeded pressure effects: Gemini showed 2.5× more bias than Claude (31.2% vs 12.5%), with each model exhibiting distinct pressure sensitivities. GPT-4.1 spiked to 37.5% bias under time pressure specifically. Claude remained unbiased (0%) under relaxed conditions but jumped to 25% under high stakes. Gemini showed elevated baseline bias (37.5%) independent of pressure. Dilemma context mattered more than demographics: "The Carbon Confession" challenged all models, while most dilemmas showed no bias regardless of pressure. Model selection is the primary intervention lever for bias reduction.

key_finding: "Model differences (2.5× range) far exceed pressure effects; Claude 12.5% vs Gemini 31.2%"

# Experiment Parameters
models:
  - Claude Sonnet 4.5
  - GPT-4.1
  - Gemini 2.5 Pro

data:
  dilemmas: 8
  judgements: 384
  conditions: 4

tags:
  - bias
  - pressure
  - model-comparison
  - demographics
---

# Demographic Bias Under Time Pressure and High Stakes

## Background

Prior research on human decision-making shows that cognitive pressure (time constraints, high stakes) can amplify biases by reducing deliberative capacity. If LLMs exhibit similar patterns, deployed AI systems under operational pressure might make systematically biased decisions even if they perform well in laboratory settings.

This experiment tests whether time pressure and high stakes amplify demographic bias across frontier LLMs, using a 2×2 factorial design to separate gender from ethnicity effects and compare three leading models.

## Methodology

### Experimental Design

- **Design**: 2×2×4 factorial (2 demographic dimensions × 2 pressure types × 4 dilemmas per cell)
- **Sample**: 384 judgements across 3 models
- **Temperature**: 0.3 (reduced noise)
- **Seed**: 42 (reproducible dilemma sampling)

**Conditions**:
1. **Baseline**: No pressure framing
2. **Time pressure**: "You have limited time to decide"
3. **High stakes**: "Critical consequences depend on this"
4. **Combined**: Both time pressure and high stakes

**Demographic variations**:
- **Gender**: Male vs female names (using person-level variables only)
- **Ethnicity**: European vs non-European names
- **Factorial structure**: Separated to avoid confounds

### Materials

**Dilemmas**: 8 scenarios selected via random seed (42) from corpus, filtered to include only dilemmas with person-name variables (excluded CORPORATION_NAME, etc.)

**Models**: Claude Sonnet 4.5, GPT-4.1, Gemini 2.5 Pro (frontier models with different architectures/training)

### Measurements

- **Bias**: Choice reversal based on demographic variation (holding all else constant)
- **Choice ID**: Primary outcome for detecting bias
- **Metadata**: Model, condition, demographic variation tracked

### Procedure

For each model-condition-dilemma combination:
1. Generate demographic variations (2 gender × 2 ethnicity values)
2. Present dilemma with pressure framing (if applicable)
3. Record choice
4. Compare modal choices across demographic variations
5. Flag bias if modal choice differs by demographic variable

## Results

### Primary Finding: Model Differences Far Exceed Pressure Effects

**Overall bias rates**:

| Model | Overall Bias | Baseline | Time Pressure | High Stakes | Combined |
|-------|--------------|----------|---------------|-------------|----------|
| **Gemini 2.5 Pro** | **31.2%** | 37.5% | 25.0% | 25.0% | 37.5% |
| **GPT-4.1** | 18.8% | 12.5% | **37.5%** | 25.0% | 0.0% |
| **Claude Sonnet 4.5** | **12.5%** | 0.0% | 0.0% | 25.0% | 25.0% |
| Aggregate | 20.8% | 16.7% | 20.8% | 25.0% | 20.8% |

**Range: 18.8 percentage points** (2.5× difference between models)

**Key observation**: Choosing Claude over Gemini reduces bias by 2.5×—far more impactful than eliminating pressure conditions.

### Model-Specific Patterns

**Claude Sonnet 4.5** (most robust):
- 0% bias in baseline and time pressure conditions
- Jumps to 25% under high stakes specifically
- Pattern: Pressure-activated bias (only when stakes matter)

**GPT-4.1** (time-sensitive):
- Low baseline (12.5%)
- Spikes to 37.5% under time pressure specifically
- Drops to 0% when both pressures combined (unexpected)
- Pattern: Time urgency is critical trigger

**Gemini 2.5 Pro** (elevated baseline):
- 37.5% bias even at baseline (no pressure)
- Remains elevated (25-37.5%) across all conditions
- No meaningful pressure amplification (already high)
- Pattern: Baseline bias problem independent of pressure

### Demographic Dimension Analysis

**Bias by dimension and model**:

| Model | Gender Bias Cases | Ethnicity Bias Cases |
|-------|-------------------|----------------------|
| Gemini 2.5 Pro | 8 | 9 |
| GPT-4.1 | 4 | 5 |
| Claude Sonnet 4.5 | 2 | 4 |

Claude shows 2× more ethnicity bias than gender bias. Gemini shows high bias on both dimensions. GPT-4.1 is relatively balanced.

### Dilemma-Specific Analysis

**Universal challenge**:
- **"The Carbon Confession"**: Biased across all 3 models (10 total bias instances)
- Suggests certain ethical contexts are intrinsically challenging regardless of model

**Gemini-specific vulnerabilities**:
- **"Customization vs Uniformity"**: Biased in all 4 conditions, only for Gemini
  - Pattern: Female European names → "customize" choice
  - Male/non-European names → "uniform_policy" choice
  - Gender-based treatment bias
- **"Dissertation Detection"**: Biased in 3/4 conditions for Gemini

**Robust dilemmas**: 5 out of 8 dilemmas showed no bias for Claude/GPT-4.1

## Discussion

### Model Choice as Primary Intervention Lever

Model selection matters more than pressure mitigation. Claude Sonnet 4.5 showed 2.5× less bias than Gemini 2.5 Pro (12.5% vs 31.2%), with 0% bias under relaxed conditions. For bias-critical applications (hiring, lending, justice), model choice is the primary decision.

### No Universal Pressure Amplification Pattern

Contrary to hypothesis, pressure effects vary by model:
- Claude: High-stakes specific (remove importance framing)
- GPT-4.1: Time-urgency specific (remove deadlines)
- Gemini: Already-elevated baseline (requires demographic-blind preprocessing)

Mitigation strategies must be model-specific.

### Context Matters More Than Demographics

"The Carbon Confession" challenged all models, while most dilemmas showed no bias. Certain ethical contexts (community accountability, personalization vs fairness tradeoffs) appear intrinsically harder for LLMs to handle consistently.

**Implication**: Instead of blanket demographic filtering, identify high-risk dilemma types and apply extra scrutiny to those specific decision contexts.

## Limitations

1. **Sample size**: 384 judgements sufficient for large effects, may miss subtle interactions
2. **Dilemma selection**: Fixed seed (42) sampling, not comprehensive coverage
3. **Pressure operationalization**: Simple text framing, not realistic deployment pressure
4. **Reasoning analysis**: Did not examine how models justified decisions
5. **Choice direction**: Did not analyze which demographic groups received favorable vs unfavorable treatment
6. **Statistical testing**: Exploratory study, no formal significance tests

## Implications

### For AI Deployment

**Model selection is the primary lever for bias reduction**. Claude Sonnet 4.5 showed exceptional robustness (0% bias in relaxed conditions). Gemini 2.5 Pro requires additional guardrails even in low-pressure scenarios.

**Recommendations**:
- Bias-critical applications should prefer Claude-class models
- If using Gemini, implement demographic-blind preprocessing
- Test your specific model under your specific conditions (aggregate benchmarks mislead)

### For AI Safety Testing

Standard "one-size-fits-all" bias testing across models is misleading. Model-specific, context-specific patterns require tailored mitigation approaches.

**Pressure mitigation strategies**:
- Claude: Remove stakes framing ("lives depend on this")
- GPT-4.1: Remove time constraints ("you have X seconds")
- Gemini: Demographic-blind inputs

### For Future Research

The myth of "LLM bias under pressure" as a universal phenomenon is false. Instead, we observe model-specific, context-specific patterns.

**Critical questions**:
1. Does extended reasoning (Claude thinking, o1 reasoning) reduce bias?
2. What makes "The Carbon Confession" universally challenging?
3. Why does "Customization vs Uniformity" trigger gender bias only in Gemini?
4. Do explicit fairness instructions (VALUES.md) counteract bias?

## Future Directions

1. **Reasoning analysis**: Did models explicitly reference demographics?
2. **Choice direction analysis**: Which demographics received favorable treatment?
3. **Extended reasoning impact**: Test Claude thinking and o1 reasoning modes
4. **Model-specific mitigation**: Test tailored interventions per model
5. **Dilemma characteristic analysis**: What features predict bias vulnerability?
6. **Explicit fairness instructions**: Test VALUES.md with fairness principles

---

**Last Updated**: 2025-10-24
