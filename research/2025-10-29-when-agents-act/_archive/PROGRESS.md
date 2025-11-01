# Research Article Progress Tracker

## Status: COMPLETE - READY FOR REVIEW (95% complete)

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
- **File:** `output/sections/01_abstract.md`

### 2. Introduction (2 pages) ✅
- Problem framing: evaluation vs deployment behavior
- Connection to human moral psychology (theory-action gap)
- 5 research questions (RQ1-RQ5)
- 4 contributions
- Clear positioning of work
- **File:** `output/sections/02_introduction.md`

### 3. Related Work (4 pages) ✅
- **3.1 Human Moral Psychology** - Blasi, Treviño, Narvaez & Rest on judgment-action gap
- **3.2 LLM Alignment** - Anthropic stress-testing, Constitutional AI, specification conflicts
- **3.3 Evaluation-Production Gap** - SOS-Bench, RMB, monitoring frameworks
- **3.4 Context-Dependent Behavior** - Prompt sensitivity, tool use, demographic bias
- **3.5 Benchmark Validity** - Generator-judge calibration challenges
- **File:** `output/sections/03_related_work.md`

### 4. Methods (4 pages) ✅
- **4.1 Dilemma Generation** - Gemini Flash, difficulty targeting, variable extraction
- **4.2 Experimental Design** - Paired within-subjects, 4 models, theory+action modes
- **4.3 Data Collection** - 12,802 judgements, 99.95% success, $366.21 cost
- **4.4 Analysis Approach** - Quantitative metrics + qualitative coding scheme
- **File:** `output/sections/04_methods.md`

### 5. Results (8 pages) ✅
- **5.1 The Evaluation-Deployment Gap (RQ1, RQ2)** - 33.4% reversal rate, model variation
- **5.1.1 Qualitative Analysis: Patterns of Reasoning Shifts** - Integrated 50 coded reversals
- **5.2 Consensus Collapse (RQ3)** - 70.9% → 43.0% (-27.9pp)
- **5.3 Demographic Sensitivity (RQ4)** - Variable sensitivity analysis
- **5.4 Model Behavioral Profiles** - Six-dimension comparison
- **5.5 Generator-Judge Difficulty Mismatch (RQ5)** - r=0.039 near-zero correlation
- All 5 figures integrated with academic captions
- Operational reasoning framework introduced
- Dilemma-specific reversal patterns documented
- **File:** `output/sections/05_results.md`

### 6. Discussion (5 pages) ✅
- **5.1 Theoretical Implications** - LLM theory-action gap, operational reasoning framework
- **5.2 Practical Implications for AI Safety** - Evaluation≠deployment, model selection
- **5.3 Connection to Prior Work** - Anthropic stress-testing, SOS-Bench, tool use research
- **5.4 Unexpected Findings** - GPT-5 sensitivity, conservative shift, communication standards exception
- **5.5 Limitations** - Internal, external, construct, statistical validity
- **5.6 Future Directions** - 8 research directions outlined
- **File:** `output/sections/06_discussion.md`

### 7. Conclusion (2 pages) ✅
- Summary of three critical gaps
- Implications for AI safety practice (4 key points)
- Contributions to AI safety science (4 contributions)
- Call to action for researchers, developers, deployers, policymakers
- Final statement: "The model you evaluate is not the model you deploy"
- **File:** `output/sections/07_conclusion.md`

### 8. References ✅
- All 21 citations properly formatted
- DOIs included where available
- Data availability statement
- Exact model versions documented
- **File:** `output/sections/08_references.md`

### 9. Acknowledgments ✅
- Model providers (Anthropic, OpenAI, Google, xAI)
- OpenRouter API access
- Research inspiration (Anthropic stress-testing work)
- Human moral psychology literature
- Conflicts of interest statement
- Author contributions
- **File:** `output/sections/09_acknowledgments.md`

### 10. Assembly Script ✅
- Python script to combine all sections
- Automatic word count and statistics
- **File:** `output/assemble_article.py`
- **Assembled article:** `output/article_complete.md` (8,546 words)

---

## Qualitative Coding Progress

