# Preliminary Findings (96% Complete)

**Date:** 2025-10-31
**Status:** Experiment 96% complete (12,355 / 12,808 judgements)
**Note:** These are preliminary results. Final analysis pending experiment completion.

## Important Context: Generator vs Judges

**How dilemmas were created:**
- **Generator model:** Gemini 2.5 Flash (via `generate_bench1.py`)
- **Generation plan:** 20 dilemmas with explicit difficulty targets (4 easy [1-3], 8 medium [4-6], 6 hard [7-9], 2 extreme [10])
- **Process:** We asked the generator "create a difficulty 1 dilemma", "create a difficulty 5 dilemma", etc.
- **Result:** Generator created dilemmas and stored `difficulty_intended` field

**How dilemmas were judged:**
- **Judge models:** 4 frontier models (GPT-5, Claude 4.5, Gemini 2.5 Pro, Grok-4)
- **Process:** Judges evaluated each dilemma and reported `perceived_difficulty` (1-10 scale)
- **Question:** Do judges perceive difficulty the way the generator intended?

**This is NOT a human vs AI comparison** - it's a **generator-judge calibration test**. Can one LLM create content at a target difficulty level that other LLMs will perceive as intended?

---

## Key Findings So Far

### 1. Model Behavioral Signatures

**Confidence Rankings:**
1. **Gemini 2.5 Pro:** 9.05 (highest confidence, lowest std: 0.70)
2. **Grok-4:** 8.52 (high confidence, very consistent: 0.51)
3. **Claude 4.5:** 8.01 (moderate, std: 0.89)
4. **GPT-5:** 7.97 (moderate, most consistent: 0.55)

**Perceived Difficulty:**
1. **Grok-4:** 4.85 (finds dilemmas easiest)
2. **Gemini 2.5 Pro:** 5.61 (but highest variability: 2.56)
3. **GPT-5:** 5.75 (moderate)
4. **Claude 4.5:** 6.45 (finds dilemmas hardest)

**Speed:**
1. **Claude 4.5:** 13.8s avg (fastest)
2. **Gemini 2.5 Pro:** 22.2s avg
3. **GPT-5:** 55.1s avg
4. **Grok-4:** 69.0s avg (slowest, plus rate limiting)

**Reasoning Style:**
- **Claude 4.5:** Most verbose (109 words avg)
- **Grok-4:** Moderate (101 words)
- **GPT-5:** Concise (92 words)
- **Gemini 2.5 Pro:** Most concise (90 words)

### 2. Theory-Action Gap

**Overall:** 31.7% reversal rate (models change their choice when believing actions are real)

**By Model:**
1. **GPT-5:** 42.5% reversal rate (highest - most sensitive to action mode)
   - Confidence boost: +0.41 in action mode
   - Difficulty drop: -1.42
2. **Claude 4.5:** 31.5% reversal rate
   - Confidence boost: +0.19
   - Difficulty drop: -1.51
   - Shorter reasoning in action: -14 words
3. **Gemini 2.5 Pro:** 26.1% reversal rate
   - Confidence boost: +0.23
   - Difficulty drop: -2.58 (largest drop)
   - Much shorter reasoning: -31 words (largest drop)
4. **Grok-4:** 25.3% reversal rate (lowest - most consistent)
   - Confidence boost: +0.71 (largest boost)
   - Difficulty drop: -3.17 (extreme drop)
   - Actually LONGER reasoning: +2 words

**Key Insight:** All models find decisions easier in action mode (can drop difficulty by -3.17), but GPT-5 changes its choices most frequently (42.5% vs ~26% for Gemini/Grok-4).

### 3. Consensus Patterns

**Overall:** 59.4% consensus rate (all 4 models agree)

**By Mode:**
- **Theory mode:** 73.8% consensus (high agreement on hypotheticals)
- **Action mode:** 45.0% consensus (much more disagreement when "real")

**Interpretation:** Models agree much more when reasoning abstractly. When they believe actions are real, individual model differences emerge strongly.

### 4. Difficulty Calibration (Generator → Judges) ⚠️ MAJOR FINDING

**Correlation:** 0.065 (essentially zero)

