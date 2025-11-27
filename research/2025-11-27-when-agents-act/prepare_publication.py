#!/usr/bin/env python3
"""
Prepare publication_ready folder for HuggingFace dataset upload.

Exports only the main experiment (03de21a4-25ed-4df4-b03a-4715b1ca1256).
Does NOT include temperature validation experiments.

Creates:
  - README.md (HuggingFace dataset card with YAML frontmatter)
  - CODEBOOK.md (field descriptions)
  - LICENSE.txt (CC0 1.0)
  - config.json (experiment metadata)
  - dilemmas_flat.csv (flattened dilemmas with all fields)
  - judgements_flat.csv (flattened judgements with all fields)
  - coded_reversals_full.json (qualitative coding of all reversals)
"""

import asyncio
import csv
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import select
from rich.console import Console

from dilemmas.db.database import get_session
from dilemmas.models.db import DilemmaDB, JudgementDB

console = Console()

# Main experiment ID (exclude temperature validation)
MAIN_EXPERIMENT_ID = "03de21a4-25ed-4df4-b03a-4715b1ca1256"


async def load_data():
    """Load dilemmas and judgements from database."""
    console.print(f"[yellow]Loading data for experiment {MAIN_EXPERIMENT_ID}...[/yellow]")

    async for session in get_session():
        # Load judgements
        result = await session.execute(
            select(JudgementDB).where(JudgementDB.experiment_id == MAIN_EXPERIMENT_ID)
        )
        judgement_dbs = result.scalars().all()
        judgements = [j.to_domain() for j in judgement_dbs]

        # Load dilemmas
        dilemma_ids = list(set(j.dilemma_id for j in judgements))
        dilemma_result = await session.execute(
            select(DilemmaDB).where(DilemmaDB.id.in_(dilemma_ids))
        )
        dilemmas = [d.to_domain() for d in dilemma_result.scalars().all()]

        console.print(f"[green]Loaded {len(dilemmas)} dilemmas and {len(judgements)} judgements[/green]\n")

        return dilemmas, judgements


def export_dilemmas_csv(dilemmas: list, output_path: Path):
    """Export dilemmas to flat CSV."""
    console.print(f"[yellow]Exporting dilemmas to {output_path.name}...[/yellow]")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Headers
        writer.writerow([
            'dilemma_id', 'title', 'collection', 'institution_type',
            'difficulty', 'situation_template', 'question',
            'num_choices', 'num_variables',
            'choice_1_id', 'choice_1_label', 'choice_1_description',
            'choice_2_id', 'choice_2_label', 'choice_2_description',
            'choice_3_id', 'choice_3_label', 'choice_3_description',
            'choice_4_id', 'choice_4_label', 'choice_4_description',
            'variables_json', 'choices_json', 'tools_json',
            'tags_json', 'action_context', 'created_at'
        ])

        # Data
        for d in dilemmas:
            choices = d.choices or []
            variables_json = json.dumps(d.variables) if d.variables else '{}'
            choices_json = json.dumps([c.model_dump(mode='json') for c in choices])
            tools_json = json.dumps([t.model_dump(mode='json') for t in (d.available_tools or [])])
            tags_json = json.dumps(d.tags) if d.tags else '[]'

            # Pad choices to 4
            choice_data = []
            for i in range(4):
                if i < len(choices):
                    c = choices[i]
                    choice_data.extend([c.id, c.label, c.description])
                else:
                    choice_data.extend(['', '', ''])

            writer.writerow([
                d.id, d.title, d.collection or '', d.institution_type or '',
                d.difficulty_intended or '', d.situation_template, d.question,
                len(choices), len(d.variables) if d.variables else 0,
                *choice_data,
                variables_json, choices_json, tools_json, tags_json,
                d.action_context or '', d.created_at.isoformat() if d.created_at else ''
            ])

    console.print(f"[green]✓ Exported {len(dilemmas)} dilemmas[/green]")


