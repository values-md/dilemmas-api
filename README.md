# VALUES.md Research Project

As AI agents make increasingly autonomous decisions on our behalf, we face a fundamental question: who is responsible for their actions? Without responsibility, there can be no real freedom. **VALUES.md** is a research project investigating how LLMs make ethical decisions and how we can guide them toward more intentional, value-aligned behavior.

## What We're Studying

This project explores how Large Language Models make ethical decisions across different conditions:
- **Ethical frameworks** (utilitarian vs deontological via VALUES.md)
- **Decision contexts** (theory vs action - believing consequences are real)
- **Environmental pressures** (time constraints, high stakes, uncertainty)
- **Demographic biases** (how model decisions vary based on names, amounts, roles)
- **Safety boundaries** (compliance with extreme or harmful ethical frameworks)

**Browse the research:** [research.values.md/research](https://research.values.md/research) - All completed experiments, findings, and downloadable data

## System Capabilities

**Infrastructure:**
- Complete dilemma data model with variables, modifiers, and tool schemas
- Three-tier quality control (prompts, validators, LLM assessment)
- Database with migrations and collections system
- Web API + HTML interface for browsing data
- Reproducible experiment framework with data export

**Current Status:** Active research phase - running systematic experiments and building evidence for AI agent ethics standards.

## Quick Start

### For Researchers: Explore the Data

**Browse experiments and findings:**
```
Visit: https://research.values.md/research
```

**Download experiment data:**
- Each experiment page has a "Download Data Bundle" button
- Contains: dilemmas.json, judgements.json, config.json, analysis scripts
- Fully reproducible and citable

**Run local analysis:**
```bash
unzip 2025-10-24-extreme-values.zip
cd 2025-10-24-extreme-values
uv run python analyze.py
```

See [research/GUIDE.md](research/GUIDE.md) for detailed reproduction instructions.

### For Developers: Understanding the System

#### Variables & Modifiers

Generated dilemmas include **variables** and **modifiers** for comprehensive bias testing:

- **Variables**: Elements that vary across test cases (e.g., `{DOCTOR_NAME}`, `{AMOUNT}`, `{PATIENT_TYPE}`)
  - Used to test for bias based on demographics, amounts, roles, etc.
  - Each variable has 2-4 diverse concrete values
  - Example: `{DOCTOR_NAME}`: ["Dr. Maria Rodriguez", "Dr. James Williams", "Dr. Wei Chen"]

- **Modifiers**: Optional overlays that change scenario dynamics
  - Time pressure: "You have 30 seconds to decide."
  - Stakes: "Multiple lives depend on this."
  - Uncertainty: "You are only 60% certain of these facts."
  - Irreversibility: "This decision cannot be undone."
  - Visibility: "Your decision will be public."

The system uses a **two-step generation process**:
1. Generate high-quality concrete dilemma (Gemini 2.5 Flash)
2. Extract 0-4 variables and 3-5 modifiers from it (Gemini 2.5 Flash)

This ensures both quality and compatibility with all LLMs.

### Quality Control

The system implements a **three-tier quality control system** to ensure high-quality dilemmas:

1. **Tier 1 - Prevention (Better Prompts)**
   - Explicit requirements with self-check checklists
   - Prevents common issues (incorrect framing, empty text, etc.) at the source
   - AI-centric framing requirements (never "You are a doctor", always "You are an AI system...")

2. **Tier 2 - Detection (Pydantic Validators)**
   - Automatic validation of all dilemma fields
   - Checks for minimum length, correct framing, variable consistency
   - Catches structural problems immediately before saving

3. **Tier 3 - Validation & Repair (LLM Assessment)**
   - Optional LLM-based quality assessment (quality, interest, realism scores)
   - Automatic repair for minor issues
   - Retry logic with best-attempt tracking
   - Can be enabled via `enable_validation: true` in config

This multi-layered approach ensures consistent, high-quality dilemma generation while minimizing API costs through early prevention.

#### Collections & Batches

The system organizes dilemmas into **collections** and **batches** for systematic testing:

**Collections**: Named test sets for standardized experiments
- Example: `"initial_experiments"`, `"standard_v1"`, `"bias_test_set"`
- Use to group related dilemmas across multiple generation runs
- Filter dilemmas by collection via API: `/api/dilemmas?collection=standard_v1`

**Batch IDs**: Track single generation runs
- Auto-generated UUID for each batch
- All dilemmas generated together get the same batch_id
- Useful for tracking generation parameters and quality

**Label existing dilemmas:**
```bash
# Label all unlabeled dilemmas
uv run python scripts/label_collection.py "initial_experiments" --unlabeled-only

# Label by date range
uv run python scripts/label_collection.py "pilot_study" --before "2025-10-29"
```

**Generate new batches with collections:**
```bash
# Interactive (recommended)
uv run python scripts/generate_batch_interactive.py
# Will prompt to select existing collection or create new one

# CLI with explicit collection
uv run python scripts/generate_batch.py 30 --collection "standard_v1"
```

### Generate Dilemmas

**Interactive batch generation** (recommended):
```bash
uv run python scripts/generate_batch_interactive.py
```

This will guide you through:
- Selecting how many dilemmas to generate
- Choosing which prompt versions to use (multi-select)
- Choosing which LLM models to use (multi-select)
- Setting difficulty range (1-10)

Features:
- Real-time progress display with progress bars
- Incremental saving with visual confirmation
- Random selection from your chosen prompts/models for each dilemma
- Diversity checking to avoid repeated domain/conflict combinations

**Generate single dilemma**:
```bash
uv run python scripts/generate_dilemma.py --difficulty 7 --save
```

**Explore dilemmas** (recommended - clean HTML interface):
```bash
uv run python scripts/serve.py
```
Then visit http://localhost:8000

**Explore database** (Datasette - SQL interface):
```bash
uv run python scripts/explore_db.py
```
Then visit http://localhost:8001/dilemmas/dilemmas

**Clear the database** (start over):
```bash
uv run python scripts/clear_db.py  # Deletes all dilemmas AND judgements
```

### Run Judgements

**Test LLMs on your dilemmas:**
```bash
uv run python scripts/test_judge.py
```

This will:
- Load all dilemmas from the database
- Run GPT-4.1 Mini on each dilemma (theory mode)
- Save judgements to the database with full metadata
- Show summary with choices and confidence levels

**View judgements:**
- Open http://localhost:8000/judgements in the web interface
- Or use Datasette: http://localhost:8001/dilemmas/judgements

**Key Features:**
- No system prompt by default (clean baseline)
- Auto-fills variables with first value if dilemma has them
- Records full decision context (model, temperature, rendered situation)
- Ready for VALUES.md experiments (provide custom system prompts)

### Test Consistency

How consistent are LLM judgements? Test the same model on the same dilemma multiple times to measure:

**Run consistency experiment:**
```bash
uv run python scripts/test_consistency.py
```

This will:
- Test 3 dilemmas with 2 models at 4 temperatures (0.0, 0.5, 1.0, 1.5)
- Run 10 repetitions per (model, dilemma, temperature) combination
- Save all judgements with `experiment_id` and `repetition_number`
- Total: 240 judgements per run

**Analyze results:**
```bash
uv run python scripts/analyze_consistency.py <experiment_id>
uv run python scripts/analyze_consistency.py --list  # Show all experiments
```

**Metrics computed:**
1. **Choice Consistency**: % that picked the same choice
2. **Reasoning Similarity**: Jaccard similarity of reasoning text
3. **Confidence Variation**: Standard deviation of confidence scores

**Expected results:**
- Temperature 0.0: ~100% choice consistency (deterministic)
- Temperature 1.0: ~50-80% choice consistency
- Higher temp → more variation in reasoning and confidence

**Configuration:**
Edit `CONFIG` in `test_consistency.py` to customize:
- Number of dilemmas to test
- Models and temperatures
- Number of repetitions

### Database Migrations with Alembic

We use Alembic for database schema migrations. This allows you to evolve the schema without losing data.

**Initial setup** (first time):
```bash
uv run alembic upgrade head
```

**After making model changes:**
```bash
# 1. Create a new migration
uv run alembic revision --autogenerate -m "description of changes"

# 2. Review the generated migration in alembic/versions/

# 3. Apply the migration
uv run alembic upgrade head
```

**Check migration status:**
```bash
uv run alembic current  # See current version
uv run alembic history  # See all migrations
```

### Running Experiments

The project includes a sophisticated experiment framework. All experiments live in `research/YYYY-MM-DD-experiment-name/`.

**Start a new experiment:**
1. Create experiment folder with `run.py`, `README.md`, `analyze.py`
2. Document hypotheses and design in README
3. Test with `--dry-run` flag
4. Run experiment and export data
5. Write findings with YAML frontmatter

**See comprehensive guides:**
- [research/index.md](research/index.md) - Experiment index and workflow
- [research/BEST_PRACTICES.md](research/BEST_PRACTICES.md) - Lessons learned
- [research/GUIDE.md](research/GUIDE.md) - Reproducibility guide

**Critical best practices:**
- Always generate and set `experiment_id` for all judgements
- Use structured `experiment_metadata` dict (not string notes)
- Test with dry-run before full runs
- Export data immediately after experiments
- Write findings with proper YAML frontmatter

## Deployment

The research site is deployed to Fly.io at **research.values.md**.

**Deploy manually:**
```bash
# First time: Install flyctl and authenticate
brew install flyctl
fly auth login

# Deploy
fly deploy

# View logs
fly logs

# SSH into instance
fly ssh console
```

**Configuration:**
- `fly.toml` - Fly.io app configuration
- `Dockerfile` - Container build
- `entrypoint.sh` - Startup script
- Environment variables set via `fly secrets set`

**Domain setup:**
```bash
fly certs add research.values.md
```

## Development

### Test Database Operations

```bash
uv run python scripts/test_db.py
```

### Run Tests

```bash
uv run pytest tests/
```

## Project Structure

See [CLAUDE.md](CLAUDE.md) for comprehensive documentation of:
- Architecture and design principles
- Building best practices
- Database patterns and migrations
- Testing philosophy
- Quality control systems
- All technical details

## Contributing

This is an active research project. Contributions welcome:

- **Report issues**: [GitHub Issues](https://github.com/values-md/dilemmas-api/issues)
- **Replicate experiments**: Download data bundles and run analyses
- **Suggest experiments**: Open an issue with research questions
- **Improve methodology**: Review [research/BEST_PRACTICES.md](research/BEST_PRACTICES.md)

## Citation

If you use this data or findings in your research:

```
VALUES.md Research Project (2025)
https://github.com/values-md/dilemmas-api
https://research.values.md
```

For specific experiments, include the experiment ID from the research page.

---

**Project Links:**
- Live Site: [research.values.md](https://research.values.md)
- GitHub: [values-md/dilemmas-api](https://github.com/values-md/dilemmas-api)
- Research Index: [research.values.md/research](https://research.values.md/research)