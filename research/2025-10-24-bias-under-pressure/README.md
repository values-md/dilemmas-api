# Bias Under Pressure: Demographic Bias Amplification Under Time Constraints and High Stakes

**Experiment ID:** `c0ecd87e-7adc-4a9b-8466-0edda52235be`
**Date:** 2025-10-24
**Status:** Completed

> **Note:** This experiment originally had UUID `b191388e-3994-4ebd-96cc-af0d033c5230`, which was accidentally reused for the 2025-10-29 bench-1 baseline experiment. On 2025-10-31, the 384 judgements from this experiment were migrated to the new UUID shown above to resolve the collision.

---

## Research Question

**Do LLMs show demographic bias in ethical decisions, and does this bias amplify under time pressure or high stakes?**

### Sub-questions:
1. Do models make different ethical choices based on demographically-identifiable names?
2. Can we separate **gender bias** from **ethnicity bias**?
3. Does time pressure amplify any observed demographic bias?
4. Do high stakes amplify any observed demographic bias?
5. Which models are most robust against bias under pressure?

---

## Hypothesis

**H1: Baseline Bias**
Models will show some demographic bias in ethical decisions based on names that signal gender and ethnicity.

**H2: Gender vs Ethnicity Effects**
Gender bias and ethnicity bias will have different magnitudes and may interact.

**H3: Time Pressure Amplification**
Time pressure prompts will amplify demographic bias, as models pattern-match to training data where humans under time constraints rely more on stereotypes.

**H4: High Stakes Amplification**
High stakes prompts will amplify demographic bias, as models activate decision patterns associated with high-consequence scenarios in training data.

**H5: Model Capability Correlation**
More capable models will show less bias and less amplification under pressure.

---

## Experimental Design

### Sample Selection
- **Dilemmas:** 8 dilemmas with name variables that appear in key decision roles
  - Selected from dilemmas with `{VICTIM_NAME}`, `{PATIENT_NAME}`, `{DOCTOR_NAME}`, `{USER_NAME}`, `{AGENT_NAME}`
  - Criteria: name appears in a position where bias could plausibly affect the decision
  - Mix of institution types (corporate, personal, public, research)

### Name Variations (2×2 Design)
Each dilemma tested with 4 names in a **2×2 factorial design** (Gender × Ethnicity):

| Gender | Euro-American | Non-Euro |
|--------|--------------|----------|
| **Female** | Emily Johnson | Priya Patel |
| **Male** | James Anderson | Jamal Washington |

**Design Benefits:**
- Separates gender bias from ethnicity bias
- Allows testing for interaction effects
- Each dimension has matched controls

### Conditions (Modifiers)
1. **Baseline:** No modifiers
2. **Time Pressure:** "You have 30 seconds to decide."
3. **High Stakes:** "Multiple lives depend on this decision."
4. **Combined:** Both time pressure and high stakes

### Sample Size
- 3 models (Claude Sonnet 4.5, GPT-4.1, Gemini 2.5 Pro)
- 8 dilemmas (randomly sampled from dilemmas with name variables)
- 4 conditions (baseline, time, stakes, combined)
- 4 name variations per condition (2×2: gender × ethnicity)
- **Total:** 3 × 8 × 4 × 4 = **384 judgements**

### Control Variables
- Temperature: 0.3 (lower than previous experiments to reduce noise)
- Repetitions: 1 per condition (single-shot)
- Mode: Theory (reasoning only, no actions)
- System prompt: None (baseline behavior)
- Dilemma selection: Random sample with fixed seed (seed=42) for reproducibility

---

## Measurements

### Primary Outcomes
1. **Choice differences by demographic:** Do models choose differently based on name?
2. **Gender bias magnitude:** Difference in choices between male vs female names (averaging across ethnicities)
3. **Ethnicity bias magnitude:** Difference in choices between Euro vs Non-Euro names (averaging across genders)
4. **Interaction effects:** Do gender and ethnicity interact? (e.g., is ethnicity bias stronger for women?)
5. **Bias amplification:** Change in bias magnitude from baseline to pressure conditions

### Secondary Outcomes
1. **Confidence by demographic:** Do models feel more/less confident with certain names?
2. **Difficulty by demographic:** Do models perceive decisions as harder/easier?
3. **Reasoning analysis:** Do models mention names differently? Use stereotypes?
4. **Model comparison:** Which models show most/least bias?

### Analysis Plan
1. **Main effects:**
   - Gender bias: Compare female vs male (averaging Euro + Non-Euro)
   - Ethnicity bias: Compare Euro vs Non-Euro (averaging male + female)
2. **Interaction effects:**
   - Test if gender bias differs by ethnicity
   - Test if ethnicity bias differs by gender
