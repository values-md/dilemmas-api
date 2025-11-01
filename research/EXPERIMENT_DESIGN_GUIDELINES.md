# Experiment Design Guidelines

**Purpose:** Lessons learned from experiments to guide future research design.

## Critical Design Principle: Balanced Variation Counts

### The Problem (Learned from bench-1 Baseline)

**What Happened:**
- Systematic variable combinations created highly uneven distribution
- Top 4 dilemmas: 64% of all judgements (256 variations each = 2,048 judgements × 4)
- Bottom 6 dilemmas: 2.2% of all judgements (4-16 variations each)
- This creates statistical imbalance where a few scenarios dominate all aggregate conclusions

**Why It Matters:**
1. **Aggregate metrics are misleading** - "Overall consensus rate" is 64% determined by 4 dilemmas
2. **Small dilemmas are invisible** - Statistically insignificant in cross-dilemma comparisons
3. **Theme representation is skewed** - 4 ethical themes dominate, 16 themes are minor
4. **Analysis complexity increases** - Must use multiple weighting schemes and report stratified results

**Root Cause:**
Variables were extracted to maximize bias testing (0-4 variables per dilemma) without considering combinatorial explosion. A dilemma with 4 variables × 4 values each = 256 variations, while a dilemma with 1 variable × 4 values = 4 variations.

### The Solution: Design for Balance

**Target: 50-100 variations per dilemma**

This range provides:
- ✅ Sufficient statistical power for within-dilemma analysis
- ✅ Manageable compute/cost (20 dilemmas × 75 variations × 4 models × 2 modes = 12,000 judgements)
- ✅ Balanced representation across all dilemmas
- ✅ Simple aggregate metrics without complex weighting

### Implementation Strategies

#### Strategy 1: Cap Variables (Recommended for Most Cases)

**Rule:** Limit to 2-3 variables per dilemma with 3-4 values each

**Examples:**
```
2 variables × 3 values = 9 variations   (minimum acceptable)
2 variables × 4 values = 16 variations  (good)
3 variables × 3 values = 27 variations  (good)
3 variables × 4 values = 64 variations  (upper range)
4 variables × 3 values = 81 variations  (acceptable if needed)
4 variables × 4 values = 256 variations (TOO MANY - avoid!)
```

**Implementation:**
- During variable extraction, set max_variables = 3
- For each variable, limit to 3-4 carefully chosen values (not exhaustive)
- Prioritize quality over quantity: better to have 3 highly distinct values than 5 similar ones

**Example - Good Variable Design:**
```yaml
dilemma: "Medical Privacy Breach"
variables:
  DOCTOR_NAME: ["Dr. Maria Rodriguez", "Dr. James Chen", "Dr. Sarah Williams"]  # 3 values
  PATIENT_TYPE: ["elderly patient", "young child", "middle-aged adult"]          # 3 values
  SEVERITY: ["minor condition", "serious illness", "life-threatening emergency"] # 3 values

# Total: 3 × 3 × 3 = 27 variations (good!)
```

**Example - Bad Variable Design:**
```yaml
dilemma: "Medical Privacy Breach"
variables:
  DOCTOR_NAME: ["Dr. Maria Rodriguez", "Dr. James Chen", "Dr. Sarah Williams", "Dr. Aisha Patel"]  # 4
  PATIENT_TYPE: ["elderly patient", "young child", "teenager", "middle-aged adult"]                 # 4
  CONDITION: ["diabetes", "heart disease", "cancer", "mental illness"]                              # 4
  SEVERITY: ["minor", "moderate", "serious", "critical"]                                            # 4

# Total: 4 × 4 × 4 × 4 = 256 variations (TOO MANY!)
```

#### Strategy 2: Stratified Sampling

**Use when:** You need comprehensive variable coverage but want balanced data

**Process:**
1. Generate all possible variations (e.g., 4 × 4 × 4 × 4 = 256)
2. Randomly sample X% to reach target count (e.g., 25% → 64 variations)
3. Use stratified sampling to ensure representative coverage:
   - Sample proportionally from each variable value
   - Ensure all variable combinations appear at least once

**Example:**
```python
# Generate all 256 variations
all_variations = generate_all_combinations(variables)

# Stratified sample to 64 variations
target_count = 64
sampled_variations = stratified_sample(
    all_variations,
    target_count,
    strata=['DOCTOR_NAME', 'PATIENT_TYPE']  # Ensure these are represented
)
```

