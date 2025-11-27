---
# Core Metadata
title: "Consistency Across Temperature Settings"
slug: "2025-10-23-consistency"
date: 2025-10-23
status: completed
experiment_id: "c588a9e9-2b3d-486d-ac8b-16e2498d6e08"

# Research Summary
research_question: "How consistent are LLM judgements across different temperature settings?"

abstract: |
  We tested whether LLM temperature affects ethical decision consistency by evaluating two models (GPT-4.1 Mini, Gemini 2.5 Flash) at four temperatures (0.0, 0.5, 1.0, 1.5) across three ethical dilemmas with 10 repetitions per condition (240 total judgements). Unexpectedly, temperature 1.0 showed perfect choice consistency (100%), higher than the supposedly deterministic temperature 0.0 (98.3%). Confidence variation was highest at temperature 0.0 despite being deterministic. These findings challenge common assumptions about temperature's role in LLM decision-making and suggest that ethical dilemmas may have strong "attractor" solutions that dominate regardless of sampling temperature.

key_finding: "Temperature 1.0 shows higher consistency (100%) than temperature 0.0 (98.3%)"

# Experiment Parameters
models:
  - GPT-4.1 Mini
  - Gemini 2.5 Flash

data:
  dilemmas: 3
  judgements: 240
  conditions: 4

tags:
  - consistency
  - temperature
  - methodology
  - model-comparison
---

# Consistency Across Temperature Settings

## Background

Temperature is a fundamental parameter in LLM sampling that controls output diversity. Conventional wisdom holds that temperature 0.0 produces deterministic outputs while higher temperatures introduce randomness. This assumption underlies many LLM applications, including ethical decision-making systems.

However, ethical dilemmas may behave differently than typical text generation tasks. If certain ethical choices represent strong "attractor" states in the model's representation space, temperature might have less effect than expected. This experiment tests whether temperature systematically affects consistency in ethical decision-making.

## Methodology

### Experimental Design

- **Design**: Between-subjects design with temperature as independent variable
- **Sample**: 240 judgements (2 models × 4 temperatures × 3 dilemmas × 10 repetitions)
- **Temperature Levels**: 0.0 (deterministic), 0.5 (balanced), 1.0 (default), 1.5 (creative)
- **Models**: GPT-4.1 Mini, Gemini 2.5 Flash
- **Repetitions**: 10 per condition for statistical reliability

### Materials

**Dilemmas**: Three diverse ethical scenarios selected for:
- Clear choices (2-4 options per dilemma)
- Genuine ethical tension (no obviously correct answer)
- Different domains (to test generalizability)

**Measurements**:
- Choice ID (primary outcome - which option selected)
- Confidence (0-10 scale)
- Reasoning text (for qualitative analysis)

### Procedure

For each model-temperature-dilemma combination:
1. Present dilemma in theory mode (hypothetical reasoning)
2. Request structured output (choice + confidence + reasoning)
3. Repeat 10 times to measure consistency
4. Analyze choice distribution and confidence variation

## Results

### Primary Finding: Temperature 1.0 Most Consistent

| Temperature | Choice Consistency | Confidence StdDev | Reasoning Similarity |
|-------------|-------------------:|------------------:|---------------------:|
| 0.0         | 98.3%             | 1.02              | 23.3%                |
| 0.5         | 95.0%             | 0.54              | 24.0%                |
| **1.0**     | **100.0%**        | **0.21**          | 25.1%                |
| 1.5         | 98.3%             | 0.54              | 24.4%                |

**Choice Consistency**: Percentage of repetitions that selected the modal (most common) choice.

**Confidence StdDev**: Standard deviation of confidence scores (lower = more stable).

### Key Observations

#### 1. Temperature 0.0 Is Not Perfectly Deterministic

With 98.3% consistency, temperature 0.0 produced non-identical outputs in 2% of cases. This contradicts the assumption of complete determinism at zero temperature.

**Possible explanations**:
- Floating-point precision in sampling
- Internal randomness in attention mechanisms
- Non-deterministic GPU operations
- API-level variability (OpenRouter implementation)

#### 2. Temperature 1.0 Shows Paradoxically Higher Consistency

The default temperature (1.0) achieved perfect 100% choice consistency, exceeding the supposedly deterministic temperature 0.0.