3. **Pressure amplification:**
   - Δ bias from baseline to time pressure
   - Δ bias from baseline to high stakes
   - Δ bias from baseline to combined
4. **Text analysis:** Reasoning for stereotype language
5. **Model comparison:** Rank models on all bias metrics

---

## Expected Outcomes

### Scenario 1: No Bias (Null Result)
- Models make identical choices regardless of name
- No amplification under pressure (nothing to amplify)
- **Interpretation:** Models are robust against demographic bias, even under pressure
- **Impact:** Strong evidence for safety, but may need more subtle bias tests

### Scenario 2: Baseline Bias, No Amplification
- Models show some bias in baseline condition
- Bias magnitude stays constant under time pressure / high stakes
- **Interpretation:** Models have implicit bias but maintain consistent reasoning under pressure
- **Impact:** Bias exists but is stable - focus on debiasing interventions

### Scenario 3: Baseline Bias + Amplification (Most Concerning)
- Models show bias in baseline
- Bias amplifies significantly under time pressure / high stakes
- **Interpretation:** Pressure leads to ethical shortcuts and stereotyping
- **Impact:** Critical safety concern - AI systems under pressure are more biased
- **Recommendation:** Add mandatory delays before high-stakes decisions

### Scenario 4: No Baseline Bias, But Amplification Under Pressure
- No bias in baseline
- Bias emerges only under time pressure / high stakes
- **Interpretation:** Pressure triggers latent bias that doesn't appear in careful reasoning
- **Impact:** Models are safe in low-pressure scenarios but risky under stress

---

## Implementation Notes

### Dilemma Selection Criteria
- Must have a name variable in a decision-critical role
- Name must refer to a person affected by the decision (not background characters)
- Dilemma must be complex enough that bias could plausibly influence reasoning
- Mix of institution types and ethical frameworks

### Name Selection Rationale
We chose names that clearly signal demographic categories in a 2×2 design:

**Euro-American Female** (Emily Johnson):
- Most common US female first name + common surname
- Signals: white, female, middle-class American

**Euro-American Male** (James Anderson):
- Common US male first name + common surname
- Signals: white, male, middle-class American

**Non-Euro Female** (Priya Patel):
- Indian/South Asian female
- Matched to Emily Johnson on gender

**Non-Euro Male** (Jamal Washington):
- African American male
- Matched to James Anderson on gender

**Design rationale:**
- 2×2 design allows separating gender from ethnicity bias
- Each demographic category has a control (matched on one dimension)
- 4 variations × 4 conditions = 16 tests per dilemma (good statistical power)
- Can expand to more ethnicities or socioeconomic variations if bias is detected

### Modifier Selection
- **Time pressure (30 seconds):** Short enough to feel urgent, long enough to be realistic
- **High stakes (multiple lives):** Clear, unambiguous high-stakes framing
- We're not testing other modifiers (uncertainty, visibility) to keep design clean

---

## Risk Mitigation

### Potential Issues
1. **Small sample per cell:** Only 1 judgement per model × dilemma × condition × name
   - Mitigation: Focus on aggregate patterns across dilemmas, not single cases

2. **Name confounds:** Names may signal more than demographics (professionalism, age, etc.)
   - Mitigation: Use common names that minimize other signals

3. **Dilemma selection bias:** We may accidentally select dilemmas where bias is more/less likely
   - Mitigation: Mix institution types and review dilemmas for balance

4. **Interpretation challenges:** Hard to distinguish bias from legitimate contextual reasoning
   - Mitigation: Careful reasoning analysis, look for explicit stereotypes

---

## Next Steps After This Experiment

### If Bias Found:
1. Test debiasing interventions (VALUES.md with "be careful of demographic bias")
2. Expand to more demographic variations (gender, ethnicity, age)
3. Test with more subtle name variations (same ethnicity, different class signals)

### If No Bias Found:
1. Test with more subtle demographic signals (names + professions, names + locations)
2. Test in action mode (do models act differently vs. just reason differently?)
3. Expand to other bias types (wealth, age, disability)

### If Amplification Found:
1. Test countermeasures (mandatory delays, "slow down and check for bias" prompts)
2. Test threshold effects (at what time pressure does bias emerge?)
3. Test in production-like conditions (multi-turn, real tools, real stakes)

---

## Files

- `run.py` - Experiment runner script
- `README.md` - This file (design and hypothesis)
- `analyze.py` - Analysis script (to be created after data collection)
- `findings.md` - Results and interpretation (to be written after analysis)
- `data/` - Exported CSV files
- `judgements.json` - Full judgement data with reasoning
- `dilemmas.json` - Dilemmas used in experiment
- `config.json` - Experiment metadata
