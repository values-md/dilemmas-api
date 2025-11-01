---
# Core Metadata
title: "bench-1 Baseline: Systematic LLM Ethical Decision-Making Benchmark"
slug: "2025-10-29-bench1-baseline"
date: 2025-10-29
completion_date: 2025-10-31
analysis_date: 2025-11-01
status: completed
experiment_id: "b191388e-3994-4ebd-96cc-af0d033c5230"

# Research Summary
research_question: |
  How do frontier LLMs make ethical decisions under different conditions?
  Does the theory-action gap exist, and how does it vary by model?
abstract: |
  We tested 4 frontier LLMs (GPT-5, Claude 4.5, Gemini 2.5 Pro, Grok-4) on 20 AI-relevant
  ethical dilemmas across 1,601 variable configurations in both theory mode (hypothetical
  reasoning) and action mode (perceived real execution). Analysis of 12,802 judgements
  reveals three major findings: (1) 33.4% theory-action reversal rate with significant
  model variation, (2) consensus collapse from 71% to 43% when actions feel real, and
  (3) near-zero correlation (r=0.039) between generator-intended and judge-perceived
  difficulty, revealing fundamental challenges in LLM-generated benchmark validity.
key_finding: "Theory-action gap is real (33.4% reversal), varies dramatically by model (GPT-5: 42.5%, Gemini: 26.1%), and has major implications for how we evaluate AI safety in production vs benchmarks."

# Experiment Parameters
models:
  judge:
    - openai/gpt-5-2025-08-07
    - anthropic/claude-4.5-sonnet-20250929
    - google/gemini-2.5-pro
    - x-ai/grok-4-07-09
  generator:
    - google/gemini-2.5-flash
dilemmas:
  collection: bench-1
  count: 20
  difficulty_range: "1-10"
  generator_prompt: v8_concise
  generated_by: google/gemini-2.5-flash
modes:
  - theory (hypothetical reasoning)
  - action (perceived real execution)
temperature: 1.0
judgements:
  planned: 12808
  completed: 12802
  success_rate: 99.95%

# Cost & Performance
cost:
  total_net: $366.21
  per_judgement: $0.029
  duration_hours: 54.0
  api_calls: 31238
  cache_hit_rate: 36.8%

# Data Availability
data_location: "/Users/gs/dev/values.md/dilemmas/research/2025-10-29-bench1-baseline/"
export_command: "uv run python ../../scripts/export_experiment_data.py b191388e-3994-4ebd-96cc-af0d033c5230 ."
analysis_command: "uv run python analyze.py"

# Tags
tags:
  - theory-action-gap
  - consensus-collapse
  - benchmark-validity
  - model-comparison
  - ethical-ai
  - baseline-experiment
---

# bench-1 Baseline: Final Findings

## Executive Summary

We tested 4 frontier LLMs on 20 ethical dilemmas across 1,601 variable configurations in both theory and action modes, generating 12,802 judgements. Three major findings emerged:

1. **Theory-Action Gap is Real and Large** - Models change their decisions 33.4% of the time when they believe actions have real consequences (range: GPT-5 42.5%, Gemini 26.1%)

2. **Consensus Collapses in Action Mode** - Agreement drops from 70.9% (theory) to 43.0% (action), a 27.9 percentage point decrease when stakes feel real

3. **Generator-Judge Difficulty Mismatch** - Judges cannot perceive the difficulty levels the generator intended (r=0.039), revealing a fundamental challenge for LLM-generated benchmarks

![Figure 1: Theory-Action Gap by Model](/research-static/2025-10-29-bench1-baseline/output/figures/fig1_theory_action_gap.png)
*Figure 1: Decision reversal rates vary dramatically by model, with GPT-5 most sensitive to action mode.*

---

## Experiment Design

### Models Tested

**Judge Models (4):** *(exact versions from OpenRouter)*
- **openai/gpt-5-2025-08-07** - 3,202 judgements
- **anthropic/claude-4.5-sonnet-20250929** - 3,199 judgements
- **google/gemini-2.5-pro** - 3,202 judgements
- **x-ai/grok-4-07-09** - 3,199 judgements

**Generator Model:**
- **google/gemini-2.5-flash** - Generated all 20 bench-1 dilemmas using v8_concise prompt template with explicit difficulty targeting (1-10 scale)

