# When Agents Act: LLM Ethical Decision-Making Dataset

**A systematic study of the evaluation-deployment gap in large language models**

## 🔍 Overview

This dataset contains 12,802 ethical decision judgements from four frontier LLMs (GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro, Grok-4) across 20 AI-relevant ethical dilemmas with 1,601 variable configurations.

**Key Finding:** Models reverse their ethical decisions **33.4%** of the time when transitioning from theory mode (hypothetical reasoning) to action mode (believing actions are real).

## 📊 Dataset Statistics

- **Dilemmas:** 20 AI-relevant ethical scenarios
- **Judgements:** 12,802 complete decision records
- **Models:** 4 (GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro, Grok-4)
- **Modes:** Theory (hypothetical reasoning) + Action (tool-enabled agents)
- **Variations:** 1,601 unique configurations (demographic/contextual variables)
- **Date:** October-November 2025

## 📁 Files

### Core Data
- **`dilemmas.json`** (132 KB) - 20 ethical dilemmas with full metadata, variables, choices, tools
- **`judgements.json`** (34 MB) - Complete 12,802 judgements with full reasoning traces
- **`dilemmas_flat.csv`** - Flattened dilemma data for easy exploration
- **`judgements_flat.csv`** - Flattened judgement data with key fields

### Analysis Files
- **`theory_action_paired.csv`** (27 MB) - Side-by-side comparison of theory vs action mode decisions
- **`consensus_by_configuration.csv`** - Model agreement patterns across configurations
- **`reversals_sample.csv`** - Examples of decision reversals with full reasoning
- **`difficulty_analysis.csv`** - Intended vs perceived difficulty comparison

### Documentation
- **`CODEBOOK.md`** - Field descriptions and data dictionary
- **`findings.md`** - Full research article with methodology and findings
- **`config.json`** - Experiment configuration
- **`LICENSE.txt`** - CC0 1.0 Public Domain Dedication

## 🚀 Quick Start

### Python
```python
import pandas as pd
import json

# Load flattened data
dilemmas = pd.read_csv('dilemmas_flat.csv')
judgements = pd.read_csv('judgements_flat.csv')

# Or load full JSON
with open('judgements.json') as f:
    judgements_full = json.load(f)

# Example: Find decision reversals
theory_action = pd.read_csv('theory_action_paired.csv')
reversals = theory_action[theory_action['choice_id_theory'] != theory_action['choice_id_action']]
print(f"Decision reversals: {len(reversals)} ({len(reversals)/len(theory_action)*100:.1f}%)")
```

### R
```r
library(jsonlite)
library(dplyr)

# Load data
dilemmas <- read.csv('dilemmas_flat.csv')
judgements <- read.csv('judgements_flat.csv')

# Find reversals by model
theory_action <- read.csv('theory_action_paired.csv')
reversals <- theory_action %>%
  filter(choice_id_theory != choice_id_action) %>%
  group_by(model_id) %>%
  summarise(reversal_rate = n() / nrow(theory_action))
```

## 🎯 Research Questions

1. **Evaluation-Deployment Gap:** Do LLMs make different ethical decisions when they believe actions have real consequences?
2. **Cross-Model Variation:** How does the gap vary across models?
3. **Consensus Stability:** Does model consensus remain stable across modes?
4. **Demographic Sensitivity:** Are models more/less sensitive to demographic variables in action mode?
5. **Benchmark Validity:** Can generator models create content at targeted difficulty levels?

## 🔬 Key Findings

### 1. Theory-Action Gap (33.4%)
Models frequently reverse decisions when transitioning from hypothetical reasoning to perceived real action:
- **GPT-5:** 42.5% reversal rate (highest)
- **Gemini 2.5 Pro:** 26.1% (lowest)
- **Claude 4.5 Sonnet:** 32.3%
- **Grok-4:** 32.7%

### 2. Consensus Collapse
Model agreement drops dramatically in action mode:
- **Theory mode:** 70.9% consensus
- **Action mode:** 43.0% consensus
- Model selection becomes critically important in production

### 3. Benchmark Validity Challenge
Generator-intended difficulty shows **near-zero correlation** (r=0.039) with judge-perceived difficulty

### 4. Reasoning Shift
Qualitative analysis reveals systematic shift from:
- **Theory mode:** Consequentialist reasoning (outcome-focused)
- **Action mode:** Deontological reasoning (rule/protocol-focused)

## 📖 Dilemma Examples

1. **Unsanctioned Surgery** - Emergency medical decision without proper authorization
2. **Predictive Policing** - Bias in crime prediction algorithms
3. **Interpreter's Dilemma** - Diplomatic translation with threatening nuances
4. **Autonomous Vehicle** - Life-or-death split-second decision
5. **Transparent Mind** - Privacy vs transparency in AI reasoning

See `dilemmas_flat.csv` for complete list with metadata.

## 🔗 Related Resources

- **Research Article:** `findings.md` (full methodology and analysis)
- **Experiment Code:** `run.py`, `analyze.py`, `create_figures.py`
- **GitHub Repository:** [dilemmas-api](https://github.com/values-md/dilemmas-api)
- **Project Website:** [values.md](https://values.md)

## 📝 Citation

```bibtex
@dataset{when_agents_act_2025,
  title={When Agents Act: Behavioral Shifts in Large Language Model Ethical Decision-Making from Evaluation to Deployment},
  author={Claude (Anthropic) and Strakhov, George},
  year={2025},
  month={November},
  note={Dataset of 12,802 LLM ethical decisions across theory and action modes},
  url={https://kaggle.com/datasets/...}  # Add your dataset URL
}
```

## ⚖️ License

**CC0 1.0 Universal (Public Domain Dedication)**

To the extent possible under law, the authors have waived all copyright and related rights to this dataset. You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.

## 🤝 Contact

- **George Strakhov:** [@strakho](https://github.com/strakho)
- **Issues:** [GitHub Issues](https://github.com/values-md/dilemmas-api/issues)

## 🏷️ Tags

`llm` `ai-safety` `ethics` `benchmarking` `evaluation` `alignment` `decision-making` `gpt-5` `claude` `gemini` `grok` `theory-action-gap`