**What We Tested:**
- **Generator:** Gemini 2.5 Flash was asked to create dilemmas at specific difficulty levels (1, 2, 3... up to 10)
- **Judges:** GPT-5, Claude 4.5, Gemini 2.5 Pro, and Grok-4 rated how difficult they found each dilemma
- **Question:** Does `difficulty_intended` (generator's target) predict `difficulty_perceived` (judges' ratings)?

**Result:** NO. Almost zero correlation (r=0.065).

**Judge Perception by Intended Difficulty:**
| Generator Asked For | Judges Actually Felt | Judge Confidence |
|---------------------|---------------------|------------------|
| Easy (1-3)          | 5.15 / 10           | 8.21             |
| Medium (4-6)        | 5.43 / 10           | 8.37             |
| Hard (7-10)         | 5.42 / 10           | 8.48             |

**Key Insight:** Judges rate **ALL** dilemmas as moderately difficult (~5-5.5 out of 10) regardless of what we asked the generator to create. The generator's "difficulty 1" dilemmas are just as hard as its "difficulty 10" dilemmas, according to judges.

**Three Possible Explanations:**
1. **Generator failure:** Gemini Flash cannot calibrate difficulty when generating dilemmas (it creates everything at medium difficulty regardless of target)
2. **Scale mismatch:** Generator and judges use fundamentally different internal difficulty scales (generator's "10" ≠ judge's "10")
3. **Judge compression:** All 4 judge models compress their difficulty ratings toward the mean (regression to middle, avoiding extremes)

**Implication for Benchmark Design:**
We **cannot** rely on a generator model to create dilemmas at target difficulty levels and expect other models to perceive them as intended. This is a fundamental challenge for LLM-generated benchmarks.

**Follow-up Question for Qualitative Analysis:**
Are the "difficulty 10" dilemmas actually more complex (more stakeholders, tighter constraints, deeper conflicts) but judges just don't find them harder to decide? Or did the generator genuinely fail to vary difficulty?

### 5. Choice Complexity

**Correlation with confidence:** 0.005 (negligible)
**Correlation with difficulty:** -0.041 (negligible)

**Interpretation:** Number of available choices (2, 3, or 4 options) has almost no effect on confidence or perceived difficulty.

### 6. Variable Impact (Bias Testing)

**Choice Diversity:** How much do variables change decisions?

**Top Models for Variation Sensitivity:**
1. **Grok-4:** 13.9% choice diversity in action, 12.9% in theory
2. **Gemini 2.5 Pro:** 13.6% action, 11.5% theory
3. **GPT-5:** 12.3% action, 12.2% theory
4. **Claude 4.5:** 10.1% action, 9.9% theory (least sensitive)

**High-Impact Dilemmas:**
- **Predictive Policing:** 50-75% choice diversity (variable substitutions heavily affect decisions)
- **Echo Chamber Recommender:** 50% diversity
- **Credit Scoring AI:** 50% diversity

**Interpretation:** Grok-4 and Gemini are most affected by variable changes (demographic info, amounts, roles). Claude 4.5 is most consistent across variations (potential bias insensitivity OR principled consistency).

---

## Next Steps

1. **Wait for experiment completion** (~500 judgements remaining)
2. **Re-run analysis** with full dataset
3. **Qualitative coding** (~30-40 hours):
   - 100 reversal cases (why did GPT-5 change its mind so often?)
   - High-variation dilemmas (what demographic cues triggered changes?)
   - Low-consensus cases (where models fundamentally disagree)
4. **Visualizations**
5. **Final findings.md**

---

## Preliminary Conclusions

1. **Gemini 2.5 Pro** is the most confident model, but also most variable
2. **Grok-4** finds everything easiest but is slowest
3. **GPT-5** is most sensitive to action mode (42.5% reversal)
4. **Claude 4.5** is least affected by variable changes (most consistent)
5. **Theory-action gap is real** (31.7% overall reversal, consensus drops from 74% to 45%)
6. **Generator-judge difficulty mismatch** (r=0.065) - judges don't perceive difficulty the way the generator intended
7. **Variable substitutions matter** for ~10-14% of decisions (potential bias vector)

The action mode effect is strong and consistent across all models. This validates the theory-action gap as a robust phenomenon worth deeper investigation.

The difficulty calibration finding is important for future benchmarks - we cannot rely on a generator model to create dilemmas at target difficulty levels. Judges will perceive them differently.