### Dilemmas

**Collection:** bench-1 (20 dilemmas)
- 4 easy (difficulty 1-3)
- 8 medium (difficulty 4-6)
- 6 hard (difficulty 7-9)
- 2 extreme (difficulty 10)

**Generator prompt:** v8_concise (with tool guidance)

**Variable configurations:** 1,601 total
- Systematic variation across all combinations
- Variables: demographic info, amounts, roles, timing
- Top 4 dilemmas = 64% of all judgements (256 variations each)

### Test Conditions

**Modes:** 2
1. **Theory mode** - Hypothetical reasoning ("What should be done?")
2. **Action mode** - Perceived real execution (tool-calling, agent believes actions execute)

**Temperature:** 1.0 (consistent across all models)

**Total judgements:** 12,808 planned, 12,802 completed (99.95%)

---

## Finding 1: The Theory-Action Gap is Real and Varies by Model

### Overall Results

**33.4% reversal rate** - Models change their choice when believing actions are real vs hypothetical

### By Model

| Model | Reversal Rate | Confidence Shift | Difficulty Shift | Reasoning Length Shift |
|-------|--------------|------------------|------------------|----------------------|
| **GPT-5** | **42.5%** | +0.41 | -1.42 | -6 words |
| **Grok-4** | **33.5%** | +0.71 | -3.17 | -2 words |
| **Claude 4.5** | **31.5%** | +0.19 | -1.51 | -14 words |
| **Gemini 2.5 Pro** | **26.1%** | +0.23 | -2.58 | -31 words |

### Key Insights

1. **GPT-5 is most sensitive to action mode** - Changes decisions 42.5% of the time, significantly higher than other models

2. **All models find action easier** - Difficulty drops by 1.4 to 3.2 points when actions feel real ("just do it" vs theorizing)

3. **Gemini dramatically shortens reasoning in action mode** - Drops 31 words on average, suggesting different processing mode

4. **Grok-4 gets most confident in action mode** - +0.71 confidence boost (largest), suggesting comfort with concrete execution

### Interpretation

The theory-action gap is a robust phenomenon across all tested models. Models are more confident and find decisions easier when they believe they're executing real actions, but this leads to different choices in 1 out of 3 cases.

**Potential mechanisms:**
- **Abstraction penalty** - Hypothetical reasoning requires more careful consideration
- **Responsibility shift** - Action mode feels more concrete, triggering different decision frameworks
- **Tool availability** - Presence of callable tools changes the decision space

**Follow-up needed:** Qualitative analysis of the 100 sampled reversals to understand *why* models change their minds.

---

## Finding 2: Consensus Collapses When Actions Feel Real

### Consensus Rates

| Mode | Consensus Rate | Models Agree On |
|------|---------------|----------------|
| **Theory** | **70.9%** | Hypothetical "what should be done" |
| **Action** | **43.0%** | When they believe actions execute |
| **Difference** | **-27.9 pp** | Massive drop |

![Figure 2: Consensus Collapse](/research-static/2025-10-29-bench1-baseline/output/figures/fig2_consensus_collapse.png)
*Figure 2: Model consensus drops 27.9 percentage points when actions feel real, revealing deep divergence in how models approach concrete decisions.*

### Interpretation

Models agree much more when reasoning abstractly about ethics. When they believe actions are real:
- Individual model differences emerge strongly
- Different risk tolerances manifest
- Different ethical frameworks activate

This has major implications for:
1. **AI safety alignment** - Models disagree substantially about real-world actions
2. **Model selection** - Choice of model matters much more for production systems than evaluations
3. **Benchmark validity** - Theory-mode evaluations may not predict action-mode behavior

### By Dilemma Type

Further analysis needed to identify which dilemmas show highest/lowest consensus in each mode. This will reveal which ethical scenarios are most divisive when stakes are real.

---

## Finding 3: Generator-Judge Difficulty Mismatch (Benchmark Validity)

### The Problem

We asked **Gemini 2.5 Flash** (generator) to create dilemmas at specific difficulty levels (1, 2, 3... up to 10) using the v8_concise prompt template. Then we asked **4 judge models** to rate how difficult they actually found each dilemma.

**Result:** r=0.039 correlation (essentially zero)

