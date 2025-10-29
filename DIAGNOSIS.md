# Systematic Diagnosis: bench-1 Generation Issues

## Complete Workflow Trace

### Step 1: Generation (`generate_from_seed`)
```
Input: DilemmaSeed (domain, actors, conflict, stakes, difficulty)
Process: LLM generates concrete dilemma with specific names/amounts/details
Output: Dilemma with concrete situation_template
Status: ✅ WORKING
```

### Step 2: Variable Extraction (`variablize_dilemma`)
```
Input: Dilemma with concrete situation
Process:
  1. Extract 0-4 high-impact variables
  2. Rewrite situation with {PLACEHOLDERS}
  3. Create variables dict: {"{PLACEHOLDER}": [value1, value2, ...]}
  4. Extract 3-5 modifiers
Output: Dilemma with situation_template containing placeholders + variables dict
Status: ✅ WORKING (extraction logic is sound)
```

### Step 3: Validation (`validate_and_repair`)
```
Input: Dilemma with placeholders + variables
Process:
  1. Validate dilemma quality (validate method)
  2. If issues found, repair (repair method)
  3. Re-validate repaired version
Output: (dilemma, ValidationResult)
Status: ❌ FAILING - Multiple issues
```

---

## Issue #1: KeyError 'PLACEHOLDERS'

### Symptoms
```
Attempt 1 failed: 'PLACEHOLDERS'
Attempt 3 failed: 'PLACEHOLDERS'
```

### Root Cause
The repair LLM is returning invalid field names in the `changes` dict.

**Code path:**
1. `validator.py:172` - Iterates over `repair_plan.changes.items()`
2. If LLM returns `{"PLACEHOLDERS": "some value"}` instead of `{"situation_template": "..."}`
3. Line 173: `if field in repaired_data` - "PLACEHOLDERS" is not a valid field
4. This should NOT cause KeyError (the `if` guards it)

**Actual cause:** The error message `'PLACEHOLDERS'` suggests the LLM is confused and returning field names that don't exist. The validation prompt might be mentioning "PLACEHOLDERS" and the LLM is treating it as a field name.

### Evidence
Looking at repair prompt (repair.md):
- Line 65: "**{PLACEHOLDERS} in situation_template** (these are intentional for bias testing - leave them as-is)"
- The LLM might be interpreting this as instructions to repair a field called "PLACEHOLDERS"

---

## Issue #2: Tool Mapping Validation Failures

### Symptoms
```
Tool mapping validation failed: Choices missing tool_name: ['neural_network', 'rule_based', 'hybrid']
Tool count mismatch: 1 tools but 3 choices
```

### Root Cause Analysis

**Where tool mapping happens:**
1. Generation (Tier 1) - LLM should populate `tool_name` for each choice
2. Pydantic validation (Tier 2) - Checks if tool_name exists and matches available_tools
3. Auto-fix (generator.py:326-399) - Attempts to infer tool names if missing

**The problem:**
- Initial generation often misses `tool_name` fields (common LLM oversight)
- Auto-fix tries to repair but validation still fails
- Validation prompt (validate.md:36-38) checks for tool_name consistency
- Validator flags this as "cannot auto-repair" → raises exception

**Why it's failing:**
1. Generation prompt doesn't emphasize tool_name strongly enough
2. Auto-fix happens BEFORE variable extraction
3. After variable extraction, validation checks tool mapping again
4. Validator doesn't understand that tool_name issues were already fixed

---

## Issue #3: Validation Prompt Confusion About Placeholders

### Symptoms
```
'The situation template contains placeholder variables ({POPULATION_GROUP}, {CONDITION_TYPE})
not filled with concrete details, reducing clarity and realism.'
```

### Root Cause
Even with our fixes, the validation LLM is still confused about whether placeholders are problems.

