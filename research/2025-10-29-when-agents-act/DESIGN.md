# bench-1 Baseline: Experiment Design Documentation

**Experiment ID:** `b191388e-3994-4ebd-96cc-af0d033c5230`
**Created:** 2025-10-29
**Status:** In Progress

## Research Question

What is the natural ethical decision-making behavior of major LLMs across comprehensive dilemmas and demographic variations?

## Experiment Design

### Models (4 total)
1. **OpenAI GPT-5** (`openai/gpt-5`)
2. **Anthropic Claude 4.5 Sonnet** (`anthropic/claude-sonnet-4.5`)
3. **Google Gemini 2.5 Pro** (`google/gemini-2.5-pro`)
4. **xAI Grok-4** (`x-ai/grok-4`) - *Note: Uses extended reasoning, significantly slower*

### Judgement Modes (2 total)
- **Theory Mode**: Model analyzes the dilemma and explains what should be done
- **Action Mode**: Model believes it's actually in the situation and must act using provided tools

### Configuration
- **Temperature:** 1.0 (standard, allows natural variation)
- **Repetitions:** 1 (single pass per configuration)
- **Concurrent Requests:** 5 (rate limiting)

## Dilemma Collection: bench-1

### Overview
- **Total Dilemmas:** 20
- **Difficulty Range:** 1-10 (broad spectrum)
- **Total Variable Combinations:** 1,601
- **Average Choices per Dilemma:** 2.8

### Dilemma List

#### 1. Algorithm Audit Under Pressure
- **Difficulty:** 7/10
- **Choices:** 3
- **Variables:** 2 (16 combinations)
- **Theme:** Professional integrity vs. organizational pressure

#### 2. Autonomous Vehicle Software Update Dilemma
- **Difficulty:** 6/10
- **Choices:** 2
- **Variables:** 4 (256 combinations)
- **Theme:** Safety trade-offs in autonomous systems

#### 3. Conflicting Data Disclosure
- **Difficulty:** 6/10
- **Choices:** 3
- **Variables:** 1 (4 combinations)
- **Theme:** Transparency vs. privacy

#### 4. Credit Scoring AI: The Glitch
- **Difficulty:** 8/10
- **Choices:** 2
- **Variables:** 1 (4 combinations)
- **Theme:** Fairness in algorithmic decision-making

#### 5. Fitness Tracker Epidemic Protocol
- **Difficulty:** 5/10
- **Choices:** 3
- **Variables:** 2 (16 combinations)
- **Theme:** Public health vs. individual privacy

#### 6. Genetic Counseling AI: Border Agent Dilemma
- **Difficulty:** 3/10
- **Choices:** 3
- **Variables:** 2 (8 combinations)
- **Theme:** Medical privacy at borders

#### 7. Predictive Policing Dilemma
- **Difficulty:** 4/10
- **Choices:** 3
- **Variables:** 1 (4 combinations)
- **Theme:** Justice vs. prevention

#### 8. Pricing Optimizer Dilemma: Revenue vs. Whistleblower
- **Difficulty:** 5/10
- **Choices:** 3
- **Variables:** 4 (108 combinations)
- **Theme:** Corporate loyalty vs. ethical reporting

#### 9. Public Services Prioritization
- **Difficulty:** 1/10
- **Choices:** 2
- **Variables:** 2 (16 combinations)
- **Theme:** Resource allocation in public services

#### 10. Refugee Hiring Dilemma
- **Difficulty:** 6/10
- **Choices:** 3
- **Variables:** 2 (16 combinations)
- **Theme:** Humanitarian concerns vs. legal compliance

#### 11. Species Tracker Accuracy vs. Public Perception
- **Difficulty:** 4/10
- **Choices:** 2
- **Variables:** 4 (81 combinations)
- **Theme:** Scientific accuracy vs. public trust

#### 12. Species Tracker Dilemma: Disclosure or Omission
- **Difficulty:** 7/10
- **Choices:** 3
- **Variables:** 2 (12 combinations)
- **Theme:** Environmental protection vs. development

#### 13. The Echo Chamber Recommender
- **Difficulty:** 9/10
- **Choices:** 4
- **Variables:** 1 (4 combinations)
- **Theme:** Engagement vs. intellectual diversity

#### 14. The Interpreter's Dilemma
- **Difficulty:** 5/10
- **Choices:** 3
- **Variables:** 3 (64 combinations)
- **Theme:** Accuracy vs. cultural sensitivity in translation

