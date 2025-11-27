# Dilemma Generation Prompts

This directory contains prompt templates for generating and modifying dilemmas.

## Structure

```
prompts/
├── generation/              # Create new dilemmas (Step 1)
│   ├── system.md            # System prompt (always used)
│   ├── v1_basic.md          # Simple generation
│   ├── v2_structured.md     # More structured approach
│   └── v3_creative.md       # Emphasize novelty
├── variation/               # Modify/extract from existing dilemmas
│   ├── system.md            # System prompt for variations
│   ├── make_harder.md       # Increase difficulty
│   └── extract_variables.md # Extract variables & modifiers (Step 2)
└── validation/              # Evaluate quality (future)
```

## Two-Step Generation Process

The system uses a two-phase approach to generate high-quality dilemmas with variables:

### Step 1: Generate Concrete Dilemma (`generation/*.md`)
- Primary LLM (e.g., Gemini 2.5 Flash) generates a complete, concrete scenario
- Uses specific names, amounts, roles, timeframes
- No placeholders or variables yet
- Focus: Quality, realism, ethical complexity

### Step 2: Extract Variables & Modifiers (`variation/extract_variables.md`)
- Extraction LLM (e.g., Kimi K2) analyzes the concrete dilemma
- Identifies elements to vary for bias testing (names, amounts, roles, etc.)
- Rewrites situation with `{PLACEHOLDERS}`
- Extracts 3-5 modifiers (time pressure, stakes, uncertainty, etc.)
- Focus: Systematic bias testing across dimensions

**Why two steps?**
- Better quality (LLM focuses on one task at a time)
- Works with all models (avoids Gemini's `additionalProperties` limitation)
- Optional and retroactive (can be applied to existing dilemmas)

## How Prompts Work

1. **System + User**: Each generation uses `generation/system.md` + one of the versioned prompts
2. **Template Variables**: Marked with `{variable_name}`, replaced at runtime
3. **Versioning**: Create new numbered versions to test different approaches

## Template Variables

**Generation prompts**:
- `{domain}` - AI system type
- `{actors}` - List of actors involved
- `{conflict}` - Core ethical tension
- `{stakes}` - What's at risk
- `{moral_foundation}` - Moral dimension
- `{constraints}` - Additional constraints/modifiers
- `{difficulty}` - Target difficulty (1-10)
- `{difficulty_guidance}` - Auto-generated guidance based on difficulty

**Variation prompts** (`make_harder.md`):
- `{current_difficulty}` - Original difficulty
- `{target_difficulty}` - Target difficulty
- `{situation}` - Original situation
- `{question}` - Original question
- `{choices}` - Original choices

**Extraction prompts** (`extract_variables.md`):
- No template variables - receives full dilemma in user prompt
- Outputs: `VariableExtraction` with rewritten situation, variables list, and modifiers list

## Adding New Prompts

1. Create new markdown file: `generation/v4_your_idea.md`
2. Use template variables as needed
3. Update config.yaml to include the new version
4. Test and compare results

## Difficulty Guidance (Auto-Generated)

Based on target difficulty, the system automatically adds guidance:

- **1-3 (Easy)**: Clear right answer, low stakes, complete info
- **4-6 (Medium)**: Genuine tradeoffs, moderate stakes, some uncertainty
- **7-9 (Hard)**: No clear answer, high stakes, incomplete info, time pressure
- **10 (Extreme)**: Competing valid principles, irreversible, cascading effects

This is injected into the `{difficulty_guidance}` variable.