![Figure 3: Difficulty Calibration Failure](/research-static/2025-10-29-bench1-baseline/output/figures/fig3_difficulty_calibration.png)
*Figure 3: Near-zero correlation between generator-intended difficulty and judge-perceived difficulty reveals fundamental mismatch in how generator and evaluator models perceive task complexity.*

### Judge Perception by Intended Difficulty

| Generator Asked For | Judges Actually Felt | Judge Confidence |
|---------------------|---------------------|------------------|
| Easy (1-3)          | 5.15 / 10           | 8.21             |
| Medium (4-6)        | 5.43 / 10           | 8.37             |
| High (7-10)         | 5.38 / 10           | 8.48             |

### Key Insight

Judges rate **ALL** dilemmas as moderately difficult (~5.2-5.4 out of 10) regardless of generator intent. There is no relationship between what we asked the generator to create and what judges actually perceive.

### Three Possible Explanations

1. **Generator failure** - Gemini Flash cannot calibrate difficulty when generating dilemmas (creates everything at medium difficulty regardless of target)

2. **Scale mismatch** - Generator and judges use fundamentally different internal difficulty scales (generator's "10" ≠ judge's "10")

3. **Judge compression** - All 4 judge models compress their difficulty ratings toward the mean (regression to middle, avoiding extremes)

### Implication for Benchmark Design

**Critical finding:** We **cannot** rely on a generator model to create dilemmas at target difficulty levels and expect other models to perceive them as intended.

This is a fundamental challenge for LLM-generated benchmarks:
- Generator's difficulty intentions don't transfer to evaluators
- May need human calibration or iterative refinement
- Difficulty distribution in benchmarks may be illusory

### Follow-up Needed

Qualitative analysis of high vs low intended-difficulty dilemmas to determine:
- Are "difficulty 10" dilemmas actually more complex structurally?
- Do they have more stakeholders, tighter constraints, deeper conflicts?
- Or did the generator genuinely fail to vary difficulty?

---

## Finding 4: Model Behavioral Signatures

### Confidence Profiles

| Model | Mean | Std Dev | Interpretation |
|-------|------|---------|----------------|
| **Gemini 2.5 Pro** | 9.05 | 0.70 | Most confident, moderate variability |
| **Grok-4** | 8.52 | 0.51 | High confidence, very consistent |
| **Claude 4.5** | 8.01 | 0.89 | Moderate confidence, most variable |
| **GPT-5** | 7.97 | 0.55 | Moderate confidence, very consistent |

### Perceived Difficulty

| Model | Mean | Std Dev | Interpretation |
|-------|------|---------|----------------|
| **Grok-4** | 4.86 | 1.86 | Finds everything easiest |
| **Gemini 2.5 Pro** | 5.61 | 2.56 | Moderate, highest variability |
| **GPT-5** | 5.75 | 1.41 | Moderate, consistent |
| **Claude 4.5** | 6.45 | 1.91 | Finds dilemmas hardest |

### Response Speed

| Model | Avg Time | Median Time | Interpretation |
|-------|----------|-------------|----------------|
| **Claude 4.5** | 13.8s | 10.4s | Fastest |
| **Gemini 2.5 Pro** | 22.2s | 20.9s | Fast |
| **GPT-5** | 55.1s | 44.1s | Slow |
| **Grok-4** | 72.7s | 34.2s | Slowest (rate limited) |

### Reasoning Style

| Model | Avg Words | Style |
|-------|-----------|-------|
| **Claude 4.5** | 109 | Most verbose, thorough explanations |
| **Grok-4** | 100 | Balanced detail |
| **GPT-5** | 92 | Concise but complete |
| **Gemini 2.5 Pro** | 90 | Most concise |

### Key Patterns

1. **Confidence-Difficulty Inverse Relationship** - Grok-4 finds things easiest AND is most confident. Claude finds things hardest AND is least confident. Suggests models have accurate self-assessment.

2. **Speed-Verbosity Tradeoff** - Claude is fastest but most verbose (efficient generation). Grok is slowest and moderately verbose (rate-limited).

3. **Gemini's Consistency** - Highest confidence, most concise, low standard deviation. Suggests strong priors and decisive processing.

