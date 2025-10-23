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

---

## 🔜 Next Up

### Reasoning Analysis
Do LLMs actually reference VALUES.md principles in their reasoning?

**Plan:** Text analysis of reasoning from VALUES.md experiment
**Why:** Validate that framework shift is genuine reasoning, not random
**Status:** Ready - have 150 reasoning texts to analyze

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

1. Run your experiment (save experiment_id)
2. Export data:
   ```bash
   uv run python scripts/export_experiment_data.py <experiment_id> research/YYYY-MM-DD-name/data
   ```
3. Write `findings.md` with setup, results, key findings
4. Update this index

Each experiment folder is **self-contained** with:
- `findings.md` - Human summary
- `config.json` - Experiment metadata
- `dilemmas.json` - Full dilemmas used
- `judgements.json` - All judgements
- `data/*.csv` - Quick analysis files

**Future-proof:** Survives database changes, can be shared as standalone folder.
