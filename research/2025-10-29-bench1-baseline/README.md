# bench-1 Baseline: Systematic LLM Behavior Mapping

**Date:** 2025-10-29

**Status:** Ready to run

---

## Research Question

**What is the natural ethical decision-making behavior of major LLMs across a comprehensive set of dilemmas and demographic variations?**

This experiment establishes a foundational baseline for:
1. Understanding how different LLMs make ethical decisions naturally (without VALUES.md guidance)
2. Comparing human judgements to LLM behavior (for "which LLM are you most like?" features)
3. Testing bias patterns across demographic variables (names, identities, contexts)
4. Comparing theory mode (hypothetical reasoning) vs action mode (tool-calling behavior)

---

## Experimental Design

### Models (4 flagship LLMs)
1. **openai/gpt-5** - OpenAI's latest flagship
2. **anthropic/claude-sonnet-4.5** - Anthropic's latest with extended reasoning
3. **google/gemini-2.5-pro** - Google's most capable model
4. **x-ai/grok-4** - xAI's flagship model

### Configuration
- **Temperature:** 1.0 (standard, natural behavior)
- **Modes:** Theory AND Action (compare hypothetical reasoning vs tool-calling)
- **Modifiers:** None (no time pressure, no stakes manipulation)
- **VALUES.md:** None (baseline natural behavior)
- **Repetitions:** 1 (single pass - we know from prior experiments that models are consistent)

### Dilemmas
- **Source:** bench-1 collection (20 curated ethical dilemmas)
- **Variables:** ALL systematic combinations
  - Each dilemma has 1-4 variables (names, demographics, contexts, amounts)
  - Total unique variations: **1,601 combinations**
  - Examples:
    - "Unsanctioned Surgery": 256 combinations (4 variables × 4 options each)
    - "Predictive Policing": 4 combinations (1 variable × 4 options)
    - See full breakdown in this README below

### Total Scope
- **Total judgements:** 12,808
  - 4 models × 1,601 variations × 2 modes
- **Estimated cost:** ~$62
  - GPT-5: $13.61
  - Claude Sonnet 4.5: $18.85
  - Gemini 2.5 Pro: $6.80
  - Grok 4: $23.01
- **Estimated time:** ~14 hours (with 5 concurrent requests)
  - Sequential: ~71 hours
  - With parallelization: ~14 hours

---

## Variable Combinations Breakdown

Each dilemma has variables that create multiple variations for bias testing:

| Dilemma | Variables | Combinations |
|---------|-----------|--------------|
| Public Services Prioritization | 2 | 16 |
| Welfare Database Access | 2 | 16 |
| Union Newsletter | 4 | 192 |
| Genetic Counseling | 2 | 8 |
| Species Tracker | 4 | 81 |
| Predictive Policing | 1 | 4 |
| Pricing Optimizer | 4 | 108 |
| Interpreter's Dilemma | 3 | 64 |
| Fitness Tracker | 2 | 16 |
| Conflicting Data | 1 | 4 |
| Autonomous Vehicle | 4 | 256 |
| Refugee Hiring | 2 | 16 |
| Species Tracker Disclosure | 2 | 12 |
| Algorithm Audit | 2 | 16 |
| Language Coach | 4 | 256 |
| Credit Scoring | 1 | 4 |
| Echo Chamber | 1 | 4 |
| Unattributed Art | 2 | 16 |
| Unsanctioned Surgery | 4 | 256 |
| Transparent Mind | 4 | 256 |
| **TOTAL** | - | **1,601** |

---

## Hypotheses

### H1: Model Differences
Different LLMs will show distinct ethical decision-making patterns:
- Choice preferences (which options they favor)
- Confidence levels
- Reasoning styles
- Difficulty perceptions

### H2: Theory vs Action Gap
Models will make different decisions in action mode vs theory mode:
- Action mode: more decisive, higher confidence, lower perceived difficulty
- Based on prior research showing -2.72 average difficulty drop in action mode

### H3: Demographic Bias
Models will show bias patterns based on variable substitutions:
- Names (gender, ethnicity)
- Demographics (age, income, status)
- Contexts (institutions, locations)

### H4: Model-Specific Bias Signatures
Each model will have distinct bias patterns:
- Based on prior research showing 2.5× bias range across models
- Gemini showed highest baseline bias (31.2%) in pressure experiments
- Claude showed pressure-activated bias (0% baseline → 25% under stakes)

---

## Technical Implementation

### Failsafes for Overnight Run

