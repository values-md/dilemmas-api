# CLAUDE.md - Project Structure & Building Principles

## ⚠️ CRITICAL RULES FOR CLAUDE

**NEVER run batch generation scripts automatically:**
- ❌ DO NOT run `generate_bench1.py` or any batch generation scripts without explicit user request
- ❌ DO NOT start background processes for generation
- ❌ DO NOT "helpfully" regenerate data
- ✅ ONLY run generation when user explicitly asks
- ✅ ALWAYS ask before running any batch operation

**Why:** Generation is expensive, creates database records, and the user manages data carefully.

## Project Overview
Research project to test how different LLMs make ethical decisions under various conditions. Foundation for the VALUES.md file format standard for AI agent ethics.

## Folder Structure

```
dilemmas/
├── src/
│   └── dilemmas/
│       ├── __init__.py
│       ├── models/              # Pydantic models
│       │   ├── __init__.py
│       │   ├── dilemma.py       # Dilemma data model
│       │   ├── judgement.py     # Judgement/decision data model
│       │   ├── config.py        # LLM config, test config
│       │   └── db.py            # SQLModel database models
│       ├── db/                  # Database layer
│       │   ├── __init__.py
│       │   └── database.py      # Connection, session management
│       ├── services/            # Business logic layer
│       │   ├── __init__.py
│       │   ├── generator.py     # Dilemma generation service
│       │   └── judge.py         # LLM judgement service
│       ├── llm/                 # LLM integration layer
│       │   ├── __init__.py
│       │   ├── openrouter.py    # OpenRouter client
│       │   └── agents.py        # pydantic-ai agent definitions
│       ├── tools/               # Tools for agents (action mode)
│       │   ├── __init__.py
│       │   └── actions.py       # Mock actions for dilemmas
│       └── api/                 # FastAPI app
│           ├── __init__.py
│           ├── app.py           # FastAPI app
│           └── templates/       # Jinja2 HTML templates
│               ├── base.html
│               ├── index.html   # List all dilemmas
│               └── dilemma.html # View single dilemma
├── tests/                       # Unit tests (pytest)
│   ├── __init__.py
│   ├── test_config.py           # Config loading tests
│   ├── test_models.py           # Pydantic model tests
│   ├── test_services.py         # Service logic tests (mocked LLMs)
│   └── test_agents.py           # Agent tests (mocked LLMs)
├── data/                        # Generated data
│   ├── dilemmas.db              # SQLite database
│   ├── dilemmas/                # Generated dilemma sets
│   └── results/                 # Test results & analysis
├── alembic/                     # Database migrations
│   ├── versions/                # Migration scripts
│   ├── env.py                   # Alembic environment config
│   └── README                   # Alembic readme
├── scripts/                     # Integration tests & experiments
│   ├── init_db.py               # Initialize database schema (deprecated)
│   ├── test_db.py               # Test database CRUD operations
│   ├── test_openrouter.py       # Test real OpenRouter connectivity
│   ├── generate_dilemmas.py     # Generate dilemma dataset
│   ├── run_experiments.py       # Run LLM experiments
│   └── analyze_results.py       # Analyze experiment results
├── alembic.ini                  # Alembic configuration
├── pyproject.toml
├── pytest.ini
├── .env.example
└── README.md
```

## Building Principles

