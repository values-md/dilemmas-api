# Experiment System Design - Phased Approach

## Overview
Build a system to test how different LLMs make ethical decisions under various conditions. Start simple with 5 dilemmas, then scale to full experiments.

---

## Phase 1: Single LLM Runner (START HERE)
**Goal:** Get one LLM making judgements on 5 dilemmas and saving to database

### Components to Build:

#### 1. Judge Service (`src/dilemmas/services/judge.py`)
```python
class DilemmaJudge:
    """Run LLMs on dilemmas and get their judgements."""

    async def judge_dilemma(
        self,
        dilemma: Dilemma,
        model_id: str,
        temperature: float,
        mode: Literal["theory", "action"] = "theory",
        system_prompt: str | None = None,
        system_prompt_type: Literal["none", "default", "custom_values", "other"] = "default",
        values_file_name: str | None = None,
        variable_values: dict[str, str] | None = None,
        modifier_indices: list[int] | None = None,
    ) -> Judgement:
        """
        Run a single LLM on a single dilemma variant.

        Steps:
        1. Render dilemma with variables (if provided)
        2. Build prompt based on mode (theory vs action)
        3. Apply system_prompt if provided (KEY for VALUES.md research!)
        4. Run LLM with structured output to get choice
        5. Package as Judgement with all metadata (including prompt info)
        6. Return Judgement (caller saves to DB)
        """
```

**Theory Mode Prompt:**
- Present the situation + question + choices
- Ask: "Which choice would you make and why?"
- Get: choice_id, reasoning, confidence

**Action Mode Prompt:**
- Use `dilemma.action_context` as system prompt
- Provide tools matching the choices
- AI believes it's real, calls a tool
- Get: choice from tool call, reasoning from before call

#### 2. Test Script (`scripts/test_judge.py`)
```python
# Test with 1 dilemma first
async def test_single_judgement():
    # Load 1 dilemma from database
    # Run judge in theory mode
    # Print result
    # Save to database

# Then test with all 5
async def test_batch():
    # Load 5 dilemmas
    # Run judge on each
    # Save all judgements
    # Print summary
```

### Success Criteria:
- ✅ Can run Gemini on 1 dilemma in theory mode
- ✅ Judgement saved to database with all metadata
- ✅ Can run on all 5 dilemmas
- ✅ Can view judgements in FastAPI interface

### Files to Create:
- `src/dilemmas/services/judge.py` - Judge service
- `scripts/test_judge.py` - Test runner
- Migration for judgements table (if not exists)

---

## Phase 2: Batch Runner with Progress
**Goal:** Run experiments that can resume if interrupted

### Components to Build:

#### 1. Experiment Config (`src/dilemmas/models/experiment.py`)
```python
class ExperimentConfig(BaseModel):
    """Configuration for an experiment run."""

    experiment_id: str  # Unique ID for this run
    dilemma_ids: list[str]  # Which dilemmas to test
    model_id: str
    temperature: float
    mode: Literal["theory", "action"]
    repetitions: int = 1  # Run each dilemma N times
```

#### 2. Experiment Runner (`src/dilemmas/services/experiment.py`)
```python
class ExperimentRunner:
    """Run batch experiments with progress tracking."""

    async def run_experiment(
        self,
        config: ExperimentConfig,
        resume: bool = True,
    ):
        """
        Run experiment, saving after each judgement.

        Features:
        - Progress bar
        - Incremental saving (resume if crashes)
        - Error logging
        - Summary statistics at end
        """
```

#### 3. Interactive Script (`scripts/run_experiment.py`)
```python
# User-friendly experiment runner
# - Select dilemmas (or "all")
# - Select model
# - Select temperature
# - Select mode
# - Show estimate: "This will make ~15 API calls, cost ~$0.50"
# - Confirm and run
```

### Success Criteria:
- ✅ Can run 5 dilemmas × 1 model × 3 repetitions = 15 judgements
- ✅ If interrupted, can resume from where it stopped
- ✅ Progress bar shows completion
- ✅ Summary shows: success rate, avg confidence, choice distribution