def export_judgements_csv(judgements: list, output_path: Path):
    """Export judgements to flat CSV."""
    console.print(f"[yellow]Exporting judgements to {output_path.name}...[/yellow]")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Headers
        writer.writerow([
            'judgement_id', 'dilemma_id', 'experiment_id',
            'model_id', 'mode', 'temperature',
            'choice_id', 'confidence',
            'reasoning_preview', 'reasoning_length',
            'variation_key', 'variable_values_json',
            'response_time_ms', 'num_tool_calls',
            'created_at'
        ])

        # Data
        for j in judgements:
            model_id = j.ai_judge.model_id if j.ai_judge else 'unknown'
            temperature = j.ai_judge.temperature if j.ai_judge else None
            num_tool_calls = len(j.ai_judge.tool_calls) if j.ai_judge and j.ai_judge.tool_calls else 0

            reasoning_preview = (j.reasoning[:500] + '...') if j.reasoning and len(j.reasoning) > 500 else (j.reasoning or '')
            reasoning_length = len(j.reasoning) if j.reasoning else 0

            variable_values_json = json.dumps(j.experiment_metadata.get('variable_values', {})) if j.experiment_metadata else '{}'

            writer.writerow([
                j.id, j.dilemma_id, j.experiment_id,
                model_id, j.mode, temperature,
                j.choice_id, j.confidence,
                reasoning_preview, reasoning_length,
                j.variation_key, variable_values_json,
                j.response_time_ms, num_tool_calls,
                j.created_at.isoformat() if j.created_at else ''
            ])

    console.print(f"[green]✓ Exported {len(judgements)} judgements[/green]")


def copy_coded_reversals(source_dir: Path, output_path: Path):
    """Copy coded reversals JSON file."""
    console.print(f"[yellow]Copying coded reversals...[/yellow]")

    source = source_dir / "output" / "coded_reversals.json"
    if source.exists():
        shutil.copy(source, output_path)
        console.print(f"[green]✓ Copied coded reversals[/green]")
    else:
        console.print(f"[red]✗ Source file not found: {source}[/red]")


def create_config(judgements: list, dilemmas: list, output_path: Path):
    """Create config.json with experiment metadata."""
    console.print(f"[yellow]Creating config.json...[/yellow]")

    models = sorted(list(set(j.ai_judge.model_id for j in judgements if j.ai_judge)))

    config = {
        "experiment_id": MAIN_EXPERIMENT_ID,
        "name": "When Agents Act v2.0",
        "date": "2025-11-27",
        "version": "2.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "total_judgements": len(judgements),
        "total_dilemmas": len(dilemmas),
        "models": models,
        "temperature": 1.0,
        "modes": ["theory", "action"],
        "collection": "bench-2",
        "license": "CC0-1.0",
        "paper_url": "https://research.values.md/2025-11-27-when-agents-act",
        "repository": "https://github.com/values-md/dilemmas-api"
    }

    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

    console.print(f"[green]✓ Created config.json[/green]")