### 1. Separation of Concerns
- **models/** - Pure data structures, no business logic
- **services/** - Core business logic, orchestration
- **llm/** - All LLM interactions isolated here
- **tools/** - Action implementations for testing theory vs action gap
- **api/** - HTTP layer, thin controllers

### 2. Pydantic-First
- Use Pydantic models everywhere for validation
- Leverage pydantic-ai for agent definitions
- Type hints on everything
- Clear data contracts between layers

### 3. Configuration Over Code
- Store LLM configs, test parameters as data
- Easy to add new models/providers
- Reproducible experiments via config snapshots

### 4. Theory vs Action Mode
- Services should support both modes explicitly
- Theory mode: agent responds with reasoning
- Action mode: agent believes it's real, calls tools
- Same dilemma, different interfaces

### 5. Testing Philosophy
This is a **research project**, not production software. We balance proper testing with pragmatism:

**tests/** - Automated unit tests with pytest
- Test pydantic models (validation, edge cases)
- Test services with **mocked** LLM calls (no API usage)
- Test core logic that shouldn't break
- Fast, deterministic, no external dependencies
- Run with: `uv run pytest`

**scripts/** - Manual integration tests & experiments
- Real LLM API calls for verification
- Experiment runners that generate data
- Manual checks during development
- Things you want to see actual output from
- Examples: `test_openrouter.py`, `generate_dilemmas.py`

**What we DO:**
- ✓ Unit tests for models and core logic
- ✓ Mock LLM responses in unit tests
- ✓ Integration scripts for real LLM testing
- ✓ Deterministic test sets with fixed seeds

**What we DON'T do:**
- ✗ Full TDD (test-first development)
- ✗ 100% coverage requirements
- ✗ Heavy mocking of internal code
- ✗ Tests for exploratory/research code

### 6. Database & Persistence
**SQLModel + JSON Hybrid Approach**

We use SQLModel (built on SQLAlchemy 2.0) with a JSON hybrid pattern:
- **Domain models** (Pydantic): Rich validation, business logic (e.g., `Dilemma`)
- **DB models** (SQLModel): Thin persistence layer (e.g., `DilemmaDB`)
- **JSON storage**: Complex nested objects stored as JSON in TEXT columns
- **Indexed fields**: Key fields (id, tags, difficulty, created_by) indexed for queries

**Why this approach:**
- Keep Pydantic models for validation
- Easy querying/filtering on indexed fields
- Simple database schema
- **Database agnostic**: Switch SQLite → Postgres → D1 with just connection string
- No ORM impedance mismatch for complex nested data

**Pattern:**
```python
# Save
db_model = DilemmaDB.from_domain(dilemma)
session.add(db_model)

# Load
db_model = await session.get(DilemmaDB, id)
dilemma = db_model.to_domain()
```

**Database location:**
- Development: `data/dilemmas.db` (SQLite)
- Production: Postgres on Neon or Cloudflare D1

**Database Migrations (Alembic):**

We use Alembic for schema migrations. This allows us to evolve the database schema without losing data.

**Key commands:**
```bash
# Create a new migration after model changes
uv run alembic revision --autogenerate -m "description of changes"

# Apply migrations
uv run alembic upgrade head

# Check current migration version
uv run alembic current

# View migration history
uv run alembic history

# Rollback one migration
uv run alembic downgrade -1
```

**Migration workflow:**
1. Modify models in `src/dilemmas/models/db.py`
2. Run `alembic revision --autogenerate -m "add new field"`
3. Review generated migration in `alembic/versions/`
4. Apply with `alembic upgrade head`

**Configuration:**
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Configured to use our SQLModel metadata
- `alembic/versions/` - Migration scripts

**Note:** Always review autogenerated migrations before applying! Alembic detects most changes but may need manual adjustments for complex schema changes.

**Production Deployment:**

We use **Fly.io + Neon Postgres** for production deployment.

**Key Architecture Decisions:**
- **Fly.io**: Docker container hosting with automatic SSL and global edge network
- **Neon Postgres**: Serverless Postgres with generous free tier, auto-scaling
- **Automatic Migrations**: `entrypoint.sh` runs `alembic upgrade head` on every deploy

**Critical Implementation Details:**

1. **Database URL Handling** (`src/dilemmas/db/database.py`):
   - Automatically reads `DATABASE_URL` from environment
   - Cleans Neon connection strings for asyncpg compatibility:
     - Converts `postgresql://` → `postgresql+asyncpg://`
     - Converts `sslmode=require` → `ssl=require`
     - Removes `channel_binding` parameter
   - Works for both local SQLite (when `DATABASE_URL` not set) and production Postgres

2. **Alembic Environment** (`alembic/env.py`):
   - Reads `DATABASE_URL` from environment (not hardcoded)
   - Applies same URL cleaning for migrations
   - Ensures migrations run against Postgres in production, SQLite locally

3. **DateTime Normalization** (`src/dilemmas/models/db.py`):
   - `DilemmaDB.from_domain()` and `JudgementDB.from_domain()` normalize datetimes
   - Converts timezone-aware → naive UTC for Postgres `TIMESTAMP WITHOUT TIME ZONE`
   - Prevents "can't subtract offset-naive and offset-aware datetimes" errors

4. **Data Sync** (`scripts/sync_*_to_prod.py`):
   - Sync local SQLite data → production Postgres
   - Uses `.to_domain()` → `.from_domain()` pattern to populate all indexed fields
   - Supports collection filtering and dry-run mode

**Deployment Workflow:**
```bash
# Set secrets (first time only)
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set OPENROUTER_API_KEY="..."
fly secrets set API_KEY="..."

# Deploy (migrations run automatically)
fly deploy

# Sync existing data from local
uv run python scripts/sync_dilemmas_to_prod.py --dry-run
uv run python scripts/sync_dilemmas_to_prod.py
uv run python scripts/sync_judgements_to_prod.py
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide with troubleshooting.

### 7. FastAPI Web Interface

We have a FastAPI web app for exploring dilemmas with a clean HTML interface:

**Features:**
- List all dilemmas with metadata, tags, difficulty
- View individual dilemmas with all details, choices, variables
- Clean, responsive HTML interface (better UX than Datasette for browsing)
- JSON API endpoints for programmatic access

**Routes:**
- `GET /` - HTML page listing all dilemmas
- `GET /dilemma/{id}` - HTML page showing single dilemma
- `GET /api/dilemmas` - JSON list of all dilemmas
- `GET /api/dilemma/{id}` - JSON single dilemma

**Start the server:**
```bash
uv run python scripts/serve.py  # Visit http://localhost:8000
```

**When to use what:**
- **FastAPI** (`serve.py`): Human-friendly browsing, clean UI, click through dilemmas
- **Datasette** (`explore_db.py`): SQL queries, data analysis, JSON inspection

### 8. Data Preservation
- Save all generated dilemmas with metadata
- Log all judgements with full context
- Results should be reproducible and analyzable

### 8.1. Experiment Best Practices

**CRITICAL: Always set experiment_id for experiments**

Every experiment runner script (`research/*/run.py`) MUST:
1. Import `uuid` and generate `experiment_id = str(uuid.uuid4())` at the start
2. Set `judgement.experiment_id = experiment_id` for EVERY judgement
3. Print the experiment_id at the end with export instructions

Without experiment_id, you cannot use `export_experiment_data.py` to extract and analyze results!

Example:
```python
import uuid