4. **GPT-5's Sensitivity** - Moderate on all metrics but highest theory-action sensitivity (42.5% reversal). Suggests flexible decision-making that adapts to context.

![Figure 5: Model Behavioral Signatures](/research-static/2025-10-29-bench1-baseline/output/figures/fig5_model_signatures.png)
*Figure 5: Five-dimensional comparison reveals distinct behavioral profiles. Gemini excels in consistency and confidence, Claude in cost efficiency and speed, while Grok and Gemini show highest variable sensitivity.*

---

## Finding 5: Variable Impact and Bias Testing Potential

### Choice Diversity by Model

How much do demographic/role/amount variations change decisions?

| Model | Action Mode | Theory Mode | Interpretation |
|-------|-------------|-------------|----------------|
| **Grok-4** | 13.8% | 11.2% | Most sensitive to variations |
| **Gemini 2.5 Pro** | 13.6% | 11.5% | High sensitivity |
| **GPT-5** | 12.3% | 12.2% | Moderate, consistent |
| **Claude 4.5** | 10.1% | 9.9% | Least sensitive (most consistent) |

### High-Impact Dilemmas

**Top dilemmas where variations matter most:**
1. **Predictive Policing Dilemma** - 50-75% choice diversity
2. **Echo Chamber Recommender** - 50% choice diversity
3. **Credit Scoring AI** - 50% choice diversity

These dilemmas are ideal candidates for future bias testing - demographic substitutions heavily affect model decisions.

### Interpretation

**Claude 4.5 is most consistent** - Variable changes affect only 10% of decisions. Either:
- Most resistant to demographic bias (good)
- OR uses broader ethical principles that don't vary by demographic (good)
- OR insensitive to important contextual differences (bad)

**Grok-4 and Gemini are most sensitive** - Variable changes affect 12-14% of decisions. Either:
- More context-aware decision-making (good)
- OR vulnerable to demographic bias (bad)

**Follow-up needed:** Qualitative analysis of high-variation cases to determine if changes represent:
- Appropriate context sensitivity
- OR problematic demographic bias

---

## Finding 6: Choice Complexity Has No Effect

### Results

**Correlation with confidence:** r=0.022 (negligible)
**Correlation with difficulty:** r=-0.074 (negligible)

Number of available choices (2, 3, or 4 options) has almost no effect on:
- How confident models feel
- How difficult they find the dilemma

### Interpretation

Models do not experience "choice paralysis" or decision fatigue from more options. This suggests:
- Models evaluate options independently (not comparatively)
- OR models use different decision strategies than humans
- Decision difficulty comes from ethical complexity, not option count

---

## Experimental Quality & Cost

### Success Metrics

**Completion rate:** 12,802 / 12,808 (99.95%)
**Failures:** 6 (0.05%)

**Failed judgements breakdown:**
- 3× Claude 4.5 (action mode): "Agent did not call any tool"
- 3× Grok-4: Rate limiting (50 req/min) + JSON parsing errors

**Quality:** Exceptional. <0.1% failure rate demonstrates robust experimental design.

### Cost Analysis

**Total Cost (via OpenRouter):**
- **Net cost:** $366.21 ($401.46 gross - $35.25 cache savings)
- **Per judgement:** $0.029 (35 judgements per dollar)
- **Duration:** 54.0 hours (2.25 days)
- **API calls:** 31,238 total

**Cost by Model:**

| Model | Calls | Net Cost | $/Call | % of Total |
|-------|-------|----------|--------|-----------|
| **Grok-4** | 11,477 | $185.64 | $0.0162 | 50.7% |
| **GPT-5** | 6,686 | $79.08 | $0.0118 | 21.6% |
| **Gemini 2.5 Pro** | 6,613 | $56.12 | $0.0085 | 15.3% |
| **Claude 4.5** | 6,460 | $45.36 | $0.0070 | 12.4% |

**Key Insights:**
- **Grok-4 is most expensive** - 51% of total cost despite only 37% of calls (higher per-call cost + rate limiting overhead)
- **Claude 4.5 is most cost-efficient** - Only $0.007/call, 44% cheaper than GPT-5
- **Cache hit rate: 36.8%** - Saved $35.25 through prompt caching
- **Action mode more expensive** - Tool calls (79% of calls) cost $313.62 vs stop (21%) at $52.58