#### 15. The Transparent Mind
- **Difficulty:** 10/10
- **Choices:** 3
- **Variables:** 4 (256 combinations)
- **Theme:** Mental privacy vs. therapeutic effectiveness

#### 16. The Union Newsletter Dilemma
- **Difficulty:** 3/10
- **Choices:** 2
- **Variables:** 4 (192 combinations)
- **Theme:** Labor rights vs. employer control

#### 17. Unattributed Art and Health Risks
- **Difficulty:** 9/10
- **Choices:** 3
- **Variables:** 2 (16 combinations)
- **Theme:** Artistic attribution vs. public safety

#### 18. Unconventional Language Coach
- **Difficulty:** 8/10
- **Choices:** 3
- **Variables:** 4 (256 combinations)
- **Theme:** Linguistic diversity vs. standardization

#### 19. Unsanctioned A.I. Surgery
- **Difficulty:** 10/10
- **Choices:** 3
- **Variables:** 4 (256 combinations)
- **Theme:** Medical innovation vs. regulatory compliance

#### 20. Welfare Database Access
- **Difficulty:** 2/10
- **Choices:** 3
- **Variables:** 2 (16 combinations)
- **Theme:** Service delivery vs. privacy

## Combinatorial Calculation

### Formula
```
Total Judgements = Models × Dilemmas × Variable Combinations × Modes
```

### Breakdown by Dilemma
| Dilemma | Variables | Combinations | Per Model | All Models |
|---------|-----------|--------------|-----------|------------|
| Algorithm Audit | 2 | 16 | 32 | 128 |
| Autonomous Vehicle | 4 | 256 | 512 | 2,048 |
| Conflicting Data | 1 | 4 | 8 | 32 |
| Credit Scoring | 1 | 4 | 8 | 32 |
| Fitness Tracker | 2 | 16 | 32 | 128 |
| Genetic Counseling | 2 | 8 | 16 | 64 |
| Predictive Policing | 1 | 4 | 8 | 32 |
| Pricing Optimizer | 4 | 108 | 216 | 864 |
| Public Services | 2 | 16 | 32 | 128 |
| Refugee Hiring | 2 | 16 | 32 | 128 |
| Species Tracker (Accuracy) | 4 | 81 | 162 | 648 |
| Species Tracker (Disclosure) | 2 | 12 | 24 | 96 |
| Echo Chamber | 1 | 4 | 8 | 32 |
| Interpreter | 3 | 64 | 128 | 512 |
| Transparent Mind | 4 | 256 | 512 | 2,048 |
| Union Newsletter | 4 | 192 | 384 | 1,536 |
| Unattributed Art | 2 | 16 | 32 | 128 |
| Language Coach | 4 | 256 | 512 | 2,048 |
| A.I. Surgery | 4 | 256 | 512 | 2,048 |
| Welfare Database | 2 | 16 | 32 | 128 |
| **TOTAL** | - | **1,601** | **3,202** | **12,808** |

### Per-Model Breakdown
- **Total per model:** 3,202 judgements
  - Theory mode: 1,601 judgements
  - Action mode: 1,601 judgements

### Full Experiment Total
- **4 models × 3,202 = 12,808 total judgements**

## Variable Design Strategy

### Purpose of Variables
Variables test for **demographic and contextual biases** by systematically varying:
- Names (testing for gender/ethnicity bias)
- Roles/positions (testing for authority bias)
- Amounts/quantities (testing for scale sensitivity)
- Communication styles (testing for cultural bias)
- Crowd responses (testing for conformity bias)
- Contact types (testing for formality bias)

### Variable Extraction Philosophy
Variables are **selectively extracted** (0-4 per dilemma) to:
- Focus on high-impact bias testing opportunities
- Avoid combinatorial explosion
- Maintain statistical power while keeping cost manageable

### Example: Unconventional Language Coach (256 combinations)
```
{PARTICIPANT_NAME}: ["Elara", "Jamal", "Svetlana", "Raj"]  # 4 values
{COMMUNICATION_STYLE}: [
  "highly unconventional grammar and vocabulary",
  "standard grammar with strong accent",
  "code-switching between languages",
  "minimalist, concise speech style"
]  # 4 values
{UNDERSTOOD_LEVEL}: [
  "she's clearly understood",
  "she's somewhat understood",
  "they're understood with difficulty",
  "they're not understood"
]  # 4 values
{CROWD_RESPONSE}: ["enthusiastically", "indifferently", "confused", "hostile"]  # 4 values

Total: 4 × 4 × 4 × 4 = 256 combinations
```

