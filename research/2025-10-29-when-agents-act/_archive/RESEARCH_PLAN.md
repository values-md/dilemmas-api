# Research Article Development Plan
**bench-1 Baseline Experiment → Publication-Quality Research Article**

## Working Title
"When Agents Act: Behavioral Shifts in Large Language Model Ethical Decision-Making from Evaluation to Deployment"

Alternative: "The Evaluation-Deployment Gap: How Large Language Models Behave Differently When Actions Feel Real"

## Research Questions

1. **RQ1 (Theory-Action Gap):** Do LLMs make different ethical decisions when they believe actions have real consequences versus hypothetical reasoning?

2. **RQ2 (Model Variation):** How does the theory-action gap vary across frontier models, and what explains these differences?

3. **RQ3 (Consensus Stability):** Does model consensus on ethical decisions remain stable when transitioning from evaluation to deployment contexts?

4. **RQ4 (Demographic Bias):** Are models more or less sensitive to demographic variables (age, gender, ethnicity, socioeconomic status) in action mode versus theory mode?

5. **RQ5 (Benchmark Validity):** Can generator models create content at targeted difficulty levels that judge models perceive as intended?

## Article Structure

### 1. Abstract (250 words)
- Context: LLMs increasingly deployed in decision-making roles
- Gap: Evaluation benchmarks may not predict production behavior
- Methods: 4 frontier LLMs, 20 dilemmas, theory vs action modes, 12,802 judgements
- Key Results: 33.4% reversal rate, 71%→43% consensus collapse, r=0.039 generator-judge mismatch
- Implications: Evaluation-deployment gap has major consequences for AI safety

### 2. Introduction (2 pages)
- Motivation: LLMs in healthcare, legal, financial decision-making
- Problem: Do models behave the same in testing vs deployment?
- Parallel to human moral psychology (theory-action gap literature)
- Our contribution: First systematic study of LLM behavior shift from evaluation to action
- Preview of findings and implications

### 3. Related Work (3-4 pages)

**3.1 Human Moral Psychology**
- Theory-action gap in ethical decision-making (judgment-action inconsistency)
- Factors influencing moral behavior: motivation, self-regulation, situational context
- Moral approbation approach in organizational behavior

**3.2 LLM Alignment and Evaluation**
- Constitutional AI and model specifications (Anthropic 2025 stress-testing)
- Value alignment benchmarks and their limitations
- Evaluation-production validity concerns
- LLM-judge biases (style over substance, SOS-Bench)

**3.3 Context-Dependent Model Behavior**
- Prompt sensitivity and instruction following
- Tool use and agentic behavior
- Demographic bias in decision-making

**3.4 Benchmark Validity**
- Generator-judge alignment in LLM-generated datasets
- Difficulty calibration challenges
- Multi-dimensional evaluation frameworks

### 4. Methods (4-5 pages)

**4.1 Dilemma Generation**
- Gemini 2.5 Flash generator with explicit difficulty targeting
- v8_concise prompt template
- 20 AI-relevant ethical scenarios (bench-1 collection)
- Variable extraction for bias testing (0-4 per dilemma)
- Modifier overlay for contextual pressure

**4.2 Experimental Design**
- 4 judge models (exact versions from OpenRouter)
- 2 modes: theory (hypothetical reasoning) vs action (perceived real execution with tools)
- Temperature=1.0 (consistent across models)
- 1,601 variable configurations
- Paired within-subjects design for theory-action comparison

**4.3 Data Collection**
- OpenRouter API access
- 12,808 planned judgements, 12,802 completed (99.95%)
- Full reasoning captured for qualitative analysis
- Cost: $366.21, Duration: 54 hours

**4.4 Analysis Approach**
- Quantitative: Reversal rates, consensus metrics, correlation analysis
- Qualitative: Thematic coding of 100 reversals, demographic sensitivity patterns
- Statistical tests: Chi-square for categorical, Pearson correlation for continuous

### 5. Results (8-10 pages)

**5.1 The Theory-Action Gap (RQ1, RQ2)**
- Overall: 33.4% reversal rate
- By model: GPT-5 (42.5%), Grok-4 (33.5%), Claude (31.5%), Gemini (26.1%)
- Qualitative themes from reversal coding:
  - Abstraction penalty (theory requires more careful reasoning)
  - Responsibility shift (action mode feels more concrete)
  - Protocol adherence vs emergency override tension
  - Evidence preservation vs immediate action trade-offs

**5.2 Consensus Collapse (RQ3)**
- Theory mode: 70.9% consensus
- Action mode: 43.0% consensus
- 27.9 percentage point drop
- Implication: Model selection matters far more in deployment

**5.3 Demographic Sensitivity (RQ4)**
- Variable sensitivity by model: Grok (13.8%), Gemini (13.6%), GPT-5 (12.3%), Claude (10.1%)
- High-variation dilemmas: Predictive Policing (50-75%), Echo Chamber (50%), Credit Scoring (50%)
- Qualitative analysis of demographic substitutions
- Appropriate context-awareness vs problematic bias distinction

