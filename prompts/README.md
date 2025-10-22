# Dilemma Generation Prompts

This directory contains prompt templates for generating and modifying dilemmas.

## Structure

```
prompts/
├── generation/           # Create new dilemmas
│   ├── system.md         # System prompt (always used)
│   ├── v1_basic.md       # Simple generation
│   ├── v2_structured.md  # More structured approach
│   └── v3_creative.md    # Emphasize novelty
├── variation/            # Modify existing dilemmas
│   ├── system.md
│   └── make_harder.md
└── validation/           # Evaluate quality (future)
```

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

**Variation prompts**:
- `{current_difficulty}` - Original difficulty
- `{target_difficulty}` - Target difficulty
- `{situation}` - Original situation
- `{question}` - Original question
- `{choices}` - Original choices

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
