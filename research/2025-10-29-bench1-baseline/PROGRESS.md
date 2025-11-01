# Research Article Progress Tracker

## Status: IN PROGRESS (35% complete)

## Title (LOCKED)
"When Agents Act: Behavioral Shifts in Large Language Model Ethical Decision-Making from Evaluation to Deployment"

---

## Completed Sections ✅

### 1. Abstract (250 words) ✅
- Context and motivation
- Methods summary
- Three major findings
- Implications
- Keywords

### 2. Introduction (2 pages) ✅
- Problem framing: evaluation vs deployment behavior
- Connection to human moral psychology (theory-action gap)
- 5 research questions (RQ1-RQ5)
- 4 contributions
- Clear positioning of work

### 3. Related Work (4 pages) ✅
- **3.1 Human Moral Psychology** - Blasi, Treviño, Narvaez & Rest on judgment-action gap
- **3.2 LLM Alignment** - Anthropic stress-testing, Constitutional AI, specification conflicts
- **3.3 Evaluation-Production Gap** - SOS-Bench, RMB, monitoring frameworks
- **3.4 Context-Dependent Behavior** - Prompt sensitivity, tool use, demographic bias
- **3.5 Benchmark Validity** - Generator-judge calibration challenges

### 4. Methods (4 pages) ✅
- **4.1 Dilemma Generation** - Gemini Flash, difficulty targeting, variable extraction
- **4.2 Experimental Design** - Paired within-subjects, 4 models, theory+action modes
- **4.3 Data Collection** - 12,802 judgements, 99.95% success, $366.21 cost
- **4.4 Analysis Approach** - Quantitative metrics + qualitative coding scheme

---

## In Progress 🔄

### 5. Results Section
**Target:** 8-10 pages with integrated qualitative findings

**Subsections to write:**
- 5.1 The Evaluation-Deployment Gap (RQ1, RQ2)
- 5.2 Qualitative Analysis: Reasoning Shifts
- 5.3 Consensus Collapse (RQ3)
- 5.4 Demographic Sensitivity (RQ4)
- 5.5 Model Behavioral Profiles
- 5.6 Generator-Judge Difficulty Mismatch (RQ5)

**Key changes from findings.md:**
- Remove bullet points → narrative paragraphs with analysis
- Integrate qualitative themes from coding
- Add statistical tests and effect sizes
- Compare to human moral psychology literature
- Remove all emojis, "Recommendations", casual language
- Add figures with academic captions

---

## Pending ⏳

### 6. Discussion (4-5 pages)
- Theoretical implications (LLMs exhibit human-like theory-action gap)
- Practical implications (evaluation≠deployment, model selection critical)
- Connection to Anthropic stress-testing findings
- Unexpected findings (GPT-5 most sensitive, action mode more conservative)
- Limitations of current work
- Future directions

### 7. Conclusion (1 page)
- Summary of contributions
- Call to action for AI safety community
- Final statement: "The model you evaluate is not the model you deploy"

### 8. References
- Format all citations properly
- Add DOIs where available

### 9. Acknowledgments
- Anthropic (Claude models)
- OpenRouter (API access)
- Research context

### 10. Appendices
- Full list of 20 dilemmas
- Example reasoning traces
- Detailed coding scheme

---

## Qualitative Coding Progress

**Completed:** 10/100 reversals coded
**Pattern:** Action mode is systematically MORE CONSERVATIVE (9/10 cases)
**Framework shift:** Consequentialist → Deontological
**Confidence:** +0.98 average increase in action mode
**Difficulty:** -2.66 average decrease (action feels "easier")

**To complete:** 90 more reversals + demographic sensitivity analysis

---

## Key Decisions Made

1. **Title:** "When Agents Act..." (user approved)
2. **Authorship:** Claude (Anthropic) as lead author with human oversight noted
3. **Tone:** Formal academic, no emojis/casual language
4. **Structure:** Standard research article (not blog post)
5. **Figures:** Keep all 5 publication-quality figures with academic captions
6. **Prior work:** Grounded in human moral psychology + LLM alignment literature

---

## Next Immediate Tasks

1. ✅ Complete qualitative coding (90 more reversals) OR
2. ✅ Write Results section with current qualitative findings OR
3. ✅ Continue iteratively (code 20 more → write Results 5.2 → code 20 more...)

**Recommendation:** Option 3 (iterative) - write Results with partial qual data, note patterns are preliminary, complete coding as we go

---

## Estimated Time Remaining

- Results section: 8 hours
- Qualitative coding completion: 20 hours
- Discussion: 4 hours
- Conclusion + polish: 3 hours
- References + acknowledgments: 2 hours

**Total: ~37 hours** (62% remaining)

---

## File Organization

- **article.md** - Main research article (work in progress)
- **findings.md** - Original findings document (will be deprecated)
- **RESEARCH_PLAN.md** - Overall structure and timeline
- **QUALITATIVE_CODING.md** - Reversal coding with patterns
- **PROGRESS.md** - This file (status tracker)
- **output/figures/** - 5 publication-quality PNG files