---

## Phase 3: Multi-Model & Custom Values Testing
**Goal:** Test multiple models AND system prompt variations

### THE KEY RESEARCH QUESTION:
**Does providing a VALUES.md file make LLMs more aligned with user preferences?**

### Components to Build:

#### 1. Expand ExperimentConfig
```python
class ExperimentConfig(BaseModel):
    # Support multiple models
    model_configs: list[ModelConfig]  # Each has model_id + temperature

    # Support multiple system prompts (KEY FEATURE!)
    system_prompt_configs: list[SystemPromptConfig]

class ModelConfig(BaseModel):
    model_id: str
    temperature: float

class SystemPromptConfig(BaseModel):
    prompt_type: Literal["none", "default", "custom_values", "other"]
    prompt_text: str | None = None
    values_file_name: str | None = None  # e.g., "alice.values.md"
```

#### 2. VALUES.md File Management
```python
class ValuesFileLoader:
    """Load and manage VALUES.md files."""

    def load_values_file(self, filename: str) -> str:
        """Load a VALUES.md file from values/ directory."""

    def list_available_values_files(self) -> list[str]:
        """List all VALUES.md files available for testing."""
```

Create `values/` directory for storing different VALUES.md variants:
- `values/none.txt` - Empty (baseline)
- `values/default.txt` - Generic ethical prompt
- `values/alice.values.md` - Alice's personal values
- `values/utilitarian.values.md` - Utilitarian ethics
- `values/deontological.values.md` - Duty-based ethics

#### 3. Update Runner
- Generate test matrix: dilemmas × models × **system_prompts** × repetitions
- Compare same model with different values
- Estimate total cost before running

### Success Criteria:
- ✅ Can test: 5 dilemmas × 1 model × 3 system prompts = 15 judgements
- ✅ E.g., test Claude with:
  * No custom prompt (baseline)
  * Generic ethical prompt
  * Alice's VALUES.md file
- ✅ Can compare: Did Alice's values change the decisions?
- ✅ Cost estimate shown before running

---

## Phase 4: Variable Expansion
**Goal:** Test bias by varying demographics, amounts, etc.

### Components to Build:

#### 1. Variable Expander (`src/dilemmas/services/variables.py`)
```python
class VariableExpander:
    """Generate all or sampled variable combinations."""

    def get_all_combinations(self, dilemma: Dilemma) -> list[dict[str, str]]:
        """Generate all possible variable combinations."""
        # If dilemma has {NAME}: [A, B, C] and {AMOUNT}: [X, Y]
        # Returns: [
        #   {NAME: A, AMOUNT: X},
        #   {NAME: A, AMOUNT: Y},
        #   {NAME: B, AMOUNT: X},
        #   ...
        # ]

    def get_sampled_combinations(
        self,
        dilemma: Dilemma,
        sample_size: int
    ) -> list[dict[str, str]]:
        """Random sample of combinations."""
```

#### 2. Expand ExperimentConfig
```python
class ExperimentConfig(BaseModel):
    variable_strategy: Literal["none", "all", "sample"]
    variable_sample_size: int | None = None
```

### Success Criteria:
- ✅ If dilemma has 3×3 variables, can test all 9 combinations
- ✅ Can sample 3 random combinations instead
- ✅ variation_key properly set for grouping later

---

## Phase 5: Modifiers & Complete System
**Goal:** Full experiment capability

### Add:
- Modifier application (time pressure, stakes, etc.)
- Theory vs Action mode comparison
- Multiple temperature testing
- Time constraints

### Success Criteria:
- ✅ Can run overnight: 5 dilemmas × 5 models × 2 temps × 2 modes × 3 reps
- ✅ ~600 judgements collected
- ✅ Ready for statistical analysis

---

## Phase 6: Analysis Tools
**Goal:** Extract insights from judgement data

### Components:

#### 1. Basic Queries
- Filter by model, temperature, mode
- Filter by system_prompt_type, values_file_name
- Group by variation_key (same scenario, different models/prompts)