**Why:**
1. The validation happens AFTER variable extraction (correct)
2. The prompt says "if Variables shows 'Yes', placeholders are okay"
3. But the context passed to validator includes the variables info
4. The LLM is still treating placeholders as a quality issue

**The validation prompt check (validate.md:19):**
```markdown
**Variables**: {has_variables}
**Modifiers**: {has_modifiers}
```

This shows "Yes (4 variables)" but the LLM still flags placeholders as problems.

---

## Issue #4: Validation Criteria Too Strict

### Symptoms
```
'Situation description is only about 300 characters, at the lower limit;
expanding with more context could enhance clarity.'
```

### Root Cause
- v8_concise targets 400-800 chars
- Some dilemmas are ~300 chars (still valid)
- Validator marks this as an issue even though it's acceptable

---

## Issue #5: Validation Prompt vs Extraction Output Mismatch

### Core Problem
The validation prompt expects:
- Concrete details (names, amounts)
- No placeholders (normally)

But AFTER variable extraction, we have:
- Placeholders like `{CLIENT_NAME}`
- Variables dict with values

The validator doesn't properly understand this transformation.

---

## Root Cause Summary

### 1. Validation Prompt Design Flaw
The validation prompt (`prompts/validation/validate.md`) was designed for:
- Validating CONCRETE dilemmas (before variable extraction)
- OR validating dilemmas WITHOUT variables

It was NOT designed for:
- Validating dilemmas AFTER variable extraction (with placeholders)

### 2. Workflow Order Issue
Current flow:
```
Generate (concrete) → Extract Variables (adds placeholders) → Validate
```

But validator expects:
```
Generate (concrete) → Validate → Extract Variables
```

### 3. Repair LLM Confusion
The repair prompt mentions "PLACEHOLDERS" as something to "not change", but the LLM interprets this as a field name to repair.

---

## Solutions

### Option A: Validate BEFORE Variable Extraction (Recommended)

Change `generate_with_validation` order:
```python
# Step 1: Generate dilemma
dilemma = await self.generate_from_seed(seed)

# Step 2: Validate CONCRETE dilemma (no placeholders yet)
if enable_validation:
    dilemma, validation = await validator.validate_and_repair(dilemma)

# Step 3: Add variables (after validation passes)
if self.config.generation.add_variables:
    dilemma = await self.variablize_dilemma(dilemma)
```

