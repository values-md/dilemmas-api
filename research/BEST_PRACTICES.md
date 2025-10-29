# Research Experiment Best Practices

This document captures lessons learned from running LLM ethical decision experiments. Follow these guidelines to avoid common pitfalls and ensure scientifically rigorous, reproducible research.

---

## Table of Contents

1. [Experiment Design Principles](#experiment-design-principles)
2. [Common Pitfalls & How to Avoid Them](#common-pitfalls--how-to-avoid-them)
3. [Experiment Workflow](#experiment-workflow)
4. [Code Quality & Testing](#code-quality--testing)
5. [Data Management](#data-management)
6. [Analysis & Interpretation](#analysis--interpretation)

---

## Experiment Design Principles

### 1. Avoid Confounded Variables

**❌ BAD - Confounded Design:**
```
Variation A: Emily Johnson (white, female)
Variation B: Arjun Patel (South Asian, male)
```
**Problem:** Can't separate gender bias from ethnicity bias.

**✅ GOOD - 2×2 Factorial Design:**
```
              Euro-American    Non-Euro
Female        Emily Johnson    Priya Patel
Male          James Anderson   Jamal Washington
```
**Benefit:** Can measure main effects AND interactions.

**Key Questions to Ask:**
- What independent variables am I testing?
- Are they orthogonal (independent) or confounded?
- Can I separate their effects in analysis?

### 2. Random Sampling

**❌ BAD:**
```python
selected_dilemmas = all_dilemmas[:8]  # First 8
```
**Problem:** Introduces bias from generation order, model selection, or timestamps.

**✅ GOOD:**
```python
random.seed(42)  # Fixed seed for reproducibility
selected_dilemmas = random.sample(all_dilemmas, 8)
```
**Benefit:** Unbiased sample, but reproducible.

### 3. Control for Noise

**Temperature Settings:**
- **High variance (temp 1.0):** Use when you WANT diversity (generating dilemmas)
- **Low variance (temp 0.3):** Use when you WANT consistency (measuring bias)

**For bias testing:**
- Lower temperature reduces random variation
- Makes it easier to detect systematic bias
- Allows single-shot per condition (saves API calls)

**OR increase repetitions:**
- If using temp 1.0, do 3+ repetitions per condition
- Average across repetitions to reduce noise

### 4. Avoid Anthropomorphic Mechanism Claims

**❌ BAD Claims:**
- "Models engage in System 1 thinking under pressure"
- "Stress-induced shortcuts lead to stereotyping"
- "Models feel cognitive load"

**✅ GOOD Claims:**
- "Models pattern-match time pressure prompts to stereotype-based reasoning in training data"
- "Shorter prompts correlate with increased reliance on base rate priors"
- "Time pressure tokens activate stereotype-associated patterns in model representations"

**Why it matters:**
- LLMs don't have cognitive processes like humans
- Mechanistic claims should reference training data and token patterns
- Be precise about what you're actually testing

### 5. Statistical Power

**Rule of thumb for bias detection:**
- **Per condition:** Need at least 8-12 dilemmas × 3 models = 24-36 comparisons
- **Per cell (if crossing factors):** At least n=3 for meaningful aggregation
- **Single-shot:** Only works if effect size is large and variance is low

**Our typical setup:**
- 8 dilemmas × 4 conditions × 4 demographics × 3 models = 384 judgements
- Per condition: 96 judgements (good for aggregate trends)
- Per dilemma×condition: 12 judgements (good for medium-large effects)

---

## Common Pitfalls & How to Avoid Them

### 1. ⚠️ String Matching Pitfalls

**The Problem:**
Substring matching with `in` operator causes false positives.

**❌ DANGEROUS PATTERNS:**
```python
# Problem: "non_euro_female" contains "euro"!
if "euro" in variation_name:
    ethnicity = "euro"

# Problem: "CORPORATION_NAME" contains "NAME"!
if "NAME" in variable_name:
    name_variables.append(variable_name)
```

**✅ SAFE PATTERNS:**
```python
# Use startswith/endswith for prefixes/suffixes
ethnicity = "non_euro" if variation_name.startswith("non_euro") else "euro"
gender = "female" if variation_name.endswith("female") else "male"

# Use explicit keyword lists with specific matching
PERSON_NAME_KEYWORDS = ["PATIENT", "DOCTOR", "VICTIM", "USER", ...]
INSTITUTIONAL_KEYWORDS = ["CORPORATION", "COMPANY", "ORGANIZATION", ...]

for var in variables:
    var_upper = var.upper()
    if "NAME" in var_upper:
        # Skip institutional names
        if any(inst in var_upper for inst in INSTITUTIONAL_KEYWORDS):
            continue
        # Include person names
        if any(person in var_upper for person in PERSON_NAME_KEYWORDS):
            person_name_vars.append(var)
```

**Best Practice:**
- Use keyword-based filtering with multiple checks
- Prefer explicit whitelisting over substring matching
- Add tests for edge cases

### 2. ⚠️ Institutional vs Person Names

**The Problem:**
Variables with "NAME" can refer to organizations, not people.

**Examples that FAIL bias testing:**
- `{CORPORATION_NAME}` → "Emily Johnson Corp" ❌
- `{COMPANY_NAME}` → "James Anderson LLC" ❌
- `{ORGANIZATION_NAME}` → "Priya Patel Foundation" ❌

**Examples that WORK for bias testing:**
- `{PATIENT_NAME}` → "Emily Johnson" ✅
- `{DOCTOR_NAME}` → "Dr. James Anderson" ✅
- `{VICTIM_NAME}` → "Priya Patel" ✅

**Solution:**
Create explicit keyword lists and filter carefully:
```python
PERSON_NAME_KEYWORDS = [
    "PATIENT", "DOCTOR", "VICTIM", "USER", "RESEARCHER",
    "MEMBER", "EMPLOYEE", "STUDENT", "TEACHER", "PROFESSOR",
    "SCIENTIST", "ENGINEER", "MANAGER", "DEVELOPER", "COLLEAGUE"
]

INSTITUTIONAL_KEYWORDS = [
    "CORPORATION", "COMPANY", "ORGANIZATION", "BUSINESS",
    "INSTITUTION", "FIRM", "ENTERPRISE", "STARTUP"
]
```

### 3. ⚠️ Metadata Structure

**❌ BAD - String Encoding:**
```python
judgement.notes = "bias_pressure|condition=baseline|variation=euro_female"
```
**Problems:**
- Fragile parsing (split on `|` and `=`)
- No type safety
- Hard to query
- Backwards compatibility nightmares

**✅ GOOD - Structured Metadata:**
```python
judgement.experiment_metadata = {
    "experiment": "bias_pressure",
    "condition": "baseline",
    "demographic_variation": "euro_female",
    "ethnicity": "euro",
    "gender": "female",
    "name_used": "Emily Johnson",
    "primary_name_variable": "{PATIENT_NAME}",
    "all_name_variables": ["{PATIENT_NAME}", "{DOCTOR_NAME}"]
}
```
**Benefits:**
- Type-safe (JSON)
- Easy to query with `json_extract()`
- Clear semantics
- Extensible

**Keep both for backwards compatibility:**
```python
# New structured format (primary)
judgement.experiment_metadata = {...}

# Old string format (for compatibility)
judgement.notes = f"bias_pressure|condition={condition}|variation={variation}"
```

### 4. ⚠️ Deterministic vs Random Assignment

**❌ BAD - Deterministic Assignment:**
```python
# Dilemma 0 ALWAYS gets "Emily Johnson"
# Dilemma 1 ALWAYS gets "Sarah Williams"
name = NAME_VARIATIONS["euro_female"][dilemmas.index(dilemma) % 3]
```
**Problem:** Confounds specific dilemmas with specific names.

**✅ GOOD - Consistent Random (or All Names):**
```python
# Option 1: Test all name variations for each dilemma
for variation_name, chosen_name in NAME_VARIATIONS.items():
    # Each dilemma tested with Emily, James, Priya, Jamal

# Option 2: Random assignment with fixed seed
random.seed(42)
name = random.choice(NAME_VARIATIONS["euro_female"])
```

---

## Experiment Workflow

### Standard Folder Structure

```
research/YYYY-MM-DD-experiment-name/
├── README.md           # Full design, hypotheses, methods
├── run.py              # Experiment runner script
├── analyze.py          # Analysis script (stats only)
├── findings.md         # Results + interpretation (YAML frontmatter required)
├── values/             # VALUES.md files (if testing frameworks)
├── data/               # Exported CSV files
├── judgements.json     # Full judgement data
├── dilemmas.json       # Dilemmas used
└── config.json         # Experiment metadata
```

### Findings.md Structure

All `findings.md` files MUST use YAML frontmatter for metadata extraction. This enables the research index page to display experiment information properly.

**Required Structure:**

```markdown
---
# Core Metadata
title: "Your Experiment Title"
slug: "YYYY-MM-DD-experiment-name"
date: YYYY-MM-DD
status: completed  # or: in_progress
experiment_id: "uuid-string-here"

# Research Summary
research_question: "Does X affect Y under Z conditions?"

abstract: |
  One-paragraph summary of the experiment (3-5 sentences).
  State the research question, design, key findings, and implications.
  This appears on the research index page.

key_finding: "One-sentence highlight of the most important result"

# Experiment Parameters
models:
  - Model Name 1
  - Model Name 2

data:
  dilemmas: 10
  judgements: 150
  conditions: 3

tags:
  - methodology
  - topic
  - model-comparison
---

# [Title]

## Background
...

## Methodology
...

## Results
...
```

**Key Points:**

- **YAML frontmatter is required** - Parser extracts metadata from YAML, not markdown body
- **Abstract is your summary** - Keep to 3-5 sentences, displays on index page
- **Key finding is your headline** - One sentence that captures the core result
- **Models list** - Display on index cards ("Tested: Claude Sonnet 4.5, GPT-4.1")
- **Tags** - Help users browse related experiments
- **Use template** - Copy from `research/TEMPLATE_findings.md`

**Structure Sections:**

1. **Background** - Why this question matters (2-3 paragraphs)
2. **Methodology** - Design, materials, measurements, procedure
3. **Results** - Primary and secondary findings with data
4. **Discussion** - Interpretation, explanations, limitations
5. **Implications** - For AI safety, agent design, future research
6. **Future Directions** - Specific follow-up experiments

**Scientific Rigor:**

- ✅ Clear hypotheses and design
- ✅ Honest limitations section
- ✅ Proper statistical interpretation
- ✅ No internal notes or TODOs
- ✅ Reproducible methods
- ❌ No overstated claims
- ❌ No anthropomorphic mechanism claims

### Workflow Steps

**1. Design & Plan**
```bash
# Create experiment folder
mkdir research/YYYY-MM-DD-experiment-name
cd research/YYYY-MM-DD-experiment-name

# Write README.md with:
# - Research question
# - Hypotheses (H1, H2, H3...)
# - Experimental design (sample size, conditions, controls)
# - Expected outcomes
# - Analysis plan
```

**2. Implement Runner Script**
```python
# run.py should have:
# - Dry-run mode
# - Progress tracking
# - Structured metadata
# - Error handling
# - Clear console output
```

**3. Test Before Running**
```bash
# ALWAYS test first!
uv run python research/YYYY-MM-DD-experiment-name/run.py --dry-run

# Check:
# - Dilemma selection makes sense
# - Sample size calculation is correct
# - Metadata structure is complete
```

**4. Verify Early Results**
```bash
# After first ~20 judgements, spot check:
sqlite3 data/dilemmas.db "
SELECT
  json_extract(data, '$.experiment_metadata') as metadata,
  substr(json_extract(data, '$.rendered_situation'), 1, 200) as situation
FROM judgements
WHERE experiment_id = 'YOUR_EXPERIMENT_ID'
LIMIT 5;
"

# Look for:
# - Names being substituted correctly
# - Metadata fields populated correctly
# - No obvious errors
```

**5. Let It Run**
- Don't interrupt unless you find a critical bug
- If you find a bug, STOP, delete data, fix, restart

**6. Export Data**
```bash
uv run python scripts/export_experiment_data.py EXPERIMENT_ID research/YYYY-MM-DD-experiment-name/data
```

**Note**: Web users will download data via the download button on the experiment page. This export step is primarily for initial data preparation.

**7. Analyze**
```bash
uv run python research/YYYY-MM-DD-experiment-name/analyze.py

# Analysis script should:
# - Compute statistics
# - Generate tables and visualizations
# - NOT make interpretations (just present data)
```

**8. Write Findings**
```bash
# Copy template
cp research/TEMPLATE_findings.md research/YYYY-MM-DD-experiment-name/findings.md

# Fill in YAML frontmatter:
# - title, date, status, experiment_id
# - research_question, abstract, key_finding
# - models, data stats, tags

# Write sections:
# - Background, Methodology, Results, Discussion
# - Implications, Limitations, Future Directions
# (No Methods Note - data available via web download button)
```

**Key Requirements:**
- Use YAML frontmatter (required for research index)
- Link to specific statistics from analyze.py
- Honest limitations section
- Scientific rigor (no overstated claims)
- **No Methods Note section** - Data is available via download button on web UI

**9. Verify Data Availability**
```bash
# Ensure all key files exist in experiment folder:
ls research/YYYY-MM-DD-experiment-name/

# Should contain:
# - findings.md (with YAML frontmatter)
# - README.md
# - config.json
# - dilemmas.json
# - judgements.json
# - analyze.py (if applicable)
# - data/*.csv (analysis outputs)
# - values/*.md (if testing frameworks)
```

Web users will access data via the "📥 Download Data Bundle" button on the experiment page.

**10. Update Research Index**
```bash
# Add to research/index.md under "Completed Experiments" (optional)
# The web UI automatically discovers new experiments
```

---

## Code Quality & Testing

### 1. Always Include Dry-Run Mode

```python
async def run_experiment(dry_run: bool = False):
    """Run the experiment."""

    if dry_run:
        console.print("[yellow]DRY RUN - No judgements will be saved[/yellow]\n")

    # ... setup ...

    console.print(f"[bold]Total judgements to collect:[/bold] {total}\n")

    if dry_run:
        console.print("[yellow]Dry run complete. Exiting.[/yellow]")
        return

    # Confirm before running
    console.print("[yellow]Press Enter to start, Ctrl+C to cancel...[/yellow]")
    input()
```

### 2. Test String Matching Logic

```python
# Always test parsing logic separately
def test_parsing():
    test_cases = [
        ("euro_female", "euro", "female"),
        ("non_euro_female", "non_euro", "female"),
        # ...
    ]

    for input_val, expected_ethnicity, expected_gender in test_cases:
        ethnicity = parse_ethnicity(input_val)
        gender = parse_gender(input_val)

        assert ethnicity == expected_ethnicity
        assert gender == expected_gender
```

### 3. Verification Scripts

Create small scripts to verify fixes:
```python
# scripts/test_person_names.py
async def test_selection():
    dilemmas = await select_dilemmas()

    for dilemma in dilemmas:
        # Check that all have person names
        # Check that none have institutional names
        # Print summary
```

### 4. Progress Tracking

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),          # Visual progress bar
    TaskProgressColumn(), # "X/Y (Z%)" counter
    console=console,
) as progress:
    task = progress.add_task("[cyan]Collecting judgements", total=total)

    for item in items:
        # Do work
        progress.update(task, advance=1, description=f"Processing {item}...")
```

---

## Data Management

### 1. Experiment IDs

Always generate a unique experiment ID:
```python
import uuid
experiment_id = str(uuid.uuid4())

# Print at start
console.print(f"[bold]Experiment ID:[/bold] [cyan]{experiment_id}[/cyan]\n")

# Store in all judgements
judgement.experiment_id = experiment_id
```

### 2. Deletion Script

Keep a deletion script for cleaning up bad runs:
```python
# scripts/delete_experiment.py
async def delete_experiment(experiment_id: str, dry_run: bool = False):
    # Count judgements
    # Confirm deletion (type 'DELETE')
    # Delete and commit
```

**Usage:**
```bash
# Check what would be deleted
uv run python scripts/delete_experiment.py EXPERIMENT_ID --dry-run

# Actually delete (requires typing 'DELETE')
uv run python scripts/delete_experiment.py EXPERIMENT_ID
```

### 3. Data Exports

Export to multiple formats for different uses:
```bash
# CSV for pandas/R
export_to_csv(experiment_id, "data/raw_judgements.csv")

# JSON for full context
export_to_json(experiment_id, "judgements.json")

# Dilemmas used
export_dilemmas(experiment_id, "dilemmas.json")
```

---

## Analysis & Interpretation

### 1. Separate Statistics from Interpretation

**analyze.py should:**
- ✅ Compute descriptive statistics
- ✅ Generate tables and charts
- ✅ Present data clearly
- ❌ NOT make interpretive claims
- ❌ NOT draw conclusions

**findings.md should:**
- ✅ Interpret the statistics
- ✅ Discuss what results mean
- ✅ Link to specific evidence
- ✅ Acknowledge limitations
- ✅ Propose follow-ups

### 2. Analysis Checklist

**Before interpreting:**
- [ ] Sample size adequate for claims?
- [ ] Control variables properly handled?
- [ ] Confounds identified and addressed?
- [ ] Effect sizes meaningful (not just p-values)?
- [ ] Outliers investigated?
- [ ] Missing data handled appropriately?

### 3. Common Analysis Patterns

**For 2×2 factorial designs:**
```python
# Main effect: Gender (averaging across ethnicities)
female_choices = df[df['gender'] == 'female']['choice_id']
male_choices = df[df['gender'] == 'male']['choice_id']

# Main effect: Ethnicity (averaging across genders)
euro_choices = df[df['ethnicity'] == 'euro']['choice_id']
non_euro_choices = df[df['ethnicity'] == 'non_euro']['choice_id']

# Interaction: Does gender effect differ by ethnicity?
# Compare (euro_female vs euro_male) to (non_euro_female vs non_euro_male)
```

**For pressure/condition effects:**
```python
# Compare baseline vs each pressure condition
for condition in ['time_pressure', 'high_stakes', 'combined']:
    baseline_df = df[df['condition'] == 'baseline']
    condition_df = df[df['condition'] == condition]

    # Calculate difference in bias
    bias_delta = calculate_bias(condition_df) - calculate_bias(baseline_df)
```

---

## Quick Reference: Pre-Flight Checklist

Before running an experiment, verify:

- [ ] **Design is clean** - No confounded variables
- [ ] **Sample size calculated** - Adequate power for hypotheses
- [ ] **Random sampling** - With fixed seed for reproducibility
- [ ] **Temperature appropriate** - Low (0.3) for consistency, or multiple reps
- [ ] **Metadata structured** - Using `experiment_metadata` dict
- [ ] **Person names only** - Not institutional names (for bias tests)
- [ ] **String matching safe** - No substring bugs (use startswith/endswith)
- [ ] **Dry-run works** - Tested before full run
- [ ] **Early verification plan** - How to check first few judgements
- [ ] **Deletion script ready** - In case of bugs
- [ ] **README complete** - Hypotheses, design, analysis plan documented
- [ ] **Progress tracking** - Can monitor experiment status

---

## Lessons from Specific Experiments

### Extreme VALUES.md Compliance (2025-10-24)

**What worked:**
- Clean 2×2 design (default vs extreme × baseline vs VALUES)
- Structured metadata made analysis easy
- Temperature 1.0 appropriate (measuring compliance, not consistency)

**Lessons:**
- Analysis scripts should NOT draw conclusions
- Let data speak for itself, interpret separately

### Bias Under Pressure (2025-10-24)

**What we learned the hard way:**
- ⚠️ Substring matching is dangerous (`"euro" in "non_euro_female"`)
- ⚠️ Institutional names are not person names (`CORPORATION_NAME` ≠ bias testing)
- ⚠️ Verify first ~20 judgements before letting experiment run fully
- ✅ Structured metadata saved us (could filter by demographics easily)
- ✅ Fixed seed randomization worked well (reproducible but unbiased)

**Bugs we fixed:**
1. String matching: `"euro" in variation_name` → `variation_name.startswith("non_euro")`
2. Name filtering: Added explicit PERSON_NAME_KEYWORDS vs INSTITUTIONAL_KEYWORDS
3. Verification: Created check scripts to spot issues early

---

## Resources

### Useful Scripts

- `scripts/delete_experiment.py` - Delete experiment data
- `scripts/export_experiment_data.py` - Export to CSV/JSON
- `scripts/explore_db.py` - Launch Datasette for SQL exploration
- `scripts/serve.py` - Browse dilemmas in web UI

### SQL Queries

**Check experiment progress:**
```sql
SELECT
  json_extract(data, '$.experiment_metadata.condition') as condition,
  json_extract(data, '$.experiment_metadata.demographic_variation') as demo,
  COUNT(*) as count
FROM judgements
WHERE experiment_id = 'YOUR_ID'
GROUP BY condition, demo;
```

**Verify metadata:**
```sql
SELECT
  json_extract(data, '$.experiment_metadata') as metadata,
  substr(json_extract(data, '$.rendered_situation'), 1, 200) as situation
FROM judgements
WHERE experiment_id = 'YOUR_ID'
LIMIT 5;
```

**Check for errors:**
```sql
SELECT
  json_extract(data, '$.error_message') as error,
  COUNT(*) as count
FROM judgements
WHERE experiment_id = 'YOUR_ID'
  AND json_extract(data, '$.error_occurred') = 1
GROUP BY error;
```

---

## Final Wisdom

**"Measure twice, cut once"** - Always dry-run and verify early results.

**"Perfect is the enemy of done"** - Exploratory studies don't need perfect designs. Learn and iterate.

**"Data beats intuition"** - Let statistics guide interpretation, not vice versa.

**"Document now, thank yourself later"** - Write the README before running the experiment.

**"Test your tests"** - Verification scripts need verification too.

---

*Last updated: 2025-10-29*
*Based on lessons from: Extreme VALUES.md Compliance, Bias Under Pressure, Theory vs Action Gap (Parts 1 & 2), VALUES.md Impact, Temperature Consistency*