#### 2. Statistical Analysis
- **Model comparison**: Do models differ in their choices?
- **Bias detection**: Do variables affect choices (demographics, amounts)?
- **Theory-Action gap**: Do choices change between theory and action mode?
- **VALUES.md effectiveness**: Do custom values change decisions?

#### 3. VALUES.md Alignment Score
```python
def calculate_alignment_score(
    judgements_baseline: list[Judgement],
    judgements_with_values: list[Judgement],
    user_expected_choices: dict[str, str],  # dilemma_id -> expected_choice_id
) -> float:
    """
    Calculate how much VALUES.md improved alignment with user.

    Returns:
        Alignment improvement score (0-1)
        - 0.0: VALUES.md had no effect
        - 0.5: VALUES.md improved alignment by 50%
        - 1.0: Perfect alignment with VALUES.md
    """
```

#### 4. Key Research Questions We Can Answer:
- Does Claude + VALUES.md match user preferences better than Claude alone?
- Which models are most responsive to custom values?
- Do certain types of values (utilitarian vs deontological) work better?
- Does temperature affect value alignment?
- Theory-action gap: Do values matter more in theory or action mode?

#### 5. Visualization
- Choice distributions by model/prompt
- Alignment scores heatmap (models × value systems)
- Confidence levels comparison
- Decision time analysis

---

## Implementation Order

**Week 1: Phase 1**
- [x] Judgement model exists
- [ ] Create judge service
- [ ] Test with 1 dilemma
- [ ] Test with 5 dilemmas

**Week 1-2: Phase 2**
- [ ] Experiment config
- [ ] Batch runner with resume
- [ ] Interactive script

**Week 2: Phase 3**
- [ ] Multi-model support
- [ ] Cost estimation

**Week 2-3: Phase 4**
- [ ] Variable expansion
- [ ] Test bias detection

**Week 3+: Phases 5-6**
- [ ] Complete system
- [ ] Analysis tools

---

## Database Schema

Already complete! We have:
- ✅ `dilemmas` table with DilemmaDB
- ✅ `judgements` table with JudgementDB
- ✅ All necessary indexes for querying

---

## Key Design Principles

1. **Save Early, Save Often**: Write each judgement to DB immediately
2. **Resumable**: Track what's done, skip completed work
3. **Cost-Aware**: Estimate and warn before large runs
4. **Fail Gracefully**: Log errors, continue with next test
5. **Rich Metadata**: Capture everything for later analysis

---

## Example Workflow (Phase 1)

```bash
# 1. Generate 5 test dilemmas (already doing)
uv run python scripts/generate_batch_interactive.py

# 2. Test judge service
uv run python scripts/test_judge.py

# 3. View results
uv run python scripts/serve.py
# Visit http://localhost:8000/judgements (new page we'll add)
```

## Example Workflow (Phase 5 - Final)

```bash
# Run full experiment
uv run python scripts/run_experiment.py

# Output:
# > Experiment Configuration:
# > - 50 dilemmas
# > - 5 models × 2 temperatures × 2 modes
# > - Variable strategy: sample 3 per dilemma
# > - Total: ~3,000 judgements
# > - Estimated cost: $15-20
# > - Estimated time: 2-3 hours
# >
# > Continue? [y/N]

# Runs overnight, saves progress

# Next morning:
uv run python scripts/analyze_results.py

# Output:
# > Experiment Results:
# > - 3,000 judgements collected
# > - Success rate: 98.5%
# > - Key findings:
# >   * Claude more consistent than others (std dev: 0.3 vs 0.8)
# >   * Theory-Action gap: 23% choice change rate
# >   * Bias detected: Amount affects GPT-4 more than others (p<0.01)
```

---

## Current Status

✅ **Complete:**
- Dilemma generation system
- Variable extraction
- Quality control
- Database models

🔜 **Next (Phase 1):**
- Judge service
- Test with 5 dilemmas
- Save judgements to DB
