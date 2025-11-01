# bench-1 Baseline Experiment - Status Report

**Final Update:** 2025-11-01
**Experiment ID:** `b191388e-3994-4ebd-96cc-af0d033c5230`

## Final Status: ✅ COMPLETE

### Experiment Completion
- **Completion:** 12,802 / 12,808 judgements (99.95%)
- **Failures:** 6 (0.05%)
- **Completion date:** 2025-10-31
- **Total runtime:** ~3 days (2025-10-29 to 2025-10-31)

### Model Performance
All 4 models running:
- **GPT-5** (openai/gpt-5): Completing successfully
- **Claude 4.5** (anthropic/claude-sonnet-4.5): 5 failures (action mode "did not call any tool")
- **Gemini 2.5 Pro** (google/gemini-2.5-pro): Completing successfully
- **Grok-4** (x-ai/grok-4): Multiple rate limit warnings (50 req/min), some JSON parsing errors

### Known Issues
1. **Grok-4 rate limiting:** Hitting 50 requests/minute limit frequently, causing retries
2. **Claude 4.5 action mode:** 5 cases where agent didn't call any tool (exhausted all 3 retries)
3. **Grok-4 JSON parsing:** Occasional malformed JSON responses
4. **Total failures:** ~10 judgements failed after 3 retries (acceptable <0.1% failure rate)

## Analysis Preparation Complete ✓

### Documentation
- ✓ `ANALYSIS_PLAN.md` - Comprehensive 3-tier analysis strategy with qualitative workflow
- ✓ `DESIGN.md` - Experiment design rationale and methodological constraints
- ✓ `README.md` - Experiment overview and quick facts

### Analysis Script
- ✓ `analyze.py` - Complete quantitative analysis implementation

**Implemented analyses:**

**Tier 1: Model Comparison (Variation-Weighted)**
1. Consensus and decisiveness rates across models
2. Model confidence and perceived difficulty
3. Theory-action gap (reversals, confidence shifts)
4. Model behavioral signatures (choice distributions, failure rates)

**Tier 2: Cross-Dilemma Patterns (Dilemma-Weighted)**
1. Difficulty effects (human vs model ratings, correlation)
2. Choice complexity effects (how # of choices affects confidence/difficulty)
3. Variable effects (how variations impact choice diversity)

**Outputs:**
- CSV files for all metrics (`output/`)
- Sample exports for qualitative analysis (`samples_reversals.csv`)
- Model comparison tables
- Theory-action paired data

### Data Requirements
The analysis script expects data exported via:
```bash
uv run python ../../scripts/export_experiment_data.py b191388e-3994-4ebd-96cc-af0d033c5230 data/
```

This will create:
- `data/judgements.json` - All 12,808 judgements with full context
- `data/dilemmas.json` - All 20 dilemmas from bench-1

## Next Steps (Once Experiment Completes)

### 1. Export Data
```bash
cd research/2025-10-29-bench1-baseline
uv run python ../../scripts/export_experiment_data.py b191388e-3994-4ebd-96cc-af0d033c5230 data/
```

### 2. Run Quantitative Analysis
```bash
uv run python analyze.py
```

Expected outputs in `output/`:
- `consensus_by_configuration.csv`
- `model_comparison.csv`
- `model_comparison_by_mode.csv`
- `theory_action_paired.csv`
- `theory_action_gap_by_model.csv`
- `model_signatures.json`
- `difficulty_analysis.csv`
- `choice_complexity_analysis.csv`
- `variation_effects_by_dilemma.csv`
- `variation_effects_by_model.csv`
- `samples_reversals.csv` (for qualitative coding)

### 3. Qualitative Analysis (~30-40 hours)
See ANALYSIS_PLAN.md for detailed coding schemes:
1. Theory-action reversals (100 cases)
2. Disagreement cases (100 cases)
3. Bias detection (100 cases per variable type)
4. High-confidence errors (all cases, estimated 50-200)
5. Extreme difficulty responses (50-100 cases)

### 4. Create Visualizations
Planned figures:
- Model comparison heatmaps (consensus, confidence, theory-action gap)
- Difficulty correlation scatter plots
- Choice distribution by model
- Theory-action gap by dilemma

### 5. Write Findings
Integrate quantitative and qualitative insights into `findings.md`

### 6. Sync to Production Database
After local analysis is complete and validated:
```bash
# Inspect production database
uv run python ../../scripts/inspect_prod_db.py

# Reset production judgements (keeps dilemmas)
uv run python ../../scripts/reset_prod_judgements.py --confirm

# Sync clean data
uv run python ../../scripts/sync_dilemmas_to_prod.py
uv run python ../../scripts/sync_judgements_to_prod.py --only-with-dilemmas
```

## UUID Collision Resolution ✓

**Issue:** Original experiment UUID `b191388e-3994-4ebd-96cc-af0d033c5230` was accidentally reused from 2025-10-24 experiment

**Resolution (Completed 2025-10-31):**
- ✓ Migrated 384 old judgements to new UUID: `c0ecd87e-7adc-4a9b-8466-0edda52235be`
- ✓ Updated all documentation in `research/2025-10-24-bias-under-pressure/`
- ✓ Updated `judgements.json` (384 occurrences replaced)
- ✓ Local database now clean (11,772 bench-1 baseline only)

Production database still has collision - will be resolved via reset/resync workflow above.

## Timeline Estimate

**Experiment completion:** Tonight (few hours)
**Data export:** 5 minutes
**Quantitative analysis:** 2-3 hours
**Qualitative analysis:** 30-40 hours (over multiple days)
**Visualization:** 2-3 hours
**Writing findings:** 5-8 hours

**Total:** ~42-53 hours of analysis work after experiment completes