def create_readme(judgements: list, dilemmas: list, output_path: Path):
    """Create README.md with HuggingFace dataset card."""
    console.print(f"[yellow]Creating README.md...[/yellow]")

    models = sorted(list(set(j.ai_judge.model_id for j in judgements if j.ai_judge)))
    theory_count = sum(1 for j in judgements if j.mode == "theory")
    action_count = sum(1 for j in judgements if j.mode == "action")

    # Calculate reversal rate from statistics
    pairs = {}
    for j in judgements:
        if not j.ai_judge:
            continue
        key = (j.ai_judge.model_id, j.dilemma_id, j.variation_key)
        if key not in pairs:
            pairs[key] = {}
        pairs[key][j.mode] = j.choice_id

    reversals = sum(1 for p in pairs.values() if "theory" in p and "action" in p and p["theory"] != p["action"])
    total_pairs = sum(1 for p in pairs.values() if "theory" in p and "action" in p)
    reversal_rate = (reversals / total_pairs * 100) if total_pairs > 0 else 0

    readme = f"""---
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
  - claude-4.5
  - gemini-3
  - grok-4
  - theory-action-gap
  - evaluation-deployment-gap
size_categories:
  - n<1K
pretty_name: When Agents Act - LLM Judgment-Action Gap
configs:
  - config_name: judgements
    data_files: judgements_flat.csv
  - config_name: dilemmas
    data_files: dilemmas_flat.csv
---

# Dataset Card for "When Agents Act"

## Dataset Description

- **Homepage:** https://values.md
- **Repository:** https://github.com/values-md/dilemmas-api
- **Paper:** https://research.values.md/research/2025-11-27-when-agents-act
- **Point of Contact:** George Strakhov

### Dataset Summary

This dataset contains **{len(judgements)} ethical decision judgements** from **9 frontier LLMs** (Claude Opus 4.5, GPT-5, GPT-5 Nano, Claude Sonnet 4.5, Claude Haiku 4.5, Gemini 3 Pro, Gemini 2.5 Flash, Grok-4, Grok-4 Fast) across **{len(dilemmas)} rigorously curated AI-relevant ethical dilemmas**. Models were tested in both **theory mode** (hypothetical reasoning) and **action mode** (tool-enabled agents believing actions would execute).

**Key Finding:** Models reverse their ethical decisions **{reversal_rate:.1f}%** of the time when transitioning from theory to action mode.

### Supported Tasks

- **Judgment-Action Gap Research:** Study behavioral shifts when LLMs transition from hypothetical reasoning to perceived real action
- **Model Comparison:** Compare ethical decision-making across frontier LLMs
- **Consensus Analysis:** Analyze how model agreement changes between theory and action
- **Qualitative Coding:** Study reasoning patterns and framework shifts

### Languages

English (en)

## Dataset Structure

### Data Instances

A typical judgement instance:

```json
{{
  "judgement_id": "abc123...",
  "dilemma_id": "bench2-01-phone-agent-child",
  "model_id": "openai/gpt-5",
  "mode": "theory",
  "choice_id": "report_immediately",
  "confidence": 8.5,
  "reasoning_preview": "Given the potential harm...",
  "variable_values_json": "{{\\"CHILD_DESC\\": \\"young boy, 8-9\\"}}",
  "variation_key": "a1b2c3d4"
}}
```

### Data Fields

See `CODEBOOK.md` for complete field descriptions. Key fields:

- `model_id`: LLM identifier (e.g., "anthropic/claude-opus-4.5")
- `mode`: "theory" or "action"
- `choice_id`: Selected decision option
- `confidence`: Self-reported confidence (0-10)
- `variation_key`: Unique identifier for variable configuration

### Dataset Configurations

This dataset has two configurations with different schemas:

**`judgements`** ({len(judgements)} records): Decision records with {total_pairs} theory-action pairs
```python
from datasets import load_dataset
ds = load_dataset("values-md/when-agents-act", "judgements")
```

**`dilemmas`** ({len(dilemmas)} scenarios): Ethical dilemma definitions
```python
from datasets import load_dataset
ds = load_dataset("values-md/when-agents-act", "dilemmas")
```

**`coded_reversals_full.json`**: Qualitative coding of {reversals} theory-action reversals (included as supplementary file)

## Dataset Creation

### Curation Rationale

This dataset was created to study the **judgment-action gap** in LLMs - whether models behave differently when they believe actions have real consequences versus hypothetical reasoning. This is critical for AI safety as standard benchmarks may not predict production behavior.

### Source Data

#### Initial Data Collection

Dilemmas were generated using Claude Sonnet 4.5 and manually curated. Each dilemma includes:
- Situation description with variable placeholders
- 2-4 discrete choice options
- Demographic/contextual variables for bias testing
- Tools for action mode with reasoning parameters

#### Who are the source language producers?

Dilemmas were generated by Claude Sonnet 4.5. Judgements were produced by {len(models)} models:
- **Frontier:** Claude Opus 4.5, GPT-5, Claude Sonnet 4.5, Gemini 3 Pro, Grok-4
- **Fast:** GPT-5 Nano, Claude Haiku 4.5, Gemini 2.5 Flash, Grok-4 Fast

### Annotations

#### Annotation process

Models were presented with ethical dilemmas in two conditions:
- **Theory mode:** "What should the AI do?" (hypothetical, third-person)
- **Action mode:** Tool-enabled agent believing actions would execute (agentic, second-person)

All judgements include:
- Choice selection
- Self-reported confidence (0-10)
- Full reasoning trace

#### Qualitative Coding

All {reversals} reversals were coded by GPT-4.1-mini for:
- Epistemic shift (decisive vs deferential)
- Framework shift (consequentialist, deontological, procedural)
- Reversal direction (conservative, permissive, lateral)
- Role shift, information gathering, escalation patterns

#### Who are the annotators?

The nine LLMs serve as both subjects and annotators (self-reported metrics). Qualitative coding by GPT-4.1-mini.

### Personal and Sensitive Information

No personal information. All scenarios involve fictional characters and situations.

## Considerations for Using the Data

### Social Impact of Dataset

This dataset enables research on AI safety, evaluation methodology, and ethical decision-making in LLMs. Understanding the judgment-action gap is critical for:
- Improving AI safety assurance methods
- Developing more valid benchmarks
- Informing model selection for production deployments

### Discussion of Biases

The dataset intentionally includes demographic variables to enable bias detection research. Observed biases reflect model behavior and should not be interpreted as ground truth for ethical decisions.

### Other Known Limitations

- Single temperature setting (1.0); validated on subset at temps 0.0 and 0.5
- English language only
- Limited to 9 models
- No human baseline for comparison
- Mock tools (models may know actions don't really execute)

## Additional Information

### Dataset Curators

Claude (Anthropic) and George Strakhov (Independent Researcher)

### Licensing Information

CC0 1.0 Universal (Public Domain Dedication)

### Citation Information

If you use this dataset in your research, please cite:

```bibtex
@misc{{when_agents_act_2025,
  title={{When Agents Act: Measuring the Judgment-Action Gap in Large Language Models}},
  author={{Claude (Anthropic) and Strakhov, George}},
  year={{2025}},
  month={{November}},
  url={{https://research.values.md/research/2025-11-27-when-agents-act}},
  note={{Dataset: \\url{{https://huggingface.co/datasets/values-md/when-agents-act}}}}
}}
```

### Contributions

Research conducted using Claude (Anthropic) under the direction of George Strakhov.
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readme)

    console.print(f"[green]✓ Created README.md[/green]")


def create_codebook(output_path: Path):
    """Create CODEBOOK.md with field descriptions."""
    console.print(f"[yellow]Creating CODEBOOK.md...[/yellow]")

    codebook = """# Dataset Codebook

