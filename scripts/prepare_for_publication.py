#!/usr/bin/env python3
"""Prepare research data for publication on Kaggle and Hugging Face.

This script transforms the research data into publication-ready formats:
- Flattens JSON to CSV for easy exploration
- Creates dataset cards and documentation
- Generates codebook with field descriptions
- Adds license and metadata files

Usage:
    uv run python scripts/prepare_for_publication.py
"""

import json
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Directories
RESEARCH_DIR = Path(__file__).parent.parent / "research" / "2025-10-29-when-agents-act"
OUTPUT_DIR = RESEARCH_DIR / "publication_ready"

def load_json(filepath):
    """Load JSON file."""
    with open(filepath) as f:
        return json.load(f)

def flatten_dilemmas(dilemmas_json_path, output_csv_path):
    """Flatten dilemmas.json to CSV format."""
    print(f"\n📄 Flattening dilemmas...")

    dilemmas = load_json(dilemmas_json_path)

    rows = []
    for d in dilemmas:
        # Extract seed components flexibly
        seed = d.get('seed_components', {})

        row = {
            'dilemma_id': d['id'],
            'title': d['title'],
            'institution_type': d.get('institution_type', ''),
            'difficulty_intended': d.get('difficulty_intended', None),
            'collection': d.get('collection', ''),
            'version': d.get('version', 1),
            'created_by': d.get('created_by', ''),
            'created_at': d.get('created_at', ''),

            # Flatten seed components (handle both list and single values)
            'seed_domain': seed.get('domain', ''),
            'seed_actors': ', '.join(seed.get('actors', [])) if isinstance(seed.get('actors'), list) else seed.get('actors', ''),
            'seed_conflict': seed.get('conflict', seed.get('power_dynamic', '')),
            'seed_stakes': ', '.join(seed.get('stakes', [])) if isinstance(seed.get('stakes'), list) else seed.get('stakes', ''),
            'seed_moral_foundation': seed.get('moral_foundation', ''),
            'seed_constraints': ', '.join(seed.get('constraints', [])) if isinstance(seed.get('constraints'), list) else seed.get('constraints', ''),

            # Text fields
            'situation': d.get('situation', d.get('situation_template', '')),
            'situation_template': d.get('situation_template', ''),
            'question': d.get('question', ''),

            # Count fields
            'num_choices': len(d.get('choices', [])),
            'num_variables': len(d.get('variables', [])),
            'num_modifiers': len(d.get('modifiers', [])),
            'num_tools': len(d.get('available_tools', d.get('tools', []))),

            # JSON fields (for complex nested data)
            'choices_json': json.dumps(d.get('choices', [])),
            'variables_json': json.dumps(d.get('variables', [])),
            'modifiers_json': json.dumps(d.get('modifiers', [])),
            'tools_json': json.dumps(d.get('available_tools', d.get('tools', []))),
            'tags_json': json.dumps(d.get('tags', [])),
        }

        # Add choice IDs as separate columns (up to 4 choices)
        for i, choice in enumerate(d.get('choices', [])[:4], 1):
            row[f'choice_{i}_id'] = choice.get('id', '')
            row[f'choice_{i}_label'] = choice.get('label', '')

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)

    print(f"✅ Created {output_csv_path.name}")
    print(f"   {len(df)} dilemmas × {len(df.columns)} columns")
    return df