**Advantages:**
- Maintains comprehensive variable coverage
- Reduces to manageable count
- Can adjust sampling rate per dilemma to achieve balance

**Disadvantages:**
- Loses some statistical power within each variable
- Sampling adds complexity to reproduction

#### Strategy 3: Post-Hoc Reduction (For Existing Dilemmas)

**Use when:** You already have high-variation dilemmas and want to balance

**Process:**
1. Keep all generated variations in database
2. For experiments, sample down to target count
3. Can run multiple experiments with different samples

**Example:**
```python
# Existing dilemma has 256 variations
# Sample 64 for experiment, keeping rest for future use
experiment_variations = random.sample(all_variations, 64)
```

**Advantages:**
- Preserves all generated content
- Flexible - can run multiple experiments with different samples
- Doesn't require regeneration

**Disadvantages:**
- Still paid generation cost for unused variations
- Need to track which sample was used in which experiment

#### Strategy 4: Modifiers as Separate Dimension

**Use when:** You want scenario variation without combinatorial explosion

**Concept:** Keep core variables low (2-3), use modifiers as independent dimension

**Example:**
```yaml
variables:  # Low count for core identity
  DOCTOR_NAME: ["Dr. Rodriguez", "Dr. Chen", "Dr. Williams"]  # 3
  PATIENT_TYPE: ["elderly", "child", "adult"]                  # 3
  # Total: 3 × 3 = 9 base variations

modifiers:  # Applied independently, not combinatorially
  - "You have 5 minutes to decide"
  - "Multiple lives are at stake"
  - "This decision is irreversible"
  - "Your decision will be public"
  - "You are only 60% certain of the facts"

# Experiment can:
# - Run 9 base variations without modifiers (baseline)
# - Run 9 base variations × 5 modifiers = 45 total (modifier analysis)
# - Or run 9 base × subset of modifiers
# Rather than: 3 × 3 × 5 = 45 if modifiers were a variable (loses independence)
```

**Advantages:**
- Tests modifier effects independently
- Doesn't multiply base variation count
- Can mix and match modifiers flexibly

**Disadvantages:**
- Can't test modifier interactions as easily
- More complex experiment design

### Calculation Helpers

**Before finalizing variables, calculate total:**

```python
def calculate_variation_count(variables: dict[str, list]) -> int:
    """Calculate total variations from variable design."""
    count = 1
    for var_name, values in variables.items():
        count *= len(values)
    return count

# Check against target
target_min = 50
target_max = 100

variation_count = calculate_variation_count(variables)
if variation_count < target_min:
    print(f"⚠️  Too few variations ({variation_count}). Consider adding a variable or values.")
elif variation_count > target_max:
    print(f"⚠️  Too many variations ({variation_count}). Consider reducing variables or values.")
else:
    print(f"✅ Good variation count ({variation_count})")
```

**Quick reference table:**

| Vars | Values Each | Total | Assessment |
|------|------------|-------|------------|
| 2 | 3 | 9 | Too few (consider adding 3rd variable) |
| 2 | 4 | 16 | Low end (acceptable) |
| 2 | 5 | 25 | Low (acceptable) |
| 3 | 3 | 27 | Good |
| 2 | 6 | 36 | Good |
| 3 | 4 | 64 | Good |
| 4 | 3 | 81 | Upper range (acceptable) |
| 2 | 8 | 64 | Good (if values are truly distinct) |
| 3 | 5 | 125 | Too many (reduce to 4 values) |
| 4 | 4 | 256 | Way too many! (reduce to 3 vars or 3 values) |

## Other Design Principles

### 2. Difficulty Distribution

**Goal:** Sample evenly across difficulty spectrum (1-10)

**Why:** Enables testing "are hard dilemmas harder?" hypothesis without confounding

**Target distribution (for 20 dilemmas):**
- 1-3 (Easy): 3-4 dilemmas
- 4-6 (Medium): 8-10 dilemmas
- 7-10 (Hard): 6-8 dilemmas

**Check:** Does variation count correlate with difficulty?
- If yes, need to decide: Is this intentional or confounding?
- If unintentional, rebalance to decouple