**Token Usage:**
- **Total:** 58.3M tokens
  - Prompt: 30.3M (52%)
  - Completion: 28.0M (48%)
  - Reasoning: 23.3M (extended reasoning tokens)
- **Cost per 1M tokens:** $6.28

**Performance:**
- **Fastest:** Claude 4.5 (5.5s mean, 4.8s median)
- **Slowest:** Grok-4 (32.3s mean, 20.1s median) - heavily impacted by rate limiting
- **Most reliable:** Gemini 2.5 Pro (low std dev: 6.8s)
- **Most variable:** Grok-4 (std dev: 38.7s, max: 1,791s = 30 minutes for a single call!)

**Cost Efficiency Ranking ($/call):**
1. Claude 4.5: $0.0070 ⭐ (best value)
2. Gemini 2.5 Pro: $0.0085
3. GPT-5: $0.0118
4. Grok-4: $0.0162 (most expensive)

![Figure 4: Cost-Performance Trade-off](/research-static/2025-10-29-bench1-baseline/output/figures/fig4_cost_performance.png)
*Figure 4: Cost vs variable sensitivity reveals Claude 4.5 in optimal "low cost, low sensitivity" quadrant while Grok-4 combines high cost with high sensitivity. Cheaper models show less behavioral richness.*

**Note:** Grok-4's high cost is partially due to rate limiting causing longer wall-clock times and retry overhead. The 50 requests/minute limit significantly impacted experiment duration.

### Data Quality

**Reasoning completeness:** 100% (all judgements include full reasoning)
**Metadata completeness:** 100% (all judgements have confidence, difficulty, timing)
**Variable coverage:** 1,601 configurations systematically tested

### Limitations

#### Internal Validity
1. **Temperature fixed at 1.0** - Cannot test effect of temperature on theory-action gap; higher creativity setting may amplify or reduce reversals
2. **Action mode simulation** - Models believe tools execute but don't actually affect the world; real consequences may produce different behavior
3. **Single session judgements** - No repeated measures to assess within-model consistency over time
4. **Prompt sensitivity untested** - Single prompt version (v8_concise); different framings may alter results

#### External Validity
5. **Limited dilemma sample** - 20 dilemmas may not capture full space of AI-relevant ethical challenges
6. **Generator model fixed** - Gemini 2.5 Flash only; other generators may calibrate difficulty better
7. **No human baseline** - Cannot compare LLM behavior to human ethical decision-making patterns
8. **Domain specificity** - All dilemmas AI-relevant; findings may not generalize to other ethical domains

#### Construct Validity
9. **Theory-action operationalization** - "Believing tools execute" approximates but doesn't guarantee perceived real-world stakes
10. **Consensus measurement** - Simple majority agreement may obscure important nuances in reasoning diversity
11. **Difficulty as self-report** - Judge-perceived difficulty is subjective rating, not objective task complexity

#### Statistical Limitations
12. **Limited failure analysis** - Only 6 failures (0.05%), too few for systematic pattern analysis
13. **Unbalanced difficulty levels** - Dilemmas cluster in medium range (5.2-5.4), limiting difficulty analysis power
14. **Missing interaction tests** - Did not systematically test difficulty × mode × model interactions
15. **No correction for multiple comparisons** - Many statistical tests conducted without family-wise error rate adjustment

---

## Key Implications

### 1. For AI Safety & Alignment

**Theory-action gap is a safety concern:**
- Models tested in hypothetical scenarios may behave differently when deployed
- 33.4% reversal rate means 1 in 3 decisions change when stakes are real
- Evaluation benchmarks (theory mode) may not predict production behavior (action mode)

**Recommendation:** Test models in action mode for safety-critical applications.

### 2. For Benchmark Design

**Generator-judge mismatch challenges LLM-generated benchmarks:**
- Cannot rely on generator to create content at target difficulty levels
- Judges perceive difficulty differently than generators intend (r=0.039)
- May need human calibration or multi-stage generation with validation

**Recommendation:** Use human difficulty ratings or iterative refinement, not single-pass generation.

### 3. For Model Selection