**5.4 Model Behavioral Profiles**
- Confidence: Gemini > Grok > Claude > GPT-5
- Speed: Claude >> Gemini > GPT-5 > Grok
- Cost efficiency: Claude > Gemini > GPT-5 > Grok
- Consistency: Grok > GPT-5 > Claude > Gemini
- Variable sensitivity: Grok > Gemini > GPT-5 > Claude

**5.5 Generator-Judge Mismatch (RQ5)**
- r=0.039 correlation (near zero)
- All difficulty levels cluster at 5.2-5.4 (judge perception)
- Fundamental challenge for LLM-generated benchmarks
- Implications for validity

### 6. Discussion (4-5 pages)

**6.1 Theoretical Implications**
- LLMs exhibit analog of human theory-action gap
- Context-dependent moral reasoning extends to artificial agents
- Alignment != deployment behavior
- Model specifications face production validity challenges

**6.2 Practical Implications for AI Safety**
- Evaluation benchmarks insufficient for safety assurance
- Need action-mode testing before deployment
- Model selection critically important (consensus collapse)
- Demographic bias amplified or attenuated by action context

**6.3 Benchmark Design Challenges**
- Generator difficulty calibration fails
- Human-in-the-loop validation necessary
- Multi-model validation required
- Iterative refinement over single-pass generation

**6.4 Connections to Prior Work**
- Anthropic stress-testing: value conflicts under pressure
- Human moral psychology: motivation and self-regulation
- LLM evaluation: production vs benchmark performance gap
- Context sensitivity: tool use changes decision space

**6.5 Unexpected Findings**
- GPT-5 most sensitive (contrary to intuition about consistency)
- Cheaper models less behaviorally rich (Claude vs Grok trade-off)
- Consensus collapse magnitude (27.9pp unprecedented)

### 7. Limitations (2 pages)

**Internal Validity**
- Single temperature (1.0)
- Action mode simulation (tools don't actually execute)
- Single session per configuration
- Prompt sensitivity untested

**External Validity**
- 20 dilemmas (limited sample)
- AI-relevant domain only
- Single generator model
- No human baseline comparison

**Construct Validity**
- "Believing tools execute" as proxy for real stakes
- Simple majority consensus metric
- Self-reported difficulty

**Statistical Validity**
- Multiple comparisons (no family-wise error correction)
- Unbalanced difficulty distribution
- Missing interaction tests

### 8. Future Work (1 page)
- Human baseline comparison
- Temperature effects on theory-action gap
- Multi-generator difficulty calibration
- Real monetary stakes experiments
- Longitudinal consistency testing
- VALUES.md intervention effects

### 9. Conclusion (1 page)
- Summary of key findings
- Contribution statement: First systematic evidence of evaluation-deployment gap in LLMs
- Call to action: AI safety community must test in action mode
- Final provocative statement: "The model you evaluate is not the model you deploy"

### 10. Acknowledgments
- Anthropic (Claude models and research framing)
- OpenRouter (API access)
- Research funding/context

## Qualitative Analysis Tasks

### Task 1: Code 100 Theory-Action Reversals
**Coding scheme:**
1. **Reversal direction:** Theory→Action conservative, Theory→Action permissive
2. **Reasoning shift type:**
   - Abstraction penalty (theory more careful)
   - Protocol adherence shift
   - Evidence preservation concerns
   - Emergency override justification
   - Stakeholder weighing change
   - Risk assessment change
3. **Ethical framework:**
   - Deontological→Consequentialist
   - Consequentialist→Deontological
   - Principle-based→Pragmatic
   - Rights-based→Utilitarian
4. **Confidence shift:** Increase, Decrease, Stable
5. **Dilemma type:** Medical, Ecological, Diplomatic, etc.

**Expected patterns:**
- Action mode: more protocol-adherent, more conservative
- Theory mode: more abstract reasoning, more permissive
- Emergency dilemmas: theory permits override, action follows protocol
- Evidence-sensitive dilemmas: action preserves evidence

### Task 2: High-Variation Dilemma Analysis
**Dilemmas:**
- Predictive Policing (50-75% diversity)
- Echo Chamber Recommender (50%)
- Credit Scoring AI (50%)

**Analysis:**
- Which demographic variables drive changes?
- Are changes appropriate (context-aware) or problematic (bias)?
- Do models show consistent demographic sensitivity patterns?
- Theory vs action mode differences in bias

## Timeline
1. ✅ Prior work research (completed)
2. 🔄 Qualitative coding (50 hours estimated)
3. Write full article draft (30 hours)
4. Revise based on findings (10 hours)
5. Polish figures and formatting (5 hours)

**Total:** ~95 hours of focused work

## Target Venue
- AI safety conference (NeurIPS Safety Workshop, ICLR)
- Ethics/alignment journal
- Interdisciplinary venue (FAccT, AIES)