def flatten_judgements(judgements_json_path, output_csv_path):
    """Flatten judgements.json to CSV format."""
    print(f"\n📄 Flattening judgements...")

    judgements = load_json(judgements_json_path)

    rows = []
    for j in judgements:
        # Base fields
        row = {
            'judgement_id': j['id'],
            'dilemma_id': j['dilemma_id'],
            'judge_type': j['judge_type'],
            'mode': j['mode'],
            'created_at': j['created_at'],

            # Decision fields
            'choice_id': j.get('choice_id', ''),
            'confidence': j.get('confidence', None),
            'perceived_difficulty': j.get('perceived_difficulty', None),
            'response_time_ms': j.get('response_time_ms', None),

            # Reasoning (first 500 chars for CSV, full available in JSON)
            'reasoning_preview': (j.get('reasoning', '') or '')[:500],
            'reasoning_length': len(j.get('reasoning', '') or ''),

            # Variation
            'variation_key': j.get('variation_key', ''),
            'variable_values_json': json.dumps(j.get('variable_values', {})),
            'modifier_indices': j.get('modifier_indices', None),

            # Experiment
            'experiment_id': j.get('experiment_id', ''),

            # Rendered situation
            'rendered_situation': j.get('rendered_situation', ''),
        }

        # AI-specific fields
        if j['judge_type'] == 'ai' and j.get('ai_judge'):
            ai = j['ai_judge']
            row['model_id'] = ai.get('model_id', '')
            row['temperature'] = ai.get('temperature', None)
            row['tokens_used'] = ai.get('tokens_used', None)
            row['extended_reasoning_enabled'] = ai.get('extended_reasoning_enabled', False)
            row['num_tool_calls'] = len(ai.get('tool_calls', []))
        else:
            row['model_id'] = ''
            row['temperature'] = None
            row['tokens_used'] = None
            row['extended_reasoning_enabled'] = False
            row['num_tool_calls'] = 0

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)

    print(f"✅ Created {output_csv_path.name}")
    print(f"   {len(df)} judgements × {len(df.columns)} columns")
    return df

def create_readme():
    """Create comprehensive README for dataset."""
    print(f"\n📝 Creating README...")

    readme = """# When Agents Act: LLM Ethical Decision-Making Dataset

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
"""

    output_path = OUTPUT_DIR / "README.md"
    output_path.write_text(readme)
    print(f"✅ Created {output_path.name}")
    return readme