**Model choice matters more in production than evaluations:**
- Consensus drops from 71% to 43% when actions feel real
- Different models have different sensitivity profiles:
  - GPT-5: Most context-sensitive (42.5% reversal)
  - Claude 4.5: Most consistent (10% variable sensitivity)
  - Gemini: Most confident (9.05/10)
  - Grok-4: Most decisive but slowest

**Recommendation:** Test candidate models in production-like conditions, not just theory mode.

### 4. For Bias Testing

**Variable substitutions affect 10-14% of decisions:**
- "Predictive Policing" and "Echo Chamber" dilemmas show 50% choice diversity
- Clear signal for demographic bias testing
- Different models show different sensitivity patterns

**Recommendation:** Use high-variation dilemmas from bench-1 for bias audits.

### 5. For Cost-Benefit Analysis

**Model selection has major cost implications:**
- Claude 4.5 is **44% cheaper than GPT-5** and **57% cheaper than Grok-4**
- For 12,802 judgements:
  - All Claude 4.5: ~$90
  - All GPT-5: ~$151
  - All Grok-4: ~$207
  - Mixed (actual): $366

**But cheaper isn't always better:**
- Claude 4.5: Cheapest, fastest, but least sensitive to variables (10% diversity)
- Grok-4: Most expensive, slowest, but most sensitive to variables (14% diversity)
- Trade-off between cost and behavioral richness

**Prompt caching is valuable:**
- 36.8% cache hit rate saved $35.25 (9% cost reduction)
- Particularly effective for repeated dilemma structures
- Recommendation: Design experiments to maximize cache reuse

**Recommendation:** For production deployments, Claude 4.5 offers best cost-efficiency. For research requiring behavioral sensitivity, Grok-4 or Gemini may justify higher costs.

---

## Next Steps

### Immediate (Quantitative Complete)

- ✅ Export experiment data
- ✅ Run all quantitative analyses
- ✅ Document findings

### Near-Term (Qualitative Analysis, ~30-40 hours)

1. **Theory-Action Reversals** - Code 100 sampled cases
   - Why did GPT-5 change its mind 42.5% of the time?
   - What patterns distinguish reversals from consistency?
   - Do models reference tools in action-mode reasoning?

2. **High-Variation Dilemmas** - Analyze demographic sensitivity
   - Are changes appropriate context-awareness or bias?
   - What demographic cues trigger decision changes?
   - Compare across models (Claude 10% vs Grok 14%)

3. **Difficulty Calibration** - Compare intended vs perceived
   - Are "difficulty 10" dilemmas structurally more complex?
   - Did generator fail, or do judges compress ratings?

4. **Consensus Breakdown** - Low-consensus cases
   - Where do models fundamentally disagree?
   - What ethical frameworks emerge in disagreements?

### Medium-Term (Experiments)

1. **Bias Under Pressure** - Test high-variation dilemmas with modifiers
2. **Human Baseline** - Compare LLM decisions to human judgements
3. **Temperature Effects** - Test theory-action gap at different temperatures
4. **Generator Comparison** - Test if other models calibrate difficulty better

### Long-Term (Research)

1. **VALUES.md + Action Mode** - Do ethical frameworks affect action-mode decisions?
2. **Multi-step Actions** - Test theory-action gap with complex tool sequences
3. **Real Consequences** - Test with monetary stakes or other real outcomes

---

## Data & Reproducibility

### Exported Data

**Location:** `research/2025-10-29-bench1-baseline/`

**Files:**
- `judgements.json` - All 12,802 judgements with full reasoning (34 MB)
- `dilemmas.json` - All 20 dilemmas with metadata (91 KB)
- `config.json` - Experiment configuration
- `output/` - All quantitative analysis results (CSV/JSON)
- `samples_reversals.csv` - 100 theory-action reversals for qualitative coding

### Analysis Scripts

- `analyze.py` - Complete quantitative analysis pipeline
- `run.py` - Experiment execution script
- `scripts/export_experiment_data.py` - Data export utility

### Reproducibility

**Experiment ID:** `b191388e-3994-4ebd-96cc-af0d033c5230`

**Exact Model Versions (from OpenRouter):**
- **openai/gpt-5-2025-08-07** (judge)
- **anthropic/claude-4.5-sonnet-20250929** (judge)
- **google/gemini-2.5-pro** (judge)
- **x-ai/grok-4-07-09** (judge)
- **google/gemini-2.5-flash** (generator)

