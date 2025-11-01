# bench-1 Baseline Experiment: COMPLETE ✅

**Experiment ID:** `b191388e-3994-4ebd-96cc-af0d033c5230`
**Completion Date:** 2025-10-31
**Analysis Date:** 2025-11-01
**Enhancement Date:** 2025-11-01
**Status:** Publication-ready (quantitative complete, qualitative pending)

---

## Quick Stats

**Success Rate:** 99.95% (12,802 / 12,808 judgements)
**Models:** 4 frontier LLMs (GPT-5, Claude 4.5, Gemini 2.5 Pro, Grok-4)
**Dilemmas:** 20 from bench-1 collection
**Variations:** 1,601 configurations
**Modes:** Theory + Action
**Total Cost:** $366.21 ($0.029 per judgement)
**Total Runtime:** 54 hours (2.25 days)
**API Calls:** 31,238 (36.8% cache hit rate)

---

## Three Major Findings

### 1. Theory-Action Gap: 33.4% Reversal Rate

Models change their decisions when they believe actions are real:
- **GPT-5:** 42.5% (most sensitive)
- **Grok-4:** 33.5%
- **Claude 4.5:** 31.5%
- **Gemini 2.5 Pro:** 26.1%

### 2. Consensus Collapse: 71% → 43%

Agreement drops 27.9 percentage points when actions feel real:
- **Theory mode:** 70.9% consensus (hypothetical)
- **Action mode:** 43.0% consensus (perceived real)

### 3. Generator-Judge Mismatch: r=0.039

Judges don't perceive difficulty the way generator intended:
- Asked generator for difficulties 1-10
- Judges rated everything as ~5.2-5.4
- Fundamental challenge for LLM-generated benchmarks

---

## Key Files

### Documentation
- **[findings.md](findings.md)** - Complete analysis and implications (3,981 words, publication-ready)
  - Comprehensive YAML front matter with all metadata
  - 5 publication-quality figures (theory-action gap, consensus collapse, difficulty calibration, cost-performance, model signatures)
  - Rigorous limitations section (internal, external, construct, statistical validity)
  - Exact model versions from OpenRouter
  - Acknowledgment of Gemini 2.5 Flash generator with v8_concise prompt
  - Strengthened conclusion with "So What?" framing
  - Key quotes for citation
- **[ANALYSIS_PLAN.md](ANALYSIS_PLAN.md)** - Analysis methodology and plan
- **[DESIGN.md](DESIGN.md)** - Experiment design rationale
- **[README.md](README.md)** - Quick reference guide
- **[PRELIMINARY_FINDINGS.md](PRELIMINARY_FINDINGS.md)** - 96% preliminary results (archived)

### Data
- **judgements.json** - All 12,802 judgements with full reasoning (34 MB)
- **dilemmas.json** - All 20 dilemmas with metadata (91 KB)
- **config.json** - Experiment configuration
- **experiment.log** - Complete execution log

### Analysis Outputs
- **output/** - All CSV/JSON analysis results
  - **Figures (output/figures/):**
    - `fig1_theory_action_gap.png` - Reversal rates by model (horizontal bar chart)
    - `fig2_consensus_collapse.png` - Theory vs action consensus (before/after + arrow)
    - `fig3_difficulty_calibration.png` - Generator-judge mismatch scatter (r=0.039)
    - `fig4_cost_performance.png` - Cost vs variable sensitivity (quadrant analysis)
    - `fig5_model_signatures.png` - 5D radar chart (confidence, speed, cost, sensitivity, consistency)
  - **Data Tables:**
    - `model_comparison.csv` - Confidence, difficulty, speed by model
    - `theory_action_paired.csv` - All paired theory/action judgements
    - `theory_action_gap_by_model.csv` - Reversal rates and shifts
    - `samples_reversals.csv` - 100 cases for qualitative coding
    - `consensus_by_configuration.csv` - Agreement patterns
    - `variation_effects_by_model.csv` - Bias sensitivity
    - And 6 more analysis files
  - **Cost Analysis:**
    - `cost_analysis.json` - Complete OpenRouter cost breakdown

---

## Next Steps

### Immediate
- ✅ Experiment complete
- ✅ Data exported
- ✅ Quantitative analysis complete
- ✅ Findings documented

### Near-Term: Qualitative Analysis (~30-40 hours)

1. **Theory-Action Reversals** - Code 100 sampled cases
   - Why did GPT-5 reverse 42.5% of the time?
   - What patterns distinguish consistency from reversals?

2. **High-Variation Dilemmas** - Analyze demographic sensitivity
   - Appropriate context-awareness or problematic bias?
   - What demographic cues trigger changes?

3. **Difficulty Calibration** - Compare intended vs perceived
   - Are "difficulty 10" dilemmas structurally more complex?
   - Did generator fail or do judges compress ratings?

4. **Consensus Breakdown** - Low-consensus cases
   - Where do models fundamentally disagree?
   - What ethical frameworks emerge?

### Medium-Term: Follow-up Experiments

1. **Bias Under Pressure** - Test high-variation dilemmas with modifiers
2. **Human Baseline** - Compare LLM to human judgements
3. **Temperature Effects** - Test theory-action gap at 0.0, 0.5, 1.0, 1.5
4. **Generator Comparison** - Test if other models calibrate better

---

## Impact & Implications

### For AI Safety
- Evaluation benchmarks (theory mode) may not predict production behavior (action mode)
- 33.4% reversal rate means 1 in 3 decisions change when stakes feel real
- Model selection matters much more in production than evaluations suggest

### For Benchmark Design
- Cannot rely on generator models to create content at target difficulty
- r=0.039 correlation reveals fundamental validity challenge
- May need human calibration or iterative refinement

### For Bias Testing
- High-variation dilemmas identified (Predictive Policing: 50-75% diversity)
- Different models show different sensitivity (Claude: 10%, Grok: 14%)
- Clear signal for demographic bias audits

---

## Data Availability

**Location:** `/Users/gs/dev/values.md/dilemmas/research/2025-10-29-bench1-baseline/`

**Export Command:**
```bash
uv run python ../../scripts/export_experiment_data.py b191388e-3994-4ebd-96cc-af0d033c5230 .
```

**Analysis Command:**
```bash
uv run python analyze.py
```

---

## Citation

If using this data or findings:

```
bench-1 Baseline Experiment (2025)
Systematic LLM Ethical Decision-Making Baseline
12,802 judgements across 4 models, 20 dilemmas, theory + action modes
Experiment ID: b191388e-3994-4ebd-96cc-af0d033c5230
```

**Key Finding:** Theory-action gap is real (33.4% reversal), varies by model, and has major implications for AI safety evaluation methodology.
