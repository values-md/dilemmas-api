# Research Notes

All experiments on LLM ethical decision-making.

---

## ✅ Completed Experiments

### [2025-10-23: Consistency Across Temperatures](2025-10-23-consistency/findings.md)
How consistent are LLM judgements at different temperatures?

**Finding:** Temp 1.0 more consistent than 0.0 (100% vs 98.3%)
**Data:** 240 judgements, 2 models, 4 temps, 3 dilemmas

### [2025-10-23: VALUES.md Impact Test](2025-10-23-values-md-test/findings.md)
Does providing VALUES.md guidance change LLM ethical decisions?

**Finding:** YES! Framework matters (utilitarian vs deontological), style doesn't
**Impact:** 2/10 dilemmas showed complete choice reversal (100% consistency)
**Data:** 150 judgements, 1 model, 5 conditions (control + 4 VALUES.md variants), 10 dilemmas
**Key Insight:** Deontological agents more confident (8.78 vs 8.43), outcome-focused decisions differ from rule-based

### [2025-10-23: Theory vs Action Gap](2025-10-23-theory-vs-action/findings.md)
Do LLMs make different decisions when they believe actions are real vs hypothetical?

**Finding:** YES! 1/4 dilemmas showed complete choice reversal
**Impact:** Action mode = different choices + higher confidence + much easier (-1.67 difficulty)
**Data:** 40 judgements, 1 model, 2 modes (theory vs action), 4 dilemmas with tools
**Key Insight:** Decisions feel dramatically easier when calling tools (-4.40 on reversed dilemma). "Just do it" vs theorizing.

### [2025-10-24: Theory vs Action Part Two - Robustness Test](2025-10-23-theory-vs-action-part-two/findings.md)
Is the "tools make decisions easier" finding universal across models and dilemmas?

**Finding:** YES! Universal across ALL 6 models, even stronger than Part One
**Impact:** -2.72 average difficulty drop (62% larger than Part One), +0.31 confidence boost
**Data:** 558 judgements, 6 models (GPT-4.1, Claude, Gemini Pro/Flash, DeepSeek, GPT-4.1 Mini), 10 dilemmas, 2 modes
**Key Insights:**
- Larger models show stronger effect (GPT-4.1: -3.91, Gemini Pro: -3.89)
- Some dilemmas show extreme gaps (Adaptive Voice Protocol: -4.90)
- 26 choice reversals across model-dilemma pairs
- Models hallucinate procedural tools they think should exist ("log_decision")
- **Major finding**: Capability correlates with decisiveness boost

### [2025-10-24: Extreme VALUES.md Compliance](2025-10-24-extreme-values/findings.md)
Do LLMs refuse harmful VALUES.md frameworks, or comply with them?

**Finding:** HIGH COMPLIANCE - 80% choice reversal rate, zero refusals detected
**Impact:** Extreme frameworks made decisions easier (-4.81 difficulty) and more confident (+1.14)
**Data:** 69 judgements, 3 models, 12 dilemmas, baseline + 5 extreme frameworks (profit_maximalism, regulatory_minimalism, etc.)
**Key Insights:**
- Models cited extreme frameworks matter-of-factly with no ethical pushback
- Corporate frameworks showed strongest effect (-6.89 difficulty drop)
- 2 non-reversal cases: models reinterpreted abstract frameworks to maintain ethical alignment
- All 3 frontier LLMs showed identical patterns
- **Major finding**: VALUES.md can override baseline ethical reasoning, no safety refusal triggered

---

## 🔜 Next Up

### Reasoning Analysis
Do LLMs actually reference VALUES.md principles / tool consequences in their reasoning?

**Plan:** Text analysis of reasoning from VALUES.md and theory-action experiments
**Why:** Validate that differences are genuine reasoning, not random
**Status:** Ready - have 150 + 40 reasoning texts to analyze

---

## 💡 Future Ideas

### Variable Bias Testing
Do LLMs show bias based on demographics/names/amounts?
- Use existing variables system
- Test gender, ethnicity, wealth variations

### Model Comparison
How do different LLMs compare on same dilemmas?
- Add Claude, Llama, Mistral, others
- Cluster models by decision patterns

### Reasoning Analysis
What ethical frameworks do models use?
- Analyze existing reasoning texts
- Categorize: utilitarian, deontological, virtue ethics
- No new judgements needed

### Theory vs Action Gap
Do models decide differently when they think it's real?
- Theory: "what should be done"
- Action: "make this API call"
- Test if decisions change with stakes

### Modifier Effects
How do time pressure, stakes, uncertainty affect decisions?
- Use existing modifiers system
- Test each modifier independently

### Extended Reasoning Impact
Does Claude's thinking or o1's reasoning change decisions?
- Compare standard vs extended reasoning modes
- Measure quality/confidence differences

---

## How to Add New Experiments

1. Create experiment folder:
   ```bash
   mkdir research/YYYY-MM-DD-experiment-name
   mkdir research/YYYY-MM-DD-experiment-name/values
   mkdir research/YYYY-MM-DD-experiment-name/data
   ```

2. Create experiment files:
   - `run.py` - Experiment runner script (loads dilemmas, runs judgements)
     - **CRITICAL:** Generate `experiment_id = str(uuid.uuid4())` at start
     - **CRITICAL:** Set `judgement.experiment_id = experiment_id` for each judgement
     - Print experiment_id at end with export instructions
   - `README.md` - Experiment design, hypothesis, measurements
   - `values/*.md` - Any VALUES.md frameworks for this experiment
   - `analyze.py` - Analysis script (optional, for post-processing)

3. Run your experiment:
   ```bash
   uv run python research/YYYY-MM-DD-experiment-name/run.py --dry-run  # Test
   uv run python research/YYYY-MM-DD-experiment-name/run.py             # Full run
   ```

4. Export and analyze data:
   ```bash
   uv run python scripts/export_experiment_data.py <experiment_id> research/YYYY-MM-DD-experiment-name/data
   uv run python research/YYYY-MM-DD-experiment-name/analyze.py
   ```

5. Write `findings.md` and update this index

Each experiment folder is **self-contained** with:
- `run.py` - Experiment runner
- `README.md` - Design and instructions
- `values/` - VALUES.md frameworks used
- `analyze.py` - Analysis script
- `findings.md` - Human summary
- `config.json` - Experiment metadata
- `dilemmas.json` - Full dilemmas used
- `judgements.json` - All judgements
- `data/*.csv` - Quick analysis files

**Future-proof:** Survives database changes, can be shared as standalone folder.