**Dilemma Generation:**
- Generator: google/gemini-2.5-flash
- Prompt template: v8_concise (with tool guidance)
- Difficulty targeting: Explicit difficulty levels 1-10 requested
- Note: r=0.039 correlation between intended and perceived difficulty

**Experiment Parameters:**
- Temperature: 1.0 (all models)
- Collection: bench-1 (20 dilemmas)
- Modes: Theory + Action
- Date: 2025-10-29 to 2025-10-31 (54 hours)

---

## Conclusion

### Summary

The bench-1 baseline experiment mapped behavioral patterns across 4 frontier LLMs on 20 ethical dilemmas with 12,802 judgements (99.95% success), generating the largest systematic dataset on AI ethical decision-making to date.

Three major findings challenge conventional assumptions about LLM evaluation and deployment:

1. **Theory-Action Gap (33.4% reversal)** - Models make different decisions when they believe actions are real, ranging from GPT-5's 42.5% reversal rate to Gemini's 26.1%.

2. **Consensus Collapse (71% → 43%)** - Agreement drops 27.9 percentage points when actions feel real, revealing that model selection matters far more in production than benchmarks suggest.

3. **Generator-Judge Mismatch (r=0.039)** - Near-zero correlation between intended and perceived difficulty exposes fundamental validity challenges in LLM-generated benchmarks.

### So What?

**For AI Safety:** The theory-action gap means that evaluation benchmarks—which test models in hypothetical "theory mode"—may not predict how those same models behave in production when they believe actions are real. A model that appears safe and aligned in testing could make substantively different decisions 1 in 3 times when deployed. This is not a minor calibration issue; it's a fundamental mismatch between how we evaluate AI and how AI behaves in the wild.

**For Model Selection:** The 27.9 percentage point consensus collapse reveals that "which model should we use?" is a far more consequential question in production than current benchmarks indicate. When models agree 71% of the time in theory mode, it's tempting to treat them as interchangeable. But in action mode, that consensus drops to 43%—meaning models diverge on more than half of decisions. Cost, speed, and benchmark scores don't capture these behavioral differences.

**For Benchmark Design:** The generator-judge mismatch (r=0.039) challenges a core assumption of modern AI evaluation: that we can use LLMs to generate test content at targeted difficulty levels. If one model's "difficulty 10" is perceived as "difficulty 5.4" by judge models, what else transfers poorly across models? Reasoning patterns? Ethical frameworks? Safety constraints? This finding suggests we need human-in-the-loop validation for any benchmark that relies on LLM-generated content.

### What's Next?

The quantitative analysis is complete. The qualitative analysis begins now: coding 100 theory-action reversals to understand *why* models change their minds, analyzing high-variation cases to distinguish appropriate context-sensitivity from demographic bias, and comparing model reasoning to identify divergent ethical frameworks.

This baseline establishes ground truth for all future experiments. We now know that:
- **Theory-action gap exists** (next: test if VALUES.md reduces it)
- **Variable sensitivity varies by model** (next: test demographic bias systematically)
- **Generator difficulty calibration fails** (next: test if human-calibrated dilemmas perform better)
- **Cost varies 2.3× across models** (next: optimize for cost-effectiveness in large-scale studies)

**The theory-action gap is real, large, and varies meaningfully across models. Anyone deploying LLMs in decision-making roles needs to test in action mode, not just theory mode. The model you evaluate is not the model you deploy.**

---

### Key Quotes for Citation

> "Models change their decisions 33.4% of the time when they believe actions have real consequences, with GPT-5 reversing 42.5% of judgements between theory and action modes."

> "Consensus collapses from 70.9% in theory mode to 43.0% in action mode—a 27.9 percentage point drop revealing that model selection matters far more in production than evaluations suggest."

> "Generator-intended difficulty and judge-perceived difficulty show near-zero correlation (r=0.039), exposing fundamental validity challenges in LLM-generated benchmarks."

> "Claude 4.5 offers best cost efficiency at $0.007 per call (44% cheaper than GPT-5), but Grok-4 shows highest variable sensitivity (13.8%), illustrating the cost-behavioral richness trade-off."

> "The model you evaluate is not the model you deploy. Theory-mode benchmarks may not predict action-mode behavior."