def create_codebook():
    """Create comprehensive codebook with field descriptions."""
    print(f"\n📖 Creating CODEBOOK...")

    codebook = """# Dataset Codebook

Complete field descriptions for the "When Agents Act" dataset.

## File Relationships

```
dilemmas_flat.csv ─┐
                   ├─> (join on dilemma_id) ─> judgements_flat.csv
judgements.json ───┘

theory_action_paired.csv ─> Pre-joined theory+action pairs by (model_id, dilemma_id, variation_key)
```

---

## dilemmas_flat.csv

One row per dilemma (20 total).

### Identification Fields
| Field | Type | Description |
|-------|------|-------------|
| `dilemma_id` | string | Unique identifier (UUID format) |
| `title` | string | Short descriptive title |
| `version` | integer | Dilemma version number (1 for originals) |
| `collection` | string | Dataset collection name ("bench-1") |

### Difficulty & Classification
| Field | Type | Description |
|-------|------|-------------|
| `difficulty_intended` | integer | Generator's target difficulty (1-10 scale) |
| `institution_type` | string | Context category (healthcare, government, corporate, etc.) |

### Seed Components (Generation Template)
| Field | Type | Description |
|-------|------|-------------|
| `seed_domain` | string | Scenario domain (medical, environmental, diplomatic, etc.) |
| `seed_actor` | string | Primary decision-maker type |
| `seed_power_dynamic` | string | Authority/hierarchical structure |
| `seed_constraint` | string | Key limiting factor in decision |
| `seed_stake` | string | What's at risk |

### Scenario Text
| Field | Type | Description |
|-------|------|-------------|
| `situation` | text | Base scenario description (with variables as placeholders) |
| `situation_template` | text | Template with `{VARIABLE_NAME}` placeholders |

### Complexity Metrics
| Field | Type | Description |
|-------|------|-------------|
| `num_choices` | integer | Number of decision options (2-4) |
| `num_variables` | integer | Number of demographic/contextual variables (0-4) |
| `num_modifiers` | integer | Number of scenario modifiers (3-5) |
| `num_tools` | integer | Number of action-mode tools available |

### Choice Options
| Field | Type | Description |
|-------|------|-------------|
| `choice_1_id` | string | First choice identifier |
| `choice_1_label` | string | First choice label |
| `choice_2_id` | string | Second choice identifier |
| `choice_2_label` | string | Second choice label |
| `choice_3_id` | string | Third choice identifier (if present) |
| `choice_3_label` | string | Third choice label (if present) |

### Structured JSON Fields
| Field | Type | Description |
|-------|------|-------------|
| `choices_json` | JSON array | Full choice objects with id, label, description, tool_use |
| `variables_json` | JSON array | Variable definitions with name and possible values |
| `modifiers_json` | JSON array | Modifier texts for scenario variation |
| `tools_json` | JSON array | Tool definitions for action mode |
| `tags_json` | JSON array | Categorical tags for filtering |

### Metadata
| Field | Type | Description |
|-------|------|-------------|
| `created_by` | string | Generator model ID |
| `created_at` | datetime | ISO 8601 timestamp |

---

## judgements_flat.csv

One row per judgement (12,802 total).

### Identification Fields
| Field | Type | Description |
|-------|------|-------------|
| `judgement_id` | string | Unique identifier (UUID) |
| `dilemma_id` | string | Foreign key to dilemmas_flat.csv |
| `experiment_id` | string | Experiment run identifier |

### Judge Information
| Field | Type | Description |
|-------|------|-------------|
| `judge_type` | string | Always "ai" in this dataset |
| `model_id` | string | LLM identifier (e.g., "openai/gpt-5") |
| `mode` | string | "theory" or "action" |
| `temperature` | float | Model temperature setting (1.0 for all) |

### Decision Fields
| Field | Type | Description |
|-------|------|-------------|
| `choice_id` | string | Selected choice identifier |
| `confidence` | float | Self-reported confidence (0-10 scale) |
| `perceived_difficulty` | float | Judge's difficulty perception (0-10 scale) |

### Reasoning
| Field | Type | Description |
|-------|------|-------------|
| `reasoning_preview` | text | First 500 characters of reasoning |
| `reasoning_length` | integer | Full reasoning length in characters |

### Variation & Context
| Field | Type | Description |
|-------|------|-------------|
| `variation_key` | string | Hash identifying unique variable configuration |
| `variable_values_json` | JSON object | Specific variable substitutions used |
| `modifier_indices` | string | Which modifiers were applied (null for none) |
| `rendered_situation` | text | Actual text shown to model (with variables filled) |

### Performance Metrics
| Field | Type | Description |
|-------|------|-------------|
| `response_time_ms` | integer | API latency in milliseconds |
| `tokens_used` | integer | Token count (if available) |
| `num_tool_calls` | integer | Tool calls made (action mode only, 0 for theory) |
| `extended_reasoning_enabled` | boolean | Whether extended thinking was enabled |

### Timestamps
| Field | Type | Description |
|-------|------|-------------|
| `created_at` | datetime | ISO 8601 timestamp |

---

## theory_action_paired.csv

One row per (model, dilemma, variation) combination with both theory and action judgements.

Contains all fields from judgements_flat.csv with suffixes:
- `_theory`: Fields from theory mode judgement
- `_action`: Fields from action mode judgement

### Example Fields
| Field | Description |
|-------|-------------|
| `model_id` | Model identifier (shared) |
| `dilemma_id` | Dilemma identifier (shared) |
| `variation_key` | Variation identifier (shared) |
| `choice_id_theory` | Choice in theory mode |
| `choice_id_action` | Choice in action mode |
| `confidence_theory` | Confidence in theory mode |
| `confidence_action` | Confidence in action mode |
| `reversed` | Boolean: did choice change? |

Use this file to easily analyze theory-action gaps without joining.

---

## consensus_by_configuration.csv

Aggregated data showing model agreement patterns.

| Field | Type | Description |
|-------|------|-------------|
| `dilemma_id` | string | Dilemma identifier |
| `variation_key` | string | Variation identifier |
| `mode` | string | "theory" or "action" |
| `consensus_rate` | float | Proportion of models agreeing (0.0-1.0) |
| `majority_choice` | string | Most common choice |
| `num_models` | integer | Number of models that responded |

---

## reversals_sample.csv

Sample of interesting decision reversals with full reasoning.

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string | Model identifier |
| `dilemma_title` | string | Dilemma title |
| `choice_theory` | string | Choice in theory mode |
| `choice_action` | string | Choice in action mode |
| `reasoning_theory` | text | Full theory mode reasoning |
| `reasoning_action` | text | Full action mode reasoning |
| `confidence_shift` | float | Confidence change (action - theory) |

---

## difficulty_analysis.csv

Comparison of intended vs perceived difficulty.

| Field | Type | Description |
|-------|------|-------------|
| `dilemma_id` | string | Dilemma identifier |
| `dilemma_title` | string | Dilemma title |
| `difficulty_intended` | integer | Generator's target (1-10) |
| `difficulty_perceived_mean` | float | Average judge perception |
| `difficulty_perceived_std` | float | Standard deviation |
| `difficulty_gap` | float | perceived - intended |
| `num_judgements` | integer | Sample size |

---

## Value Ranges & Special Values

### Confidence & Difficulty Scales
- **Scale:** 0.0 to 10.0
- **Interpretation:** Higher = more confident/difficult
- **Missing:** Represented as empty string or null

### Temperature
- **Value:** 1.0 for all judgements
- **Reason:** Standard temperature for natural behavior baseline

### Mode
- **"theory":** Hypothetical reasoning ("What should be done?")
- **"action":** Tool-enabled agent ("I will take action X")

### Model IDs
- `openai/gpt-5` - OpenAI GPT-5
- `anthropic/claude-sonnet-4.5` - Claude 4.5 Sonnet
- `google/gemini-2.5-pro` - Gemini 2.5 Pro
- `x-ai/grok-4` - Grok-4

---

## Data Quality Notes

1. **Completeness:** All 12,802 judgements include full reasoning traces
2. **Missing values:** Rare; typically only in optional fields like modifier_indices
3. **Consistency:** All judgements use same experiment_id for traceability
4. **Validation:** See `findings.md` for data validation methodology

---

## Questions?

See `README.md` for usage examples and citation information.
"""

    output_path = OUTPUT_DIR / "CODEBOOK.md"
    output_path.write_text(codebook)
    print(f"✅ Created {output_path.name}")
    return codebook