**Possible explanations**:
- **Attractor hypothesis**: Ethical dilemmas have strong solution attractors that dominate sampling
- **Structured output effect**: JSON schema constraints may reduce temperature's influence
- **Sample size artifact**: Only 3 dilemmas may not represent broader behavior
- **Optimal exploration-exploitation**: Temperature 1.0 may hit the sweet spot for ethical reasoning

#### 3. Confidence Most Stable at Temperature 1.0

Despite higher temperature, confidence variation was **lowest** at temperature 1.0 (StdDev = 0.21) and **highest** at temperature 0.0 (StdDev = 1.02).

This suggests that confidence calibration in ethical reasoning may be most stable at default temperature settings, where models are trained to perform.

#### 4. Reasoning Diversity High Regardless of Temperature

Reasoning similarity remained low (20-27% Jaccard similarity) across all temperature settings. Models generated genuinely different reasoning texts even when reaching identical conclusions.

**Implication**: Same ethical choice, multiple justification paths. This aligns with moral psychology findings that humans post-hoc rationalize intuitive moral judgements.

### Model Differences

- **GPT-4.1 Mini**: More consistent overall, less sensitive to temperature
- **Gemini 2.5 Flash**: More variation at temperature 0.0, suggesting architectural differences in determinism implementation

## Discussion

### Why Is Temperature 1.0 Most Consistent?

**Hypothesis 1: Training Distribution Alignment**
Models are trained and evaluated at temperature 1.0. Ethical reasoning capabilities may be optimized for this setting, with lower temperatures creating "overly cautious" sampling that introduces instability.

**Hypothesis 2: Ethical Attractor States**
Certain ethical choices may represent strong attractors in the model's probability space. When these attractors are sufficiently strong, temperature has minimal effect on final choice, but temperature 1.0 provides the optimal exploration to reliably find them.

**Hypothesis 3: Structured Output Constraints**
JSON schema requirements (fixed choice options) may constrain the output space enough that temperature's effect is minimized, with temperature 1.0 hitting the sweet spot between constraint satisfaction and natural sampling.

### Limitations

1. **Small sample**: Only 3 dilemmas tested
   - May not generalize to all ethical scenarios
   - Need replication with 20-30 dilemmas

2. **Specific models**: Only tested GPT-4.1 Mini and Gemini 2.5 Flash
   - Other models may show different patterns
   - Larger models (GPT-4.1, Claude Sonnet 4.5) may behave differently

3. **Theory mode only**: Did not test action mode (tool calling)
   - Temperature effects may differ when models believe actions are real

4. **Single domain**: Ethical dilemmas only
   - Results may not apply to other structured output tasks

5. **API variability**: OpenRouter may introduce additional sources of variation
   - Direct API access might show different patterns

## Implications

### For Experimental Design

**Recommendation**: Use temperature 1.0 for ethical decision studies requiring consistency, not temperature 0.0.

If using temperature 0.0, do not assume perfect determinism. Run multiple repetitions and check for variation.

### For Production Systems

Systems requiring highly consistent ethical decisions should consider:
- Temperature 1.0 as default (not 0.0)
- Multiple samples with majority voting if perfect consistency is critical
- Monitoring for non-determinism even at temperature 0.0

### For LLM Evaluation

Temperature 0.0 may not be the appropriate "deterministic baseline" for ethical reasoning benchmarks. Consider temperature 1.0 as the reference condition since it produces both high consistency and stable confidence.

## Future Directions

1. **Larger sample**: Test with 30+ dilemmas to confirm pattern
   - If temperature 1.0 remains most consistent, this finding is robust
   - If pattern disappears, it was an artifact of these 3 dilemmas

2. **Model spectrum**: Test across model sizes and families
   - Hypothesis: Larger models show stronger attractor effects
   - Test: GPT-4.1, Claude Opus, Llama 70B+

3. **Action mode**: Does temperature affect tool-calling consistency differently?
   - Theory mode vs action mode × temperature interaction

4. **Domain generalization**: Test non-ethical structured output tasks
   - Are medical diagnoses, legal analyses similarly affected?

5. **Confidence calibration**: Why is confidence most stable at temperature 1.0?
   - Investigate relationship between sampling temperature and uncertainty estimation

---

**Last Updated**: 2025-10-23