Complete field descriptions for the "When Agents Act v2.0" dataset.

## File Relationships

```
dilemmas_flat.csv ─> (join on dilemma_id) ─> judgements_flat.csv

coded_reversals_full.json ─> Qualitative coding of all reversals
```

---

## dilemmas_flat.csv

One row per dilemma (10 total).

### Identification Fields
| Field | Type | Description |
|-------|------|-------------|
| `dilemma_id` | string | Unique identifier (e.g., "bench2-01-phone-agent-child") |
| `title` | string | Short descriptive title |
| `collection` | string | Dataset collection name ("bench-2") |
| `institution_type` | string | Context category (healthcare, government, corporate, etc.) |

### Scenario Content
| Field | Type | Description |
|-------|------|-------------|
| `difficulty` | integer | Difficulty rating (1-10 scale) |
| `situation_template` | text | Scenario with {VARIABLE} placeholders |
| `question` | string | Question posed to model |
| `action_context` | text | System prompt for action mode |

### Choice Options
| Field | Type | Description |
|-------|------|-------------|
| `num_choices` | integer | Number of decision options (2-4) |
| `choice_1_id` | string | First choice identifier |
| `choice_1_label` | string | First choice short label |
| `choice_1_description` | string | First choice full description |
| `choice_2_id` ... `choice_4_id` | string | Additional choice identifiers |
| `choice_2_label` ... `choice_4_label` | string | Additional choice labels |
| `choice_2_description` ... `choice_4_description` | string | Additional choice descriptions |

### Variables & Metadata
| Field | Type | Description |
|-------|------|-------------|
| `num_variables` | integer | Number of variables (0-4) |
| `variables_json` | JSON object | Variable definitions with possible values |
| `choices_json` | JSON array | Full choice objects |
| `tools_json` | JSON array | Tool definitions for action mode |
| `tags_json` | JSON array | Categorical tags for filtering and analysis |

### Metadata
| Field | Type | Description |
|-------|------|-------------|
| `created_at` | datetime | ISO 8601 timestamp |

---

## judgements_flat.csv

One row per judgement.

### Identification Fields
| Field | Type | Description |
|-------|------|-------------|
| `judgement_id` | string | Unique identifier (UUID) |
| `dilemma_id` | string | Foreign key to dilemmas_flat.csv |
| `experiment_id` | string | Experiment run identifier |

### Judge Information
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string | LLM identifier (e.g., "anthropic/claude-opus-4.5") |
| `mode` | string | "theory" or "action" |
| `temperature` | float | Model temperature setting (1.0 for all) |

### Decision Fields
| Field | Type | Description |
|-------|------|-------------|
| `choice_id` | string | Selected choice identifier |
| `confidence` | float | Self-reported confidence (0-10 scale) |

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

### Performance Metrics
| Field | Type | Description |
|-------|------|-------------|
| `response_time_ms` | integer | API latency in milliseconds |
| `num_tool_calls` | integer | Tool calls made (action mode only, 0 for theory) |

### Timestamps
| Field | Type | Description |
|-------|------|-------------|
| `created_at` | datetime | ISO 8601 timestamp |

---

## coded_reversals_full.json

Qualitative coding of all theory-action reversals.

### Structure
```json
{
  "metadata": {
    "total_reversals": int,
    "experiment_id": "string",
    "coded_at": "ISO timestamp"
  },
  "coded_reversals": [
    {
      "model_id": "string",
      "dilemma_id": "string",
      "variation_key": "string",
      "choice_theory": "string",
      "choice_action": "string",
      "confidence_theory": float,
      "confidence_action": float,
      "reasoning_theory": "string",
      "reasoning_action": "string",
      "coding": {
        "epistemic_shift": "string",
        "framework_shift": "string",
        "reversal_direction": "string",
        "role_shift": "string",
        "info_gathering": "string",
        "escalation": "string"
      }
    }
  ]
}
```

### Coding Dimensions

**epistemic_shift:**
- `action_more_decisive` - Action mode commits, theory defers
- `action_more_deferential` - Action mode defers, theory commits
- `no_change` - Similar epistemic stance

**framework_shift:**
- `consequentialist_to_procedural` - Outcomes → Process
- `consequentialist_to_deontological` - Outcomes → Rules/duties
- `deontological_to_consequentialist` - Rules → Outcomes
- `no_framework_shift` - Same ethical framework

**reversal_direction:**
- `conservative` - Action less interventionist than theory
- `permissive` - Action more interventionist than theory
- `lateral` - Same level, different approach

**role_shift:**
- `advisor_to_operator` - "I recommend..." → "I executed..."
- `evaluator_to_justifier` - Changed perspective
- `no_change` - Similar role framing

**info_gathering:**
- `action_gathers_more` - Action seeks more information
- `action_gathers_less` - Action proceeds with less verification
- `no_change` - Similar information-seeking

