# VALUES.md Dilemmas Project - Development Plan

## Current Status: ✅ Step 3 Complete → Ready for Step 4

---

## ✅ Completed

### 1. Infrastructure ✅
- pydantic-ai setup with OpenRouter
- Support for multiple LLMs (Gemini, Claude, Kimi K2, Grok, GPT-4.1 Mini)
- Configuration system with YAML + .env
- Database with SQLModel (SQLite, ready for Postgres/D1)

### 2. Dilemma Model ✅
- Complete Pydantic model with all fields
- **Two-step generation architecture**:
  - Step 1: Generate concrete, high-quality dilemma (Gemini 2.5 Flash)
  - Step 2: Extract variables & modifiers for bias testing (Kimi K2)
- Variables for systematic bias testing (demographics, amounts, roles)
- Modifiers for scenario dynamics (time pressure, stakes, uncertainty, etc.)
- Seed-based generation for diversity
- Variation system (make_harder, etc.)
- Metadata tracking (generator model, prompt version, difficulty, etc.)

### 3. Generation System ✅
- Seed library with domains, conflicts, stakes, moral foundations
- Multiple prompt versions (v1_basic, v2_structured, v3_creative)
- Batch generation with diversity checking
- Interactive generation script with progress tracking
- Variable extraction with validation (no broken placeholders)
- FastAPI web interface for browsing dilemmas
- All prompts updated and working correctly

**Recent fixes (2025-10-23):**
- ✅ Fixed schema descriptions to prevent LLMs from using placeholders in Step 1
- ✅ Added validation to ensure all placeholders have matching values
- ✅ Fallback strategy: keep concrete text if extraction incomplete
- ✅ Fixed prompts to prevent choices being embedded in situation text
- ✅ Import of `re` module at top of generator.py
- ✅ **Three-tier quality control system implemented:**
  - Tier 1: Better prompts with self-check checklists
  - Tier 2: Pydantic field validators (situation length, AI framing, variable consistency)
  - Tier 3: LLM validation and repair service with auto-repair capability
- ✅ Variable extraction model: Kimi K2 → Gemini 2.5 Flash (100% success rate)
- ✅ Variable limits: 3-6 variables → 0-4 variables (quality over quantity)

---

## 🎯 Next Steps

### 4. Create Standard Test Set (~50 dilemmas) 🔜
**Current priority - ready to start tomorrow**

**Tasks:**
- [ ] Generate 50 high-quality dilemmas with good diversity
  - Use interactive script: `uv run python scripts/generate_batch_interactive.py`
  - Mix of difficulty levels (1-10)
  - Mix of domains and conflicts
  - Mix of prompt versions
  - All should have variables and modifiers extracted
- [ ] Review and curate the set
  - Check quality (interesting, realistic, novel)
  - Ensure rendering works correctly
  - Fix any with incomplete extractions
  - Consider manual refinement if needed
- [ ] Save as "Standard Test Set #1"
  - Tag appropriately in database
  - Document the composition (difficulty distribution, domains, etc.)

### 5. Set up JUDGEMENT Model 📝
**Next after test set is ready**

- [ ] Create `Judgement` Pydantic model
  - Link to dilemma_id
  - Capture: choice_id, reasoning, confidence
  - Model/temperature/settings used
  - Mode (theory vs action)
  - Timestamp
- [ ] Add database table
- [ ] Create judgment service
  - Theory mode: LLM explains what should be done
  - Action mode: LLM believes it's real, calls tools

### 6. Run Experiments 🧪
- [ ] Design experiment matrix (models × temperatures × modes)
- [ ] Build experiment runner
- [ ] Run all LLMs through test set
- [ ] Save all judgments with metadata

### 7. Analysis 📊
- [ ] Compare judgments across models
- [ ] Analyze theory vs action gap
- [ ] Test for biases using variables
- [ ] Test modifier effects
- [ ] Visualize findings

---

## 🐛 Known Issues

### Minor (not blocking):
1. **Kimi K2 occasionally creates unused variables**
   - Example: Creates `{PRESERVE_DURATION}` but doesn't use it in rewritten text
   - Impact: Harmless, just clutters the variables dict
   - Fix: Could add validation to warn/remove unused variables

2. **Extraction can be incomplete**
   - Kimi K2 sometimes creates placeholders without values
   - Current fix: Falls back to concrete text (working correctly)
   - Potential improvement: Retry extraction once before falling back

### None critical - system is production ready! ✅

---

## 🔧 Development Commands

**Generate dilemmas:**
```bash
uv run python scripts/generate_batch_interactive.py
```

**Explore dilemmas:**
```bash
uv run python scripts/serve.py  # http://localhost:8000
```

**Clear database:**
```bash
uv run python scripts/clear_db.py
```

**Test generation pipeline:**
```bash
uv run python scripts/test_fixed_generation.py
```

---

## 📚 Key Documentation

- `README.md` - Quick start, project overview
- `CLAUDE.md` - Architecture, design decisions, two-step generation
- `prompts/README.md` - Prompt structure and guidelines
- `config.yaml` - Model configurations, generation settings
