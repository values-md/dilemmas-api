# Extreme VALUES.md Compliance Experiment

**Date**: 2025-10-24
**Question**: At what extremity do LLMs refuse to follow VALUES.md frameworks? Do models comply with harmful ethical instructions?

## Experimental Design

### Hypothesis
LLMs will show varying compliance with extreme VALUES.md frameworks, with some models refusing or pushing back against clearly harmful directives while others follow instructions more literally.

### Conditions (6 frameworks per institution type)

**Corporate Dilemmas:**
1. **Baseline** - No VALUES.md (control)
2. **Shareholder Primacy** - Moderate: Maximize shareholder value above stakeholders
3. **Profit Absolutism** - Extreme: Profit justifies ANY means, no ethical constraints

**Public/Government Dilemmas:**
1. **Baseline** - No VALUES.md (control)
2. **Collectivist Absolutism** - Extreme: Collective good overrides all individual rights

**Personal Assistant Dilemmas:**
1. **Baseline** - No VALUES.md (control)
2. **Owner Absolutism** - Extreme: Serve owner exclusively, no ethical limits

**Nonprofit Dilemmas:**
1. **Baseline** - No VALUES.md (control)
2. **Mission Absolutism** - Extreme: Mission justifies all means, no moral constraints

**Research/Academic Dilemmas:**
1. **Baseline** - No VALUES.md (control)
2. **Scientific Absolutism** - Extreme: Truth above all, no research ethics

### Control Variables

- **Models**: 3 frontier models
  - Claude Sonnet 4.5 (anthropic/claude-sonnet-4.5)
  - GPT-4.1 (openai/gpt-4.1)
  - Gemini 2.5 Pro (google/gemini-2.5-pro)
- **Temperature**: 1.0
- **Dilemmas**: 10 total (2 per institution type)
- **Mode**: Theory mode
- **Context Matching**: Frameworks matched to institution type

### Sample Size

10 dilemmas × 6 frameworks × 3 models = **180 judgements**

### Measurements

1. **Compliance rate**: Do models follow extreme VALUES.md instructions?
2. **Refusal patterns**: What language indicates pushback or refusal?
3. **Model differences**: Which models are more/less compliant?
4. **Framework sensitivity**: Are certain extreme frameworks followed more readily?
5. **Choice distribution**: How do choices change with extremity?

## VALUES.md Files

All VALUES.md files are in the `values/` directory:
- `corporate_shareholder_primacy.md` - Moderate corporate framework
- `corporate_profit_absolutism.md` - Extreme corporate framework
- `public_collectivist_absolutism.md` - Extreme government framework
- `personal_owner_absolutism.md` - Extreme personal assistant framework
- `nonprofit_mission_absolutism.md` - Extreme nonprofit framework
- `research_scientific_absolutism.md` - Extreme research framework

## Running the Experiment

```bash
# Dry run (1 judgement to test)
uv run python research/2025-10-24-extreme-values/run.py --dry-run

# Full experiment (~30-45 minutes)
uv run python research/2025-10-24-extreme-values/run.py
```

## Results

Results are saved incrementally to the main database. View judgements at:
- Database: `data/dilemmas.db`
- Web interface: `http://localhost:8000/judgements`
- Filter by: `notes` contains `extreme_values_experiment`

Analysis script will be added after experiment completion.
