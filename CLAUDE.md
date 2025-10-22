# CLAUDE.md - Project Structure & Building Principles

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
│       │   └── config.py        # LLM config, test config
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
│       └── api/                 # FastAPI app (add later)
│           ├── __init__.py
│           ├── main.py          # FastAPI app
│           └── routes.py        # API routes
├── tests/                       # Unit tests (pytest)
│   ├── __init__.py
│   ├── test_config.py           # Config loading tests
│   ├── test_models.py           # Pydantic model tests
│   ├── test_services.py         # Service logic tests (mocked LLMs)
│   └── test_agents.py           # Agent tests (mocked LLMs)
├── data/                        # Generated data
│   ├── dilemmas/                # Generated dilemma sets
│   └── results/                 # Test results & analysis
├── scripts/                     # Integration tests & experiments
│   ├── test_openrouter.py       # Test real OpenRouter connectivity
│   ├── generate_dilemmas.py     # Generate dilemma dataset
│   ├── run_experiments.py       # Run LLM experiments
│   └── analyze_results.py       # Analyze experiment results
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

### 6. Data Preservation
- Save all generated dilemmas with metadata
- Log all judgements with full context
- Results should be reproducible and analyzable

### 7. Progressive Enhancement
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

## Key Design Decisions
- **Python 3.12+** for modern type hints
- **uv** for fast dependency management
- **pydantic-ai** for agent framework (over langchain/llamaindex)
- **OpenRouter** for model access (over direct API calls)
- **FastAPI** for API (when needed)
- Keep it simple, avoid over-abstraction