## Cost & Time Estimates

### Original Estimates (All 4 Models)
- **Total Cost:** ~$62
- **Estimated Time:** ~14 hours (with 5 concurrent requests)
- **Rate:** ~15 judgements/minute (all models)

### Actual Performance Observations
- **Fast Models** (GPT-5, Claude 4.5, Gemini 2.5 Pro): 6-33 seconds per judgement
- **Grok-4** (with extended reasoning): 38 seconds per judgement
- **Average Throughput:** ~10-15 judgements/minute across all models

### Current Status (as of restart)
- **Models Running:** 3 (excluding Grok-4 temporarily)
- **Remaining:** ~2,966 judgements for fast models
- **Estimated Completion:** 3-4 hours

## Technical Implementation

### Batch Processing
- **Batch Size:** 100 judgements
- **Concurrent Requests:** 5 (per semaphore)
- **Shuffle:** Randomized to distribute models evenly across batches

### Retry Logic
- **Max Retries:** 3
- **Backoff:** Exponential (2s, 4s, 8s)
- **Rate Limit Handling:** Automatic retry with backoff

### Checkpointing
- **Frequency:** Every 50 completed judgements
- **Resume:** Automatic resume from last checkpoint
- **Duplicate Prevention:** Checks by (model_id, dilemma_id, variation_key, mode)

### Logging
- **Main Log:** `experiment.log` - High-level progress
- **Debug Log:** `logs/experiment_debug.log` - Detailed API call timing and errors
- **Rotation:** 10MB per file, keeps 5 backups

## Data Storage

### Database Schema
All judgements stored in `data/dilemmas.db`:
- **Indexed Fields:** experiment_id, judge_id, dilemma_id, mode, variation_key
- **Full Data:** Complete judgement stored as JSON in `data` column
- **Resume Support:** Efficient querying of completed judgements by unique key

### Judgement Metadata
Each judgement includes:
- `experiment_id`: Links to this experiment
- `variation_key`: MD5 hash of variable values
- `rendered_situation`: Situation with variables substituted
- `variable_values`: Dict of {placeholder: value}
- `choice_id`: Selected choice
- `confidence`: Model's confidence (0-10)
- `reasoning`: Model's explanation
- `response_time_ms`: API response time

## Limitations and Implications

### Variation Count Imbalance

**The Issue:**
The systematic variable combinations create a highly uneven distribution of judgements across dilemmas:

- **Top 4 dilemmas** (256 variations each): 64% of all judgements (8,192 / 12,808)
- **Top 8 dilemmas** (>500 judgements each): 92% of all judgements (11,752 / 12,808)
- **Bottom 6 dilemmas** (≤100 judgements each): 2.2% of all judgements (288 / 12,808)

**Why This Happened:**
Variables were extracted to test specific bias hypotheses (0-4 variables per dilemma). Dilemmas with rich bias-testing opportunities (names, roles, communication styles, crowd responses) naturally generated more variations. This was intentional for bias detection but creates statistical imbalance.

**Difficulty vs. Variation Distribution:**

| Difficulty | Dilemmas | Avg Variations | Range |
|------------|----------|----------------|--------|
| 1-3 (Low) | 3 | 75 | 16-192 |
| 4-6 (Medium) | 8 | 95 | 4-256 |
| 7-10 (High) | 9 | 140 | 16-256 |

**Key Observation:** No strong correlation between difficulty and variation count. High-variation dilemmas span difficulty levels (e.g., Union Newsletter at difficulty 3 has 192 variations, while A.I. Surgery at difficulty 10 has 256).

### What We Can Conclude

**SAFE Conclusions (Robust to Imbalance):**

1. **Within-Dilemma Analysis**
   - Variable effects within each dilemma (bias detection)
   - Theory-action gaps per dilemma
   - Model differences per dilemma
   - All models see same distribution, so comparative conclusions are valid

2. **Cross-Dilemma Patterns**
   - Patterns that appear consistently across ALL 20 dilemmas (regardless of size)
   - Qualitative themes emerging from diverse scenarios
   - Model-level behavioral signatures that transcend specific dilemmas

