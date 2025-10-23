# Research Notes

All experiments on LLM ethical decision-making.

---

## ✅ Completed Experiments

### [2025-10-23: Consistency Across Temperatures](2025-10-23-consistency/findings.md)
How consistent are LLM judgements at different temperatures?

**Finding:** Temp 1.0 more consistent than 0.0 (100% vs 98.3%)
**Data:** 240 judgements, 2 models, 4 temps, 3 dilemmas

---

## 🔜 Next Up

### VALUES.md System Prompt Test
Does providing a VALUES.md file change LLM decisions?

**Plan:** Test 3 conditions (no prompt / generic / custom VALUES.md)
**Why:** Core research question - validates the whole project premise
**Status:** Waiting for 10-dilemma test set

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