async def run_experiment():
    experiment_id = str(uuid.uuid4())  # Generate ONCE at start
    console.print(f"Experiment ID: {experiment_id}")

    for ... in experiment_plan:
        judgement = await judge.judge_dilemma(...)
        judgement.experiment_id = experiment_id  # Set for EACH judgement
        # ... save to database

    console.print(f"Export: uv run python scripts/export_experiment_data.py {experiment_id} ...")
```

**CRITICAL: Balanced Variation Counts**

⚠️ **ALWAYS design for 50-100 variations per dilemma**

When extracting variables, avoid combinatorial explosion:
- ❌ **BAD:** 4 variables × 4 values each = 256 variations per dilemma
- ✅ **GOOD:** 2-3 variables × 3-4 values each = 9-64 variations per dilemma

**Why this matters:**
- Unbalanced variation counts create statistical bias (a few dilemmas dominate all conclusions)
- High-variation dilemmas cost 10-50× more than low-variation dilemmas
- Aggregate metrics become misleading when top 4 dilemmas represent 64% of data

**Before finalizing experiment design:**
1. Calculate variation count for EACH dilemma
2. Verify all dilemmas are in 50-100 range
3. If some are too high (>100), reduce variables or sample down
4. If some are too low (<50), add variables or increase values

**Quick check:**
```python
variation_count = 1
for var, values in dilemma.variables.items():
    variation_count *= len(values)

if not 50 <= variation_count <= 100:
    print(f"⚠️ Variation count {variation_count} outside target range!")