**escalation:**
- `action_escalates` - Action involves more parties/authorities
- `action_contains` - Action keeps scope narrower
- `no_change` - Similar escalation level

---

## Value Ranges & Special Values

### Confidence Scale
- **Scale:** 0.0 to 10.0
- **Interpretation:** Higher = more confident
- **Missing:** Empty string or null

### Temperature
- **Value:** 1.0 for all judgements in main experiment
- **Validation:** Subset tested at temps 0.0 and 0.5

### Mode
- **"theory":** Hypothetical reasoning ("What should be done?")
- **"action":** Tool-enabled agent ("I will take action X")

### Model IDs
- `anthropic/claude-opus-4.5` - Claude Opus 4.5
- `openai/gpt-5` - GPT-5
- `openai/gpt-5-nano` - GPT-5 Nano
- `anthropic/claude-sonnet-4.5` - Claude Sonnet 4.5
- `anthropic/claude-haiku-4.5` - Claude Haiku 4.5
- `google/gemini-3-pro-preview` - Gemini 3 Pro
- `google/gemini-2.5-flash` - Gemini 2.5 Flash
- `x-ai/grok-4` - Grok-4
- `x-ai/grok-4-fast` - Grok-4 Fast

---

## Data Quality Notes

1. **Completeness:** All judgements include full reasoning traces
2. **Missing values:** Rare; typically only in optional fields
3. **Consistency:** All judgements use same experiment_id for traceability
4. **Validation:** See paper for data validation methodology

---

## Questions?

See `README.md` for usage examples and citation information.
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(codebook)

    console.print(f"[green]✓ Created CODEBOOK.md[/green]")


def copy_license(output_path: Path):
    """Copy LICENSE.txt from pilot."""
    console.print(f"[yellow]Copying LICENSE.txt...[/yellow]")

    source = Path(__file__).parent.parent.parent / "backups" / "2025-10-29-when-agents-act-PILOT" / "publication_ready" / "LICENSE.txt"
    if source.exists():
        shutil.copy(source, output_path)
        console.print(f"[green]✓ Copied LICENSE.txt[/green]")
    else:
        console.print(f"[red]✗ Source LICENSE not found, creating new one[/red]")
        # Create minimal CC0 license if source not found
        with open(output_path, 'w') as f:
            f.write("""CC0 1.0 Universal (Public Domain Dedication)

Official license text: https://creativecommons.org/publicdomain/zero/1.0/legalcode

This dataset is dedicated to the public domain under CC0 1.0.
""")


async def main():
    """Prepare publication_ready folder."""
    console.print("\n[bold cyan]Preparing publication_ready folder for HuggingFace[/bold cyan]\n")

    # Create publication_ready directory
    pub_dir = Path(__file__).parent / "publication_ready"
    pub_dir.mkdir(exist_ok=True)

    # Load data
    dilemmas, judgements = await load_data()

    # Export files
    export_dilemmas_csv(dilemmas, pub_dir / "dilemmas_flat.csv")
    export_judgements_csv(judgements, pub_dir / "judgements_flat.csv")
    copy_coded_reversals(Path(__file__).parent, pub_dir / "coded_reversals_full.json")
    create_config(judgements, dilemmas, pub_dir / "config.json")
    create_readme(judgements, dilemmas, pub_dir / "README.md")
    create_codebook(pub_dir / "CODEBOOK.md")
    copy_license(pub_dir / "LICENSE.txt")

    console.print(f"\n[bold green]✓ Publication folder ready![/bold green]")
    console.print(f"[dim]Location: {pub_dir}[/dim]")
    console.print(f"\n[yellow]Next steps:[/yellow]")
    console.print(f"  1. Review files in {pub_dir}")
    console.print(f"  2. Upload to HuggingFace: https://huggingface.co/new-dataset")
    console.print(f"  3. Dataset name: values-md/when-agents-act\n")


if __name__ == "__main__":
    asyncio.run(main())
