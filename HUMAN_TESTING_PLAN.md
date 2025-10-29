# Human Testing & VALUES.md Generation Plan

## Overview

Build a system for humans to take ethical dilemma tests and generate personalized VALUES.md files based on their decisions.

## Current State - What We Already Have

### ✅ Existing API Endpoints

**Public (no auth required):**
- `GET /api/dilemmas` - Get all dilemmas as JSON (line 207-219)
- `GET /api/dilemma/{id}` - Get single dilemma as JSON (line 222-236)

**Protected (requires API key):**
- `GET /api/dilemmas?collection={name}&limit={n}` - Filtered list with pagination (line 546-634)
  - Supports: collection, batch_id, difficulty_min/max, tags, search, sorting
  - Returns: `{items: Dilemma[], total, limit, offset}`

### ✅ Existing Database Models

**Dilemma Model** (`src/dilemmas/models/dilemma.py`):
- Has all dilemma data including choices, variables, modifiers
- Can render with specific variable values: `dilemma.render(variable_values)`
- Already serializes to JSON via Pydantic

**Judgement Model** (`src/dilemmas/models/judgement.py`):
- Discriminated union: `judge_type: "human" | "ai"`
- **HumanJudgeDetails** includes:
  - `participant_id` (anonymous ID for linking judgements)
  - Demographics: age, gender, education_level, country, culture, professional_background
  - `values_scores`: dict[str, float] for moral foundations, etc.
  - Experimental context: recruitment_source, compensation, consent
- Common fields:
  - `choice_id`: which choice was selected
  - `confidence`: 1-10 scale
  - `reasoning`: optional text explanation
  - `response_time_ms`: how long they took
  - `variation_key`: hash of which variable values were used

**Database Tables:**
- `DilemmaDB` - stores dilemmas
- `JudgementDB` - stores both human and AI judgements

## What We Need to Build

### 1. Frontend (separate Next.js/React app)

You'll build this separately. It needs:

**Pages:**
- `/login` - Auth (email/password or social)
- `/onboarding` - Collect demographics (optional but encouraged)
- `/test` - Take the dilemma test
- `/results` - View their VALUES.md file
- `/profile` - Edit demographics, retake test

**Test Flow:**
1. Fetch dilemmas from batch: `GET /api/dilemmas?collection=bench-1`
2. For each dilemma:
   - Render situation with random variable values
   - Show choices
   - Collect: choice_id, confidence (optional slider), reasoning (optional textarea)
   - Track response_time_ms
3. Submit all judgements at end
4. Generate and display VALUES.md

### 2. New API Endpoints Needed

**GET `/api/collections/{collection_name}/dilemmas`**
- Public endpoint
- Returns all dilemmas in a specific collection/batch
- Response: `list[Dilemma]`
- Use case: Frontend fetches bench-1 test set