```

See `research/EXPERIMENT_DESIGN_GUIDELINES.md` for comprehensive design principles.

See `research/index.md` for full experiment workflow documentation.

### 9. Quality Control System

Since LLMs are unpredictable, we implement a **three-tier quality control system** to ensure high-quality dilemma generation:

**Tier 1: Prevention (Better Prompts)**
- Explicit requirements with self-check checklists built into generation prompts
- CRITICAL REQUIREMENTS section that LLM must verify before outputting
- Prevents common issues at the source (incorrect framing, empty text, etc.)
- AI-centric framing requirements (never "You are a doctor", always "You are an AI system...")
- Files: `prompts/generation/system.md`, `prompts/generation/*.md`

**Tier 2: Detection (Pydantic Field Validators)**
- `@field_validator` decorators on Dilemma model validate all fields
- Checks for minimum length, correct framing, variable consistency
- Catches structural problems immediately during structured output parsing
- Raises ValidationError if issues found, triggering retry or fallback
- Files: `src/dilemmas/models/dilemma.py`

**Tier 3: Validation & Repair (LLM Assessment)**
- Optional LLM-based quality assessment with structured output
- Evaluates quality_score, interest_score, realism_score (0-10 scale)
- Identifies issues with severity levels (minor, major, critical)
- Automatic repair for minor issues via separate repair agent
- Retry logic with best-attempt tracking if quality below threshold
- Files: `src/dilemmas/models/validation.py`, `src/dilemmas/services/validator.py`, `prompts/validation/`

**Configuration:**
```yaml
generation:
  enable_validation: false  # Set to true to enable Tier 3
  min_quality_score: 7.0    # Minimum acceptable quality
```

**Usage:**
```python
# Standard generation (Tier 1 + Tier 2)
dilemma = await generator.generate_random(difficulty=7)

# With validation (all three tiers)
dilemma, validation = await generator.generate_with_validation(
    seed=seed,
    max_attempts=3,
    min_quality_score=7.0,
    enable_validation=True
)
```

**Why three tiers?**
- Early prevention is cheaper than repair
- Layered defense catches different types of issues
- Optional Tier 3 for when quality is critical (can be expensive)
- Graceful degradation: best attempt returned if all retries fail

### 10. Progressive Enhancement
- Start simple: models → services → agents
- Add FastAPI layer only when needed
- Don't build what we don't need yet

## Environment Variables
```
OPENROUTER_API_KEY=...
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
DEFAULT_TEMPERATURE=1.0
```

## Development Workflow
1. Define models first
2. Build services with simple logic
3. Integrate LLMs via pydantic-ai
4. Create test scripts
5. Add API layer when frontend is needed

## Common Tasks

**Run Tests:**
```bash
uv run pytest                    # All unit tests
uv run pytest -v                 # Verbose output
uv run pytest tests/test_dilemma.py  # Specific test file
```

**Database Operations:**
```bash
# Migrations (recommended way to manage schema)
uv run alembic upgrade head              # Apply all pending migrations
uv run alembic revision --autogenerate -m "description"  # Create new migration
uv run alembic current                   # Check current migration version

# Legacy/Testing
uv run python scripts/init_db.py         # Direct schema initialization (deprecated, use Alembic)
uv run python scripts/test_db.py         # Test CRUD operations
uv run python scripts/explore_db.py      # Launch Datasette web UI
```

**Integration Tests:**
```bash
uv run python scripts/test_openrouter.py  # Test OpenRouter connectivity
```

**Explore Dilemmas:**
```bash
uv run python scripts/serve.py       # FastAPI web UI (recommended)
# Opens at http://localhost:8000 - clean interface for browsing dilemmas

uv run python scripts/explore_db.py  # Datasette (SQL queries)
# Opens at http://localhost:8001 - great for JSON inspection and SQL
```

**Sync to Production:**
```bash
# Preview what would be synced (dry-run mode)
uv run python scripts/sync_dilemmas_to_prod.py --dry-run
uv run python scripts/sync_judgements_to_prod.py --dry-run

# Sync all local dilemmas to production
uv run python scripts/sync_dilemmas_to_prod.py

# Sync specific collections
uv run python scripts/sync_dilemmas_to_prod.py --collections "initial_experiments,standard_v1"
uv run python scripts/sync_judgements_to_prod.py --collections initial_experiments

# Sync judgements for a specific experiment
uv run python scripts/sync_judgements_to_prod.py --experiment-id abc123...

# Only sync judgements if their dilemmas exist in production
uv run python scripts/sync_judgements_to_prod.py --only-with-dilemmas
```

**Requirements:**
- Set `PROD_DATABASE_URL` in `.env` (Neon/Postgres connection string)
- Scripts compare by ID and only add missing records (safe, won't overwrite)
- Shows preview table and asks for confirmation before syncing
- Both dilemmas and judgements can be filtered by collection

## Key Design Decisions
- **Python 3.12+** for modern type hints
- **uv** for fast dependency management
- **pydantic-ai** for agent framework (over langchain/llamaindex)
- **OpenRouter** for model access (over direct API calls)
- **SQLModel + Alembic** for database (JSON hybrid + migrations)
- **FastAPI** for API (when needed)
- Keep it simple, avoid over-abstraction

### 11. Two-Step Generation: Concrete → Variable Extraction

**The Challenge:**
We need to generate high-quality dilemmas with variables for bias testing (e.g., `{DOCTOR_NAME}`, `{AMOUNT}`) and modifiers for scenario dynamics (time pressure, stakes, uncertainty). However, Gemini doesn't support `additionalProperties` in JSON Schema, which breaks `dict[str, list[str]]` structured output.

**The Solution: Two-Step Generation**

1. **Step 1: Generate Concrete Dilemma** (Primary LLM)
   - Focus on quality and coherence
   - Generate a complete, concrete scenario
   - No variables yet - e.g., "Dr. Maria Rodriguez, a senior cardiologist..."
   - Model: Gemini 2.5 Flash (temperature 1.0) for creativity

2. **Step 2: Extract Variables & Modifiers** (Extraction LLM)
   - Analyze the concrete dilemma
   - **Selectively** identify 0-4 elements to vary for bias testing
   - Rewrite with `{PLACEHOLDERS}` only for high-impact variables
   - Extract 3-5 modifiers for scenario dynamics
   - Model: Gemini 2.5 Flash (temperature 0.3) for consistency
   - Uses `list[Variable]` instead of dict (Gemini-compatible)
   - **Quality over quantity**: Only extract variables with high impact on bias testing

**Benefits:**
- ✓ Works with any model (no schema limitations)
- ✓ Better quality (LLM focuses on one task at a time)
- ✓ Optional (toggle via config: `add_variables: true`)
- ✓ Retroactive (can apply to existing dilemmas)
- ✓ Flexible (different models for each step)
- ✓ Avoids combinatorial explosion (0-4 variables instead of 10+)

**Configuration:**
```yaml
generation:
  add_variables: true                      # Enable two-step process
  variable_model: google/gemini-2.5-flash  # Extraction model (100% success rate)
```

**Variable Extraction Strategy:**
- **0-4 variables maximum** (quality over quantity)
- Only extract variables with HIGH impact on testing bias
- If no meaningful variables exist, return empty list (that's fine!)
- Each variable exponentially increases test combinations
- Example: 4 variables × 3 values = ~81 combinations vs. 10 variables × 3 values = ~59,000 combinations

**File Organization:**
- `src/dilemmas/models/extraction.py` - `VariableExtraction` model
- `prompts/variation/extract_variables.md` - Extraction prompt
- `src/dilemmas/services/generator.py` - `variablize_dilemma()` method

**Example:**
```python
# Step 1: Generate concrete dilemma
gen = DilemmaGenerator()
dilemma = await gen.generate_from_seed(seed)
# situation: "Dr. Maria Rodriguez made an error affecting an elderly patient..."

# Step 2: Extract variables
dilemma = await gen.variablize_dilemma(dilemma)
# situation_template: "{DOCTOR_NAME} made an error affecting {PATIENT_TYPE}..."
# variables: {
#   "{DOCTOR_NAME}": ["Dr. Maria Rodriguez", "Dr. James Williams", "Dr. Wei Chen"],
#   "{PATIENT_TYPE}": ["an elderly patient", "a young adult", "a child"]
# }
# modifiers: [
#   "You have 5 minutes to decide.",
#   "The hospital's accreditation is at stake.",
#   "Some information may be incomplete."
# ]
```

**Variables vs Modifiers:**
- **Variables**: Elements in the situation that vary (names, amounts, roles)
  - Used for bias testing (gender, ethnicity, socioeconomic status)
  - Embedded in situation template with `{PLACEHOLDERS}`
- **Modifiers**: Optional overlays that change scenario dynamics
  - Time pressure, stakes, uncertainty, irreversibility, visibility
  - Appended to situation as separate sentences
  - Test how contextual factors affect decisions