### 3. Theme Coverage

**Goal:** Diverse ethical dimensions

**Dimensions to cover:**
- Individual vs. collective wellbeing
- Privacy vs. transparency
- Safety vs. innovation
- Fairness vs. efficiency
- Autonomy vs. paternalism
- Short-term vs. long-term consequences
- Rule-following vs. outcome-optimization

**Check:** Are themes evenly represented in terms of judgement counts?
- If 80% of judgements are in one theme, findings won't generalize

### 4. Choice Count Consistency

**Recommendation:** 2-3 choices per dilemma (consistent across set)

**Why:**
- 2 choices: Binary decisions, clean analysis, but may be too constraining
- 3 choices: Sweet spot - enough nuance, not overwhelming
- 4+ choices: Risk of choice overload, harder to achieve consensus

**Avoid:** Mixing 2-choice and 4-choice dilemmas in same experiment (confounds analysis)

### 5. Mode Design (Theory vs. Action)

**Always test both modes** to measure theory-action gap

**Considerations:**
- Are action mode tools consistent in granularity across dilemmas?
- Do tools actually enable action, or just relabel theory mode?
- Can we measure "behavioral realism" in action mode?

### 6. Model Selection

**Consider:**
- **Model speed:** Grok-4 with extended reasoning is 5-10× slower than others
- **Model cost:** Budget for full experiment (models × dilemmas × variations × modes)
- **Model diversity:** Include different architectures/companies for comparison

**For large experiments (>10K judgements):**
- Test with subset first (1 model, 2 dilemmas, all variations)
- Verify timing and cost before full run
- Consider excluding very slow models or running them separately

## Pre-Experiment Checklist

Before running a large experiment, verify:

- [ ] **Variation counts:** 50-100 per dilemma (calculate for each)
- [ ] **Total judgements:** Confirm budget and time (models × dilemmas × variations × modes)
- [ ] **Difficulty distribution:** Even spread across 1-10
- [ ] **Theme coverage:** Diverse ethical dimensions
- [ ] **Choice counts:** Consistent across dilemmas (2-3 choices)
- [ ] **Variable quality:** Are values truly distinct and meaningful?
- [ ] **API key loading:** Test background execution with env vars
- [ ] **Logging configured:** Detailed logs for debugging
- [ ] **Resume capability:** Test checkpoint and resume
- [ ] **Shuffle enabled:** For parallel execution across models
- [ ] **Cost estimate:** Calculated and approved
- [ ] **Time estimate:** Realistic based on test runs

## Experiment Documentation Template

Every experiment should have:

1. **README.md** - Overview, how to run, how to analyze
2. **DESIGN.md** - Detailed design, combinatorial calculations, limitations
3. **QUICKSTART.md** - Quick commands to start/stop/monitor
4. **config.json** - Machine-readable configuration
5. **findings.md** - Analysis results (created after completion)

## Analysis Guidelines

When analyzing experiments:

1. **Check for imbalance first** - Variation counts per dilemma
2. **Report multiple weighting schemes** - Variation-weighted AND dilemma-weighted
3. **Use stratification** - Small/medium/large categories
4. **State limitations explicitly** - What can/cannot be concluded
5. **Visualize distributions** - Show variation count imbalance clearly
6. **Per-dilemma analysis first** - Before aggregating across dilemmas
7. **Concordance checks** - Do conclusions hold across weighting schemes?

## Cost-Benefit Framework

When deciding variation counts, consider:

**Benefits of more variations (50 → 250):**
- More statistical power for bias detection within dilemma
- Can test more nuanced variable interactions
- Richer dataset for future analysis

**Costs of more variations:**
- 5× more API calls, time, money
- Statistical imbalance across dilemmas (if others have fewer)
- Diminishing returns (beyond ~100 variations per dilemma)
- Analysis complexity (must weight/stratify)

**Rule of thumb:** More variations are worth it IF:
- Dilemma is core to research question (justify the focus)
- ALL dilemmas have similarly high counts (maintain balance)
- Budget allows for comprehensive coverage (not sacrificing other dilemmas)

Otherwise: Keep it balanced at 50-100 per dilemma.

---

**Last Updated:** 2025-10-30 (after bench-1 baseline experience)
**Status:** Living document - update with lessons from each experiment
