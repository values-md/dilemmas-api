# Dataset Codebook

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