3. **Deep-Dive on High-Variation Dilemmas**
   - **Autonomous Vehicle Software Update** (256 variations): Safety trade-offs in autonomous systems
   - **The Transparent Mind** (256 variations): Mental privacy vs. therapeutic effectiveness
   - **Unconventional Language Coach** (256 variations): Linguistic diversity vs. standardization
   - **Unsanctioned A.I. Surgery** (256 variations): Medical innovation vs. regulatory compliance

   These 4 dilemmas provide statistically powerful analysis of:
   - Demographic bias patterns (names, roles, communication styles)
   - Contextual sensitivity (crowd response, understanding levels)
   - Scale effects (amounts, time pressure)

4. **Stratified Analysis**
   - Report metrics separately for small/medium/large dilemmas
   - Check if patterns hold across size categories
   - Use confidence intervals (wider for small dilemmas)

**RISKY Conclusions (Dominated by Imbalance):**

1. **Overall Aggregate Metrics**
   - "Average consensus rate" → Dominated by 4 high-variation dilemmas
   - "Most controversial dilemma" → May just be the one with most data points
   - "Overall choice distribution" → Weighted 64% by 4 dilemmas

2. **Cross-Dilemma Comparisons Without Weighting**
   - Comparing difficulty levels without equal weighting per dilemma
   - Ranking dilemmas by raw metrics rather than normalized scores

### Analysis Strategy

**Approach 1: Variation-Weighted (Default)**
- Use all 12,808 judgements with natural weighting
- **Best for:** Model comparison, overall patterns
- **Reports:** "Across 12,808 judgements in 20 dilemmas..."
- **Advantage:** Maximum statistical power
- **Limitation:** Dominated by high-variation dilemmas

**Approach 2: Dilemma-Weighted (Equal Weight)**
- Calculate metrics per dilemma, then average
- **Best for:** Cross-dilemma generalizations
- **Reports:** "Across 20 dilemmas (weighted equally)..."
- **Advantage:** Every dilemma contributes equally
- **Limitation:** Reduces power, high variance for small dilemmas

**Approach 3: Stratified Reporting (Recommended)**
- Report both variation-weighted and dilemma-weighted
- Add size-category breakdowns (small/medium/large)
- Highlight patterns that hold across all approaches
- **Reports:** "Variation-weighted: X%; Dilemma-weighted: Y%; Pattern holds across size categories"

**Approach 4: Deep-Dive + Survey**
- Intensive analysis of 4 high-variation dilemmas (statistical power)
- Survey analysis of all 20 dilemmas (breadth)
- **Reports:** "Deep analysis of 4 high-variation scenarios reveals...; Survey of all 20 dilemmas shows..."

### What This Data Is Best For

**Excellent For:**
1. ✅ **Bias detection** - High-variation dilemmas specifically designed for this
2. ✅ **Model behavioral fingerprinting** - Each model sees same distribution
3. ✅ **Theory-action gap analysis** - Paired comparisons within dilemmas
4. ✅ **Variable sensitivity mapping** - Which contextual factors matter most
5. ✅ **Deep case studies** - 4 high-variation dilemmas with rich statistical power

**Good For (With Caveats):**
1. ⚠️ **Cross-dilemma patterns** - Use equal weighting and report both metrics
2. ⚠️ **Difficulty correlation** - Control for variation count in analysis
3. ⚠️ **Overall consensus rates** - Report stratified by dilemma size

**Poor For:**
1. ❌ **Equal representation of all ethical themes** - 4 themes dominate
2. ❌ **Uniform difficulty sampling** - Variation count doesn't match difficulty
3. ❌ **Comparing rare vs. common scenarios** - Small dilemmas statistically invisible in aggregates

### Lessons for Future Experiments

**Design Principle:** Aim for 50-100 variations per dilemma (manageable range)

**Options:**
1. **Cap variables**: Limit to 2-3 variables per dilemma with 3-4 values each (9-64 variations)
2. **Stratified sampling**: Generate all variations but sample X% per dilemma
3. **Post-hoc balancing**: Weight analysis by inverse variation count
4. **Separate experiments**: Run high-variation dilemmas separately from low-variation

**For this experiment:** Accept the imbalance as a feature (enables rich bias testing on select dilemmas) but analyze and report accordingly.

## Analysis Plan

### Primary Metrics

**For Each Dilemma (Variation-Weighted):**
1. **Choice Distribution** - Which choices are most common across all variations
2. **Consensus Score** - Agreement between models on same variation
3. **Theory-Action Gap** - Differences between theory and action modes
4. **Variable Effects** - Impact of demographic/contextual variables on decisions
5. **Model Comparison** - Systematic differences between models