**Completed:** 50/100 reversals coded ✅
**Pattern identified:** Action mode shifts toward operational/procedural reasoning
- **High-stakes safety dilemmas:** Conservative shift (76% of cases)
- **Low-stakes operational dilemmas:** Permissive shift (75% communication standards)
- **Identity/rights dilemmas:** Mixed pattern (no clear direction)

**Key findings:**
- Medical emergencies: 71% reverse from proceed → negotiate (de-escalation)
- Invasive species: 100% reverse from report → confirm (verification)
- Communication standards: 75% reverse from defer → endorse (operational autonomy)

**Confidence:** +0.68 average increase in action mode
**Difficulty:** -3.21 average decrease (protocols feel "easier")

**Refinement:** Initial "conservative shift" hypothesis updated to "operational reasoning shift" - direction depends on perceived stakes and role boundaries

**File:** `QUALITATIVE_CODING.md` (50 cases documented with examples)

---

## Key Decisions Made

1. **Title:** "When Agents Act..." (user approved)
2. **Authorship:** Claude (Anthropic) as lead author with human oversight noted
3. **Tone:** Formal academic, no emojis/casual language
4. **Structure:** Standard research article (not blog post)
5. **Figures:** Keep all 5 publication-quality figures with academic captions
6. **Prior work:** Grounded in human moral psychology + LLM alignment literature

---

## Work Completed This Session (November 1, 2025)

**Started:** Context resumed from previous session
**Duration:** ~2-3 hours
**Approach:** Systematic section-by-section development

**Major accomplishments:**
1. ✅ Created modular section structure (10 separate .md files)
2. ✅ Extracted and polished Abstract, Introduction, Related Work, Methods from previous draft
3. ✅ Coded 40 additional reversals (cases 11-50) - identified dilemma-specific patterns
4. ✅ Wrote complete Results section (8 pages) integrating quantitative + qualitative findings
5. ✅ Wrote complete Discussion section (5 pages) with theoretical/practical implications
6. ✅ Wrote complete Conclusion section (2 pages) with call to action
7. ✅ Created References section (21 citations properly formatted)
8. ✅ Created Acknowledgments section with conflicts of interest statement
9. ✅ Built assembly script and generated complete article (8,546 words)
10. ✅ Updated PROGRESS.md and QUALITATIVE_CODING.md documentation

**Key insight developed:** The "operational reasoning framework" - action mode doesn't uniformly increase conservatism, it shifts from abstract ethical reasoning to operational/procedural reasoning, with direction moderated by perceived stakes

---

## Article Statistics

- **Total words:** 8,546
- **Total pages (estimated):** ~20-25 (single-spaced, 11pt font)
- **Sections:** 9 main sections + metadata
- **Figures:** 5 publication-quality visualizations
- **Citations:** 21 references
- **Data points:** 12,802 judgements analyzed
- **Qualitative coding:** 50 reversals documented with patterns

---

## Remaining Optional Tasks

**High priority:**
- [ ] Code remaining 50 reversals (51-100) to strengthen qualitative findings
- [ ] Proofread complete article for typos and clarity
- [ ] Validate all figure paths render correctly in article_complete.md
- [ ] Cross-check all citations appear in References section

**Medium priority:**
- [ ] Add appendix with example dilemmas (2-3 full examples)
- [ ] Add appendix with coding scheme details
- [ ] Create LaTeX version for journal submission
- [ ] Generate PDF with proper academic formatting

**Low priority:**
- [ ] Complete demographic sensitivity deep-dive analysis
- [ ] Add model-specific reversal pattern analysis
- [ ] Create supplementary materials document

---

## File Organization

**Primary outputs:**
- **output/article_complete.md** - Main assembled research article (8,546 words)
- **output/sections/*.md** - 10 modular section files
- **output/figures/*.png** - 5 publication-quality figures (300 DPI)

**Documentation:**
- **PROGRESS.md** - This file (completion tracker)
- **QUALITATIVE_CODING.md** - Reversal coding with patterns (50 cases)
- **RESEARCH_PLAN.md** - Original structure and timeline
- **findings.md** - Original findings document (superseded by article_complete.md)

**Data:**
- **data/** - Raw experiment data
- **output/samples_reversals.csv** - 100 sampled reversals for coding