def create_license():
    """Create CC0 license file."""
    print(f"\n⚖️  Creating LICENSE...")

    license_text = """CC0 1.0 Universal (Public Domain Dedication)

Official license text: https://creativecommons.org/publicdomain/zero/1.0/legalcode

CREATIVE COMMONS CORPORATION IS NOT A LAW FIRM AND DOES NOT PROVIDE
LEGAL SERVICES. DISTRIBUTION OF THIS DOCUMENT DOES NOT CREATE AN
ATTORNEY-CLIENT RELATIONSHIP. CREATIVE COMMONS PROVIDES THIS
INFORMATION ON AN "AS-IS" BASIS. CREATIVE COMMONS MAKES NO WARRANTIES
REGARDING THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS
PROVIDED HEREUNDER, AND DISCLAIMS LIABILITY FOR DAMAGES RESULTING FROM
THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS PROVIDED
HEREUNDER.

Statement of Purpose

The laws of most jurisdictions throughout the world automatically confer
exclusive Copyright and Related Rights (defined below) upon the creator
and subsequent owner(s) (each and all, an "owner") of an original work of
authorship and/or a database (each, a "Work").

Certain owners wish to permanently relinquish those rights to a Work for
the purpose of contributing to a commons of creative, cultural and
scientific works ("Commons") that the public can reliably and without fear
of later claims of infringement build upon, modify, incorporate in other
works, reuse and redistribute as freely as possible in any form whatsoever
and for any purposes, including without limitation commercial purposes.

These owners may contribute to the Commons to promote the ideal of a free
culture and the further production of creative, cultural and scientific
works, or to gain reputation or greater distribution for their Work in
part through the use and efforts of others.

For these and/or other purposes and motivations, and without any
expectation of additional consideration or compensation, the person
associating CC0 with a Work (the "Affirmer"), to the extent that he or she
is an owner of Copyright and Related Rights in the Work, voluntarily
elects to apply CC0 to the Work and publicly distribute the Work under its
terms, with knowledge of his or her Copyright and Related Rights in the
Work and the meaning and intended legal effect of CC0 on those rights.

---

Copyright and Related Rights

A Work made available under CC0 may be protected by copyright and related
or neighboring rights ("Copyright and Related Rights"). Copyright and
Related Rights include, but are not limited to, the following:

  i. the right to reproduce, adapt, distribute, perform, display,
     communicate, and translate a Work;
 ii. moral rights retained by the original author(s) and/or performer(s);
iii. publicity and privacy rights pertaining to a person's image or
     likeness depicted in a Work;
 iv. rights protecting against unfair competition in regards to a Work,
     subject to the limitations in paragraph 4(a), below;
  v. rights protecting the extraction, dissemination, use and reuse of data
     in a Work;
 vi. database rights (such as those arising under Directive 96/9/EC of the
     European Parliament and of the Council of 11 March 1996 on the legal
     protection of databases, and under any national implementation
     thereof, including any amended or successor version of such
     directive); and
vii. other similar, equivalent or corresponding rights throughout the
     world based on applicable law or treaty, and any national
     implementations thereof.

Waiver

To the greatest extent permitted by, but not in contravention of,
applicable law, Affirmer hereby overtly, fully, permanently, irrevocably
and unconditionally waives, abandons, and surrenders all of Affirmer's
Copyright and Related Rights and associated claims and causes of action,
whether now known or unknown (including existing as well as future claims
and causes of action), in the Work (i) in all territories worldwide, (ii)
for the maximum duration provided by applicable law or treaty (including
future time extensions), (iii) in any current or future medium and for any
number of copies, and (iv) for any purpose whatsoever, including without
limitation commercial, advertising or promotional purposes (the "Waiver").

Public License Fallback

Should any part of the Waiver for any reason be judged legally invalid or
ineffective under applicable law, then the Waiver shall be preserved to
the maximum extent permitted taking into account Affirmer's express
Statement of Purpose. In addition, to the extent the Waiver is so judged
Affirmer hereby grants to each affected person a royalty-free, non
transferable, non sublicensable, non exclusive, irrevocable and
unconditional license to exercise Affirmer's Copyright and Related Rights
in the Work (i) in all territories worldwide, (ii) for the maximum
duration provided by applicable law or treaty (including future time
extensions), (iii) in any current or future medium and for any number of
copies, and (iv) for any purpose whatsoever, including without limitation
commercial, advertising or promotional purposes (the "License"). The
License shall be deemed effective as of the date CC0 was applied by
Affirmer to the Work. Should any part of the License for any reason be
judged legally invalid or ineffective under applicable law, such partial
invalidity or ineffectiveness shall not invalidate the remainder of the
License, and in such case Affirmer hereby affirms that he or she will not
(i) exercise any of his or her remaining Copyright and Related Rights in
the Work or (ii) assert any associated claims and causes of action with
respect to the Work, in either case contrary to Affirmer's express
Statement of Purpose.

Limitations and Disclaimers

 a. No trademark or patent rights held by Affirmer are waived, abandoned,
    surrendered, licensed or otherwise affected by this document.
 b. Affirmer offers the Work as-is and makes no representations or
    warranties of any kind concerning the Work, express, implied,
    statutory or otherwise, including without limitation warranties of
    title, merchantability, fitness for a particular purpose, non
    infringement, or the absence of latent or other defects, accuracy, or
    the present or absence of errors, whether or not discoverable, all to
    the greatest extent permissible under applicable law.
 c. Affirmer disclaims responsibility for clearing rights of other persons
    that may apply to the Work or any use thereof, including without
    limitation any person's Copyright and Related Rights in the Work.
    Further, Affirmer disclaims responsibility for obtaining any necessary
    consents, permissions or other rights required for any use of the
    Work.
 d. Affirmer understands and acknowledges that Creative Commons is not a
    party to this document and has no duty or obligation with respect to
    this CC0 or use of the Work.
"""

    output_path = OUTPUT_DIR / "LICENSE.txt"
    output_path.write_text(license_text)
    print(f"✅ Created {output_path.name}")
    return license_text

