# Research Reproducibility Guide

This guide explains how to reproduce and analyze experiments from the VALUES.md research project.

---

## Quick Start: Download & Analyze

### 1. Download Experiment Data

Visit any experiment page on the [research index](/research) and click the **"📥 Download Data Bundle"** button.

Each bundle contains:

- `README.md` - Experiment design and methodology
- `config.json` - Experiment configuration and metadata
- `dilemmas.json` - Full dilemmas used (with tool schemas, variables, etc.)
- `judgements.json` - All judgements with choices, confidence, reasoning
- `analyze.py` - Analysis script (if available)
- `data/*.csv` - Pre-computed summary statistics
- `values/*.md` - VALUES.md frameworks (if experiment tested ethical frameworks)

### 2. Run Analysis

```bash
# Extract the downloaded zip
unzip 2025-10-23-theory-vs-action.zip
cd 2025-10-23-theory-vs-action

# Install dependencies (if you haven't already)
# Note: Requires Python 3.12+ and uv package manager
pip install uv

# Run the analysis script
uv run python analyze.py
```

The analysis script will:
- Load `judgements.json` and `dilemmas.json`
- Compute statistics and generate visualizations
- Output results to console and/or `data/` directory

---

## Data Format Reference

### judgements.json

Array of judgement objects:

```json
{
  "id": "uuid",
  "dilemma_id": "uuid",
  "experiment_id": "uuid",
  "model": "anthropic/claude-sonnet-4.5",
  "temperature": 1.0,
  "choice_id": "notify",
  "confidence": 8.5,
  "difficulty": 6.2,
  "reasoning": "Detailed ethical reasoning...",
  "rendered_situation": "Situation with variables filled in...",
  "mode": "theory",
  "timestamp": "2025-10-23T12:34:56Z",
  "experiment_metadata": {
    "condition": "baseline",
    "demographic_variation": "euro_female",
    "custom_field": "..."
  }
}
```

**Key fields:**
- `choice_id` - Which option was selected
- `confidence` / `difficulty` - Self-reported metrics (0-10 scale)
- `reasoning` - LLM's justification for the choice
- `experiment_metadata` - Custom fields specific to each experiment

### dilemmas.json

Array of dilemma objects:

```json
{
  "id": "uuid",
  "title": "The Carbon Confession",
  "situation_template": "You are monitoring {USER_NAME}'s...",
  "situation": "Rendered situation...",
  "choices": [
    {
      "id": "notify",
      "label": "Notify community moderators",
      "action_context": "You can call notify_moderators(...)"
    }
  ],
  "variables": {
    "{USER_NAME}": ["Alice Chen", "Bob Smith", "..."]
  },
  "tags": ["privacy", "community"],
  "difficulty": 7
}
```

### config.json

Experiment metadata:

```json
{
  "experiment_id": "uuid",
  "title": "Theory vs Action Gap",
  "date": "2025-10-23",
  "models": ["gpt-4.1-mini"],
  "dilemmas_count": 4,
  "judgements_count": 40,
  "conditions": ["theory", "action"]
}
```

---

## Advanced: Custom Analysis

### Loading Data with Python

```python
import json
from pathlib import Path

# Load judgements
with open("judgements.json") as f:
    judgements = json.load(f)

# Load dilemmas
with open("dilemmas.json") as f:
    dilemmas = json.load(f)

# Example: Filter by condition
baseline_judgements = [
    j for j in judgements
    if j.get("experiment_metadata", {}).get("condition") == "baseline"
]

# Example: Group by choice
from collections import Counter
choices = Counter(j["choice_id"] for j in judgements)
print(choices)  # {'notify': 15, 'suppress': 10, ...}
```

### Loading Data with pandas

```python
import pandas as pd

# Load pre-computed CSV summaries
df = pd.read_csv("data/raw_judgements.csv")

# Filter and analyze
baseline = df[df["condition"] == "baseline"]
print(baseline.groupby("choice_id").size())

# Compare conditions
pivot = df.pivot_table(
    values="difficulty",
    index="dilemma_id",
    columns="condition",
    aggfunc="mean"
)
```

---

## For Researchers: Reproducing from Database

If you have access to the original database (not included in data bundles), you can export experiments using:

```bash
# Export a specific experiment
uv run python scripts/export_experiment_data.py <experiment-id> research/YYYY-MM-DD-name/data

# This creates:
# - judgements.json
# - dilemmas.json
# - config.json
# - data/*.csv
```

**Note:** Most users should just download the pre-exported data bundle from the web UI instead.

---

## Data Availability

All research data is:
- ✅ **Self-contained** - Each bundle includes everything needed
- ✅ **Version-controlled** - Part of the repository
- ✅ **Reproducible** - Includes exact model IDs, temperatures, prompts
- ✅ **Citable** - Each experiment has a unique ID

### Citation

If you use this data in your research, please cite:

```
VALUES.md Research Project (2025)
https://github.com/values-md/dilemmas-api
Experiment ID: [specific-experiment-id]
```
- - -

**Last Updated**: 2025-10-29

**Status**: Living document
