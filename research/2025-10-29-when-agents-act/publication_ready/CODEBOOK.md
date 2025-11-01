# Dataset Codebook

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