def create_hf_metadata():
    """Create dataset card metadata for Hugging Face."""
    print(f"\n🤗 Creating Hugging Face metadata...")

    metadata = """---
license: cc0-1.0
task_categories:
  - text-classification
  - question-answering
  - text-generation
language:
  - en
tags:
  - llm
  - ai-safety
  - ethics
  - benchmarking
  - evaluation
  - alignment
  - decision-making
  - gpt-5
  - claude
  - gemini
  - grok
  - theory-action-gap
  - evaluation-deployment-gap
size_categories:
  - 10K<n<100K
pretty_name: When Agents Act - LLM Ethical Decision-Making
dataset_info:
  features:
    - name: judgement_id
      dtype: string
    - name: dilemma_id
      dtype: string
    - name: model_id
      dtype: string
    - name: mode
      dtype: string
    - name: choice_id
      dtype: string
    - name: confidence
      dtype: float64
    - name: perceived_difficulty
      dtype: float64
    - name: reasoning_preview
      dtype: string
    - name: variable_values_json
      dtype: string
    - name: variation_key
      dtype: string
  splits:
    - name: judgements
      num_examples: 12802
    - name: dilemmas
      num_examples: 20
  configs:
    - config_name: default
      data_files:
        - split: judgements
          path: judgements_flat.csv
        - split: dilemmas
          path: dilemmas_flat.csv
---

# Dataset Card for "When Agents Act"

## Dataset Description

- **Homepage:** https://values.md
- **Repository:** https://github.com/values-md/dilemmas-api
- **Paper:** See `findings.md` in this repository
- **Point of Contact:** George Strakhov

### Dataset Summary

This dataset contains 12,802 ethical decision judgements from four frontier LLMs (GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro, Grok-4) across 20 AI-relevant ethical dilemmas with 1,601 variable configurations. Models were tested in both theory mode (hypothetical reasoning) and action mode (tool-enabled agents believing actions would execute).

**Key Finding:** Models reverse their ethical decisions 33.4% of the time when transitioning from theory to action mode.

### Supported Tasks

- **Evaluation-Deployment Gap Research:** Study behavioral shifts between evaluation and production contexts
- **Model Comparison:** Compare ethical decision-making across frontier LLMs
- **Bias Detection:** Analyze demographic sensitivity in AI decisions
- **Benchmark Validity:** Study generator-judge calibration in LLM-generated benchmarks

### Languages

English (en)

## Dataset Structure

### Data Instances

A typical judgement instance:

```json
{
  "judgement_id": "abc123...",
  "dilemma_id": "def456...",
  "model_id": "openai/gpt-5",
  "mode": "theory",
  "choice_id": "report_immediately",
  "confidence": 8.5,
  "perceived_difficulty": 6.0,
  "reasoning_preview": "Given the potential harm...",
  "variable_values_json": "{\"DOCTOR_NAME\": \"Dr. Smith\"}",
  "variation_key": "a1b2c3d4"
}
```

### Data Fields

See `CODEBOOK.md` for complete field descriptions. Key fields:

- `model_id`: LLM identifier (gpt-5, claude-4.5-sonnet, gemini-2.5-pro, grok-4)
- `mode`: "theory" or "action"
- `choice_id`: Selected decision option
- `confidence`: Self-reported confidence (0-10)
- `perceived_difficulty`: Judge's difficulty perception (0-10)
- `variation_key`: Unique identifier for variable configuration

### Data Splits

- `judgements`: 12,802 decision records
- `dilemmas`: 20 ethical scenarios

## Dataset Creation

### Curation Rationale

This dataset was created to study the evaluation-deployment gap in LLMs - whether models behave differently when they believe actions have real consequences versus hypothetical reasoning. Understanding this gap is critical for AI safety as standard benchmarks may not predict production behavior.

### Source Data

#### Initial Data Collection and Normalization

Dilemmas were generated using Gemini 2.5 Flash with explicit difficulty targets (1-10). Each dilemma includes:
- Situation description with variable placeholders
- 2-4 discrete choice options
- Demographic/contextual variables for bias testing
- Scenario modifiers (time pressure, stakes, uncertainty)
- Tools for action mode

#### Who are the source language producers?

Dilemmas were generated by Gemini 2.5 Flash. Judgements were produced by GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro, and Grok-4.

### Annotations

#### Annotation process

Models were presented with ethical dilemmas in two conditions:
- **Theory mode:** "What should be done?" (hypothetical reasoning)
- **Action mode:** Tool-enabled agent with belief that actions would execute

All judgements include:
- Choice selection
- Self-reported confidence (0-10)
- Perceived difficulty (0-10)
- Full reasoning trace

#### Who are the annotators?

The four frontier LLMs serve as both subjects and annotators (self-reported metrics).

### Personal and Sensitive Information

No personal information. All scenarios involve fictional characters and situations.

## Considerations for Using the Data

### Social Impact of Dataset

This dataset enables research on AI safety, evaluation methodology, and ethical decision-making in LLMs. Understanding the evaluation-deployment gap is critical for:
- Improving AI safety assurance methods
- Developing more valid benchmarks
- Informing model selection for production deployments

### Discussion of Biases

The dataset intentionally includes demographic variables to enable bias detection research. Observed biases reflect model behavior and should not be interpreted as ground truth for ethical decisions.

### Other Known Limitations

- Single temperature setting (1.0)
- English language only
- Limited to 4 frontier models
- No human baseline for comparison

## Additional Information

### Dataset Curators

Claude (Anthropic) and George Strakhov (Independent Researcher)

### Licensing Information

CC0 1.0 Universal (Public Domain Dedication)

### Citation Information

```bibtex
@dataset{when_agents_act_2025,
  title={When Agents Act: Behavioral Shifts in Large Language Model Ethical Decision-Making from Evaluation to Deployment},
  author={Claude (Anthropic) and Strakhov, George},
  year={2025},
  month={November},
  publisher={Hugging Face},
  url={https://huggingface.co/datasets/...}
}
```

### Contributions

Research conducted using Claude (Anthropic) under the direction of George Strakhov.
"""

    # For HF, this goes in the README.md with YAML frontmatter
    output_path = OUTPUT_DIR / "README_HF.md"
    output_path.write_text(metadata)
    print(f"✅ Created {output_path.name}")
    print(f"   (Rename to README.md when uploading to Hugging Face)")
    return metadata