**POST `/api/judgements`**
- Public endpoint (no auth required)
- Submit a batch of human judgements
- Request body:
```json
{
  "participant_id": "anon-uuid",
  "demographics": {
    "age": 32,
    "gender": "non-binary",
    "education_level": "masters",
    "country": "US",
    "culture": "Western",
    "professional_background": "software_engineer",
    "device_type": "desktop"
  },
  "judgements": [
    {
      "dilemma_id": "abc123",
      "choice_id": "choice_1",
      "confidence": 8,
      "reasoning": "I chose this because...",
      "response_time_ms": 45000,
      "rendered_situation": "The actual text shown to user",
      "variable_values": {"{DOCTOR_NAME}": "Dr. Smith"},
      "modifier_indices": [0, 2]
    }
  ]
}
```
- Response: `{success: true, judgement_ids: string[]}`
- Backend creates full `Judgement` objects:
  - Sets `judge_type="human"`
  - Sets `mode="theory"` (humans don't use action mode)
  - Embeds demographics in `human_judge` field for each judgement
  - Validates: dilemma_id exists, choice_id valid for that dilemma
- All demographics fields are optional except `participant_id`

**POST `/api/values/generate`**
- Protected or participant-specific
- Generate VALUES.md file from participant's judgements
- Request body:
```json
{
  "participant_id": "anon-uuid"
}
```
- Process:
  1. Fetch all judgements for this participant
  2. Fetch corresponding dilemmas
  3. Use LLM to analyze patterns:
     - Which values they prioritize (care, fairness, loyalty, authority, sanctity)
     - How they handle conflicts (consequentialist, deontological, virtue ethics)
     - Risk tolerance, time preference, scope sensitivity
     - Consistency across similar dilemmas
  4. Generate structured VALUES.md file
- Response: `{values_md: string, confidence_score: float}`

**GET `/api/values/{participant_id}`**
- Retrieve previously generated VALUES.md
- Response: `{values_md: string, generated_at: datetime, judgements_count: int}`

### 3. VALUES.md Generation Service

**New file:** `src/dilemmas/services/values_generator.py`

```python
class ValuesGenerator:
    """Generate VALUES.md file from human judgements."""

    async def generate(
        self,
        participant_id: str,
        include_reasoning: bool = True
    ) -> tuple[str, float]:
        """
        Args:
            participant_id: Anonymous ID
            include_reasoning: Whether to include LLM reasoning in output

        Returns:
            (values_md_content, confidence_score)
        """
        # 1. Fetch all judgements for participant
        # 2. Analyze patterns with LLM
        # 3. Generate VALUES.md using template
```

**LLM Prompt Strategy:**

Use a specialized prompt to analyze judgement patterns:
- Input: List of (dilemma, choice, reasoning)
- Output: Structured values profile
- Model: Claude Sonnet 4.5 or GPT-4 for nuance

**VALUES.md Template Structure:**
```markdown
# Personal Values Profile

> Generated from 20 ethical dilemmas • {date}

## Core Values

### Primary Values
- **Care/Harm** (8.5/10): You consistently prioritize...
- **Fairness/Cheating** (7.0/10): You show strong preference for...
- **Loyalty/Betrayal** (6.0/10): You balance...

### Secondary Values
- **Authority/Subversion** (5.0/10): ...
- **Sanctity/Degradation** (4.0/10): ...

## Decision-Making Style

### Ethical Framework
You lean toward **consequentialism** (70%) - evaluating actions by outcomes...

### Conflict Resolution
When values conflict, you tend to prioritize: [order]

## Patterns Observed

### Strengths
- Consistent application of fairness principles
- Willing to make difficult tradeoffs

### Considerations
- May underweight long-term consequences
- Strong certainty even with incomplete information

## Specific Behaviors

[Examples from their actual choices]

---

*This profile is based on your responses to 20 dilemmas. It represents patterns in your ethical reasoning, not absolute truth about your character.*
```

### 4. Database Schema (Already Ready!)

**No participant table needed on research backend!**

The Next.js frontend will handle:
- User accounts and authentication
- User profiles and demographics management
- Session/progress tracking
- UI state and preferences

This backend only stores research data:
- **DilemmaDB** - stores dilemmas
- **JudgementDB** - stores judgements with embedded demographics

**Why embed demographics in each judgement?**
- ✅ Self-contained research exports (each judgement has full context)
- ✅ Temporal accuracy (demographics frozen at time of judgement)
- ✅ Research integrity (can't lose data if user deletes frontend account)
- ✅ No foreign keys → simpler queries and exports
- ✅ Privacy-friendly (backend only knows anonymous participant_id)

**Existing `HumanJudgeDetails` already has structured demographics:**
- `participant_id`: str (anonymous ID from frontend)
- `age`: int | None (1-120, validated)
- `gender`: str | None
- `education_level`: str | None
- `country`: str | None
- `culture`: str | None
- `professional_background`: str | None
- `values_scores`: dict[str, float] | None (moral foundations, etc.)
- Plus experimental context: `recruitment_source`, `device_type`, `changed_mind`, etc.

### 5. Implementation Order

**Phase 1: API Endpoints (Backend)**
1. ✅ Already have: GET `/api/dilemmas?collection={name}`
2. Create: GET `/api/collections/{collection}/dilemmas` (simpler public version)
3. Create: POST `/api/judgements` (batch submission)
4. Test with curl/Postman

**Phase 2: VALUES.md Generator**
1. Create ValuesGenerator class
2. Design LLM analysis prompt
3. Create VALUES.md template
4. Test with mock data
5. Create: POST `/api/values/generate`
6. Create: GET `/api/values/{participant_id}`

**Phase 3: Frontend Integration**
1. You build Next.js app
2. Integrate API calls
3. Design UX for dilemma presentation
4. Handle variable rendering
5. Collect judgements
6. Display VALUES.md

## Technical Decisions

### Architecture: Two-App Separation

**Frontend (Next.js App):**
- User accounts, authentication, sessions
- User profiles and demographics UI
- Test-taking interface
- Progress tracking and resume functionality
- VALUES.md display
- Sends participant_id + demographics snapshot with each judgement batch

**Backend (This Python API):**
- Research data only (dilemmas + judgements)
- No user accounts, no auth, no sessions
- Simple API key protection for admin endpoints
- Anonymous participant_id for linking judgements
- Demographics embedded in each judgement record

**Benefits:**
- ✅ Separation of concerns (app vs research data)
- ✅ Frontend can change auth without affecting research
- ✅ Research data remains self-contained and portable
- ✅ Backend stays simple and focused
- ✅ Can export/analyze data without frontend database

### Participant ID Strategy

**Frontend generates stable anonymous ID:**
- On first visit: generate UUID, store in localStorage
- Optional: upgrade to authenticated account (keeps same participant_id)
- Sends participant_id with every judgement submission
- Backend treats it as opaque identifier (no lookups, no validation)

**Backend perspective:**
- participant_id is just a string for grouping judgements
- No participant table, no foreign keys
- Can generate VALUES.md for any participant_id by querying judgements

### Variable Rendering Strategy

Each test taker gets **one random variation** per dilemma:
- Frontend picks random values from `dilemma.variables`
- Submits those values in `variable_values` field
- Stores in `variation_key` for analysis
- This ensures diversity in testing while keeping it manageable

### LLM for VALUES.md Generation

**Model:** Claude Sonnet 4.5 or GPT-4
**Temperature:** 0.3 (consistent analysis)
**Input:** All judgements with full context
**Output:** Structured values profile (use Pydantic model)

## Open Questions

1. **How many dilemmas should a human take?**
   - Minimum for valid profile: ~10-15
   - bench-1 has 20 - good starting point
   - Could do shorter "quick profile" (5-8 dilemmas)

2. **Should we randomize dilemma order?**
   - Yes - prevents order effects
   - Frontend shuffles before presenting

3. **Should we show confidence slider?**
   - Optional but valuable
   - Shows decision certainty
   - Helps identify values they're less sure about

4. **Should we require reasoning text?**
   - Optional, but encouraged
   - Provides richer data for VALUES.md
   - Maybe required for 2-3 "key" dilemmas?

5. **How do we handle incomplete tests?**
   - Save progress with partial judgements
   - Require minimum (e.g., 10) for VALUES.md generation
   - Clear messaging about progress

## Next Steps

1. **Review this plan** - Make sure it aligns with your vision
2. **Decide on auth strategy** - Anonymous vs full auth
3. **I'll implement API endpoints** - Backend work
4. **You build frontend** - React/Next.js app
5. **Test end-to-end** - With real humans!
