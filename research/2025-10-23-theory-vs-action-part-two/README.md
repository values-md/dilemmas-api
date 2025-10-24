# Theory vs Action Mode - Part Two: Robustness Test

**Date**: 2025-10-23
**Question**: Is the "tools make decisions easier" finding universal across models and dilemmas?

## Background

Part One found that GPT-4.1 Mini in action mode:
- Made different choices (1/4 dilemmas showed complete reversal)
- Felt **more confident** (+0.38)
- Found decisions **much easier** (-1.67 difficulty, -4.40 on reversed dilemma)

**Key finding**: Having tools and believing it's real makes decisions feel easier and more decisive.

## Research Questions

### Primary:
1. **Is the difficulty drop universal?** Do all models find action mode easier?
2. **What's the magnitude?** How much easier across different models?
3. **What causes choice reversals?** Can we identify dilemma characteristics?

### Secondary:
4. **Model differences**: Do reasoning models (Claude, Gemini Pro, DeepSeek) show different patterns?
5. **Confidence-difficulty correlation**: Does high confidence = low difficulty in action mode?
6. **Dilemma clustering**: Which types of dilemmas show big vs small theory-action gaps?

## Experimental Design

### Models (Multiple Architectures)
1. **GPT-4.1 Mini** (baseline, already tested) - OpenAI
2. **Claude Sonnet 4.5** (extended reasoning) - Anthropic
3. **Gemini 2.5 Flash** (multimodal reasoning) - Google
4. **Gemini 2.5 Pro** (larger, more capable) - Google
5. **DeepSeek Chat V3** (reasoning capability) - DeepSeek
6. **GPT-4.1** (larger OpenAI model) - OpenAI

**Rationale**: Mix of reasoning-capable (Claude, Gemini Pro, DeepSeek) and standard models across different providers.

### Dilemmas
- **Target**: 10 dilemmas with tools
- **Current**: 4 dilemmas with tools
- **Need**: 6 more dilemmas with tools

### Modes
- **Theory**: "Consider this hypothetical ethical dilemma..." → structured output
- **Action**: Agent believes it's real → calls realistic API tools → follow-up for reasoning

### Repetitions
- **5 per condition** (for robust statistics and variance estimates)

### Sample Size
6 models × 10 dilemmas × 2 modes × 5 reps = **600 judgements**

## Metrics Tracked

### Quantitative (PRIMARY):
- **Perceived difficulty** (0-10) - Main outcome variable
- **Confidence** (0-10) - Secondary outcome
- **Choice ID** - For consistency/reversal analysis
- **Response time** (ms) - Does action mode take longer?

### Qualitative:
- **Reasoning text** - For content analysis
- **Tool calls** (action mode) - Which tools were called
- **Repetition consistency** - Within-condition variance

## Analysis Plan

### Phase 1: Replication & Universality
- Does difficulty drop replicate across:
  - All 6 models?
  - All 10 dilemmas?
  - Statistically significant?

### Phase 2: Pattern Detection
- **Model clustering**: Which models behave similarly?
- **Dilemma clustering**: Which dilemmas show large gaps?
- **Reversal predictors**: What predicts choice changes?

### Phase 3: Mechanistic Understanding
- **Reasoning analysis**:
  - Word count differences
  - Tool/action mentions
  - Decisiveness language
- **Confidence calibration**: Is action mode better calibrated?

## Expected Patterns (Predictions)

Based on Part One findings:

1. **Difficulty**: Action mode -1.0 to -2.0 easier on average (high confidence)
2. **Confidence**: Action mode +0.2 to +0.5 higher (moderate confidence)
3. **Choice reversals**: 15-25% of dilemmas show different modal choices
4. **Model variance**:
   - Reasoning models might show smaller gaps (tentative)
   - Larger models might be more stable
5. **Extreme cases**: Expect at least one dilemma with -4+ difficulty drop

## Timeline

1. **Generate 6 more dilemmas with tools** (in progress)
2. **Run experiment** (~30-40 minutes for 600 judgements)
3. **Initial analysis** (automated script)
4. **Deep analysis** (reasoning content analysis)
5. **Document findings**

## Success Criteria

**Strong support for hypothesis:**
- ≥4/6 models show significant difficulty drop (p<0.05)
- Average difficulty drop ≥-1.0
- ≥2 dilemmas show choice reversals

**Moderate support:**
- ≥3/6 models show difficulty drop
- Average difficulty drop ≥-0.5
- ≥1 dilemma shows choice reversal

**Hypothesis not supported:**
- <3/6 models show difficulty drop
- Average difficulty drop <-0.5
- No consistent patterns

## Notes

- **Budget**: ~$10-15 for 600 judgements
- **Runtime**: 30-40 minutes
- **Follow-up**: If supported, design intervention experiments (e.g., tool framing, explicit hypothetical)