1. **Save after each judgement** - Immediate DB write (no batch commits)
2. **Resume capability** - Track completed (model, dilemma, variation, mode) tuples
3. **Skip on resume** - Query existing judgements on startup, skip completed
4. **Error handling** - Catch API failures, retry 3× with exponential backoff (2s, 4s, 8s)
5. **Rate limiting** - 5 concurrent requests (conservative, can increase to 10-15)
6. **Graceful shutdown** - Handle Ctrl+C, save progress
7. **Progress checkpoints** - Log every 50 judgements
8. **Failure logging** - Record all failures for post-run analysis

### Rate Limits (OpenRouter)
- **Paid models:** N RPS for $N balance (we have ~62 RPS available)
- **Practical limit:** Response time (~20 sec avg) not rate limits
- **Strategy:** 5 concurrent requests (well below limits)
- **429 handling:** Exponential backoff retry

### Resume Logic
```python
# On startup:
1. Query all judgements for this experiment_id
2. Build set of completed: (model_id, dilemma_id, variation_key, mode)
3. Skip those when iterating through experiment plan
4. Continue from where we left off
```

---

## Measurements

For each judgement, we capture:

**Common fields:**
- `choice_id` - Which option was selected
- `confidence` - Self-reported confidence (0-10)
- `perceived_difficulty` - How hard the decision felt (0-10)
- `reasoning` - LLM's explanation
- `response_time_ms` - API latency
- `rendered_situation` - Actual text shown (with variables filled)
- `variable_values` - Specific variables used
- `variation_key` - Hash for grouping identical variations

**AI-specific fields:**
- `model_id` - Which LLM
- `temperature` - Model setting (1.0 for all)
- `mode` - Theory or action
- `tool_calls` - Tool calls made (action mode only)
- `tokens_used` - Token count

**Experiment metadata:**
- `experiment_id` - Links to this experiment
- `experiment_metadata` - Custom fields (condition, etc.)

---

## Analysis Plan

After data collection:

### 1. Model Comparison
- Choice distribution by model
- Confidence levels by model
- Difficulty perception by model
- Reasoning style analysis

### 2. Theory vs Action Gap
- Choice reversals (same variation, different modes)
- Confidence differences
- Difficulty differences
- Tool calling patterns

### 3. Bias Detection
- Choice differences by demographic variables
- Statistical significance testing
- Bias magnitude by model
- Bias consistency across dilemmas

### 4. Human Comparison Baseline
- Create model "profiles" for human matching
- "You think most like [MODEL]" features
- Similarity scoring algorithms

---

## Running the Experiment

**Experiment ID:** `b191388e-3994-4ebd-96cc-af0d033c5230`

This ID is hardcoded in `run.py` and persists across runs for auto-resume.

```bash
# Navigate to research folder
cd research/2025-10-29-bench1-baseline

# Test run (dry-run mode)
uv run python run.py --dry-run

# Full run (overnight)
./start.sh
# PID and log file will be shown

# Monitor progress
tail -f experiment.log

# Check progress
uv run python check_progress.py

# Query judgements directly
sqlite3 ../../data/dilemmas.db "SELECT COUNT(*) FROM judgements WHERE experiment_id = 'b191388e-3994-4ebd-96cc-af0d033c5230'"

# Resume if interrupted
uv run python run.py  # Automatically resumes from last checkpoint
```

---

## Expected Outputs

After completion:

### Database Records
- 12,808 judgements in `judgements` table
- All linked via `experiment_id`

### Data Export
```bash
uv run python ../../scripts/export_experiment_data.py <experiment_id> data/
```

Creates:
- `judgements.json` - All judgements
- `dilemmas.json` - All dilemmas used
- `config.json` - Experiment metadata
- `data/*.csv` - Quick analysis files

### Analysis
```bash
uv run python analyze.py
```

Generates:
- Model comparison tables
- Theory vs action analysis
- Bias detection results
- Visualizations
- `findings.md` - Summary report

---

## Related Experiments

**Prerequisites:**
- bench-1 collection generated ✅

**Follow-up experiments:**
- VALUES.md impact on bench-1
- Variable bias deep-dive (focused on specific demographics)
- Extended reasoning impact (Claude thinking, etc.)
- Temperature variations on bench-1

---

## Notes

- **Why systematic (all variations)?**
  - Comprehensive bias testing
  - Human comparison baseline needs breadth
  - Future-proof: can answer any variable-related question
  - Cost ($62) and time (14 hours) are acceptable

- **Why no repetitions?**
  - Prior experiments showed high consistency (98-100%)
  - Single pass captures breadth over depth
  - Save budget for other experiments

- **Why these 4 models?**
  - Flagship models from major labs
  - Representative of what humans interact with
  - Good coverage of reasoning capabilities

---

## Contact

Questions? See `research/GUIDE.md` or experiment runner comments.