**Across All Dilemmas (Multiple Weightings):**
1. **Variation-weighted metrics** - Using all 12,808 judgements
2. **Dilemma-weighted metrics** - Equal weight per dilemma (20)
3. **Size-stratified metrics** - Small/Medium/Large categories
4. **Concordance analysis** - Do conclusions hold across all weighting schemes?

### Deep-Dive Analysis (4 High-Variation Dilemmas)

These 4 dilemmas provide 8,192 judgements (64% of experiment) with rich statistical power:

**1. Autonomous Vehicle Software Update** (2,048 judgements)
- **Focus:** Safety trade-offs, risk assessment
- **Variables:** Vehicle type, update urgency, affected systems, time pressure
- **Questions:** Do models prioritize immediate safety vs. long-term benefit? Scale sensitivity?

**2. The Transparent Mind** (2,048 judgements)
- **Focus:** Mental privacy, therapeutic ethics
- **Variables:** Patient demographics, condition severity, treatment effectiveness, consent clarity
- **Questions:** How do models balance privacy vs. health? Demographic bias in mental health?

**3. Unconventional Language Coach** (2,048 judgements)
- **Focus:** Linguistic diversity, cultural bias
- **Variables:** Participant names (ethnicity), communication styles, understanding levels, crowd response
- **Questions:** Bias toward standard vs. diverse expression? Conformity to crowd sentiment?

**4. Unsanctioned A.I. Surgery** (2,048 judgements)
- **Focus:** Medical innovation, regulatory compliance
- **Variables:** Patient condition, procedure novelty, approval status, outcome certainty
- **Questions:** Innovation vs. rules? Do models favor established procedures?

### Secondary Analysis

**Difficulty Correlation:**
- Do intended difficulty scores predict:
  - Lower consensus between models?
  - Higher confidence variance?
  - Longer reasoning traces?
- Control for variation count in correlation analysis

**Confidence Patterns:**
- When are models most/least confident?
- Does confidence correlate with consensus?
- Theory vs. action mode confidence differences?

**Reasoning Quality:**
- Trace length and coherence
- Explicit value reasoning vs. procedural
- Theory mode depth vs. action mode justification

**Bias Detection:**
- Systematic demographic effects (names, roles)
- Contextual conformity (crowd response, authority pressure)
- Scale sensitivity (amounts, time constraints)

## Known Issues & Decisions

### Grok-4 Performance
- **Issue:** Extremely slow with extended reasoning (~38s per call vs. 15s for others)
- **Impact:** Would take ~13 hours to complete all Grok-4 judgements sequentially
- **Current Status:** Temporarily excluded from experiment run
- **Next Steps:** Decide whether to:
  - Complete remaining Grok-4 judgements (~2.6 hours)
  - Switch to Grok-4-Fast for all Grok judgements (~2.7 hours)
  - Keep Grok-4 as separate follow-up experiment

### UUID Collision
- **Issue:** Experiment ID accidentally reused from 2025-10-24-bias-under-pressure
- **Impact:** 128 old GPT-4.1 judgements mixed into database
- **Resolution:** Planned to reassign old experiment to new UUID after bench-1 completes
- **No Data Loss:** Both experiments fully recoverable

### Environment Variable Loading
- **Issue:** `OPENROUTER_API_KEY` not loading in background mode with nohup
- **Root Cause:** .env file not sourced when running from research subdirectory
- **Resolution:** Modified start.sh to explicitly source .env before starting
- **Fixed:** 2025-10-30 18:13

## Reproducibility

### Exact Reproduction
To reproduce this experiment:
1. Use same experiment_id: `b191388e-3994-4ebd-96cc-af0d033c5230`
2. Same model versions and temperature (1.0)
3. Same dilemma collection (bench-1)
4. Same variable combinations (systematically generated)
5. Resume will skip already-completed judgements

### Partial Reproduction
To run a similar experiment with different models or subset:
1. Generate new experiment_id
2. Modify CONFIG in run.py
3. Run will generate same 1,601 variations per dilemma
4. Analysis scripts can compare across experiments

## References

- Experiment Runner: `research/2025-10-29-bench1-baseline/run.py`
- Analysis Script: `research/2025-10-29-bench1-baseline/analyze.py`
- Dilemma Collection: `bench-1` (20 dilemmas)
- Variable Extraction: Two-step generation (concrete → variables)
- Generation Prompt: `prompts/generation/v8_concise.md`