def main():
    """Main execution."""
    print("=" * 60)
    print("🚀 Preparing Dataset for Publication")
    print("=" * 60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Step 1: Flatten data
    print(f"\n📦 Output directory: {OUTPUT_DIR}")

    dilemmas_csv = flatten_dilemmas(
        RESEARCH_DIR / "dilemmas.json",
        OUTPUT_DIR / "dilemmas_flat.csv"
    )

    judgements_csv = flatten_judgements(
        RESEARCH_DIR / "judgements.json",
        OUTPUT_DIR / "judgements_flat.csv"
    )

    # Step 2: Copy key analysis files
    print(f"\n📋 Copying analysis files...")

    analysis_files = [
        "theory_action_paired.csv",
        "summary_by_condition.csv",
        "config.json",
        "findings.md",
    ]

    # From output/ folder
    output_analysis_files = [
        "consensus_by_configuration.csv",
        "samples_reversals.csv",
        "difficulty_analysis.csv",
    ]

    for filename in analysis_files:
        src = RESEARCH_DIR / filename
        if src.exists():
            import shutil
            shutil.copy(src, OUTPUT_DIR / filename)
            print(f"  ✓ {filename}")

    for filename in output_analysis_files:
        src = RESEARCH_DIR / "output" / filename
        if src.exists():
            import shutil
            shutil.copy(src, OUTPUT_DIR / filename)
            print(f"  ✓ {filename}")

    # Step 3: Create documentation
    create_readme()
    create_codebook()
    create_license()
    create_hf_metadata()

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("✅ Dataset Preparation Complete!")
    print("=" * 60)
    print(f"\n📁 Location: {OUTPUT_DIR}")
    print(f"\n📊 Files created:")
    print(f"  - dilemmas_flat.csv ({len(dilemmas_csv)} dilemmas)")
    print(f"  - judgements_flat.csv ({len(judgements_csv)} judgements)")
    print(f"  - README.md (Kaggle/general)")
    print(f"  - README_HF.md (Hugging Face with metadata)")
    print(f"  - CODEBOOK.md")
    print(f"  - LICENSE.txt (CC0 1.0)")
    print(f"  - config.json")
    print(f"  - findings.md")
    print(f"  - theory_action_paired.csv")
    print(f"  - consensus_by_configuration.csv")
    print(f"  - samples_reversals.csv")
    print(f"  - difficulty_analysis.csv")

    print(f"\n🎯 Next steps:")
    print(f"  1. KAGGLE:")
    print(f"     - Go to https://www.kaggle.com/datasets")
    print(f"     - Click 'New Dataset'")
    print(f"     - Upload all files from {OUTPUT_DIR}")
    print(f"     - Kaggle will use README.md as dataset description")
    print(f"")
    print(f"  2. HUGGING FACE:")
    print(f"     - Create new dataset at https://huggingface.co/new-dataset")
    print(f"     - Rename README_HF.md to README.md")
    print(f"     - Upload all files via web UI or git")
    print(f"     - HF will parse YAML frontmatter automatically")

    print(f"\n💡 Tips:")
    print(f"  - Test CSV files in Excel/pandas before uploading")
    print(f"  - Kaggle supports up to 100GB (you're well under)")
    print(f"  - HF supports files up to 50GB per file")
    print(f"  - Both platforms support versioning")

    return 0

if __name__ == "__main__":
    sys.exit(main())