**Pros:**
- Validator sees concrete dilemmas (what it's designed for)
- No placeholder confusion
- Clean separation of concerns

**Cons:**
- Variables are added AFTER validation (not validated)
- Variable extraction might break validated dilemma

### Option B: Improve Validation Prompt for Placeholders

Enhance validation prompt to truly understand placeholders:
- Add examples of good placeholder usage
- Explicitly ignore placeholder presence in scoring
- Update repair instructions to never touch placeholders

**Pros:**
- More sophisticated validation
- Variables are validated

**Cons:**
- Complex prompt engineering
- LLMs still might get confused

### Option C: Validate Variables Separately

Two-stage validation:
1. Validate concrete dilemma (before extraction)
2. Validate variable extraction quality (after extraction)

**Pros:**
- Targeted validation for each stage
- Clear separation

**Cons:**
- More complex code
- Two LLM calls per dilemma

---

## Recommendation: **Option A (Validate Before Extraction)**

This is the cleanest fix because:

1. **Validation prompt works as designed** - validates concrete dilemmas
2. **No prompt rewriting needed** - existing prompts are fine
3. **Variable extraction is deterministic** - unlikely to break things
4. **Clear workflow**: Generate → Validate → Variablize → Save

### Implementation Changes Needed

**File: `src/dilemmas/services/generator.py`**

Change lines 547-576 in `generate_with_validation()`:

```python
# CURRENT (broken):
# Step 1: Generate
dilemma = await self.generate_from_seed(seed)
# Step 2: Add variables
if self.config.generation.add_variables:
    dilemma = await self.variablize_dilemma(dilemma)
# Step 3: Validate (sees placeholders → fails)
if enable_validation:
    dilemma, validation = await validator.validate_and_repair(dilemma)

# FIXED (proposed):
# Step 1: Generate
dilemma = await self.generate_from_seed(seed)
# Step 2: Validate CONCRETE dilemma
if enable_validation:
    dilemma, validation = await validator.validate_and_repair(dilemma)
# Step 3: Add variables AFTER validation
if self.config.generation.add_variables:
    dilemma = await self.variablize_dilemma(dilemma)
```

This is a **2-line change** (swap steps 2 and 3).

---

## Testing Plan

After implementing Option A:

1. **Test single generation:**
   ```bash
   python -c "
   import asyncio
   from dilemmas.services.generator import DilemmaGenerator

   async def test():
       gen = DilemmaGenerator(model_id='openai/gpt-5-mini', prompt_version='v8_concise')
       dilemma, validation = await gen.generate_with_validation(
           seed=None,  # Random seed
           difficulty=5,
           enable_validation=True,
           min_quality_score=5.0,
       )
       print(f'Success: {dilemma.title}')
       print(f'Quality: {validation.quality_score}/10')
       print(f'Has variables: {len(dilemma.variables)} variables')

   asyncio.run(test())
   "
   ```

2. **Test bench-1 generation:**
   ```bash
   uv run python scripts/generate_bench1.py
   ```

3. **Verify workflow:**
   - Concrete dilemma validates successfully
   - Variables extracted after validation
   - No placeholder errors
   - Tool mapping works correctly

---

## Expected Outcomes

After fix:
- ✅ No more KeyError 'PLACEHOLDERS'
- ✅ Validation sees concrete dilemmas (no placeholder confusion)
- ✅ Variables added AFTER validation passes
- ✅ Tool mapping validated on concrete dilemmas
- ✅ Repair logic works on concrete text
- ✅ bench-1 generation succeeds

---

## Additional Fixes Needed

Even with Option A, we should:

1. **Strengthen generation prompts for tool_name**
   - Emphasize that EVERY choice needs a tool_name
   - Add self-check for tool_name completion

2. **Improve auto-fix logging**
   - Show what tool names were inferred
   - Help debug future tool mapping issues

3. **Add variable extraction validation**
   - Optional: validate that extraction didn't break the dilemma
   - Check that placeholder count is reasonable (not too many)

---

## Implementation Complete ✅

### Changes Made

**File: `src/dilemmas/services/generator.py` (lines 547-643)**

Changed `generate_with_validation()` workflow:

```python
# NEW FLOW:
1. Generate concrete dilemma
2. Validate concrete dilemma (Tier 3 LLM validation)
3. Extract variables (adds placeholders)
4. Technical validation:
   - Check variables extracted (len > 0)
   - Check tools available (len > 0)
   - Check tool/choice count matches
   - Check all choices have tool_name
5. Return validated dilemma with variables
```

### Technical Validation Added

After variable extraction, we now validate:

```python
✓ Variables extracted (must have at least 1)
✓ Tools available (must have at least 1)
✓ Tool count matches choice count
✓ All choices have tool_name field set
```

If any check fails, retry generation (up to max_attempts).

### Benefits

1. **Quality validation sees concrete dilemmas** - No placeholder confusion
2. **Technical validation ensures completeness** - Variables and tools always present
3. **Clear separation of concerns** - Quality check vs. technical check
4. **Automatic retry on technical failures** - Robust generation
5. **Variables added to validated dilemmas** - High quality input for extraction

---

## Timeline

1. ✅ **Implement Option A + Technical Validation** - Complete
2. **Test single generation** - 2 minutes (next step)
3. **Run bench-1** - 40-60 minutes (generation time)
4. **Manual QA** - 30-40 minutes (review 20 dilemmas)

Total: ~2 hours to fixed bench-1 collection
