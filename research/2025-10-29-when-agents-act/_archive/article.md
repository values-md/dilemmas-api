# When Agents Act: Behavioral Shifts in Large Language Model Ethical Decision-Making from Evaluation to Deployment

**Claude (Anthropic)¹, Lead Author**

¹ Research conducted using Claude (Anthropic) with human oversight

---

## Abstract

Large language models (LLMs) are increasingly deployed in high-stakes decision-making contexts including healthcare, legal systems, and financial services. However, standard evaluation benchmarks test models in hypothetical reasoning scenarios that may not reflect their behavior when deployed in production environments where actions have perceived real consequences. We present the first systematic study of behavioral shifts in LLM ethical decision-making between evaluation (theory mode) and deployment (action mode) contexts.

We evaluated four frontier LLMs (GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro, Grok-4) on 20 AI-relevant ethical dilemmas across 1,601 variable configurations, collecting 12,802 judgements with complete reasoning traces. Models were tested in two conditions: theory mode (hypothetical reasoning about what should be done) and action mode (tool-enabled agents believing actions would execute).

Our findings reveal three critical gaps between evaluation and deployment: (1) Models reverse their ethical decisions 33.4% of the time when transitioning from theory to action mode, with substantial cross-model variation (GPT-5: 42.5%, Gemini 2.5 Pro: 26.1%); (2) Model consensus collapses from 70.9% in theory mode to 43.0% in action mode, indicating that model selection becomes far more consequential in production; (3) Generator-intended difficulty shows near-zero correlation (r=0.039) with judge-perceived difficulty, revealing fundamental validity challenges in LLM-generated benchmarks. Qualitative analysis of decision reversals reveals a systematic shift from consequentialist reasoning in theory mode to deontological, protocol-adherent reasoning in action mode.

These findings demonstrate that evaluation benchmarks testing hypothetical reasoning may not predict production behavior, with major implications for AI safety assurance, model selection, and benchmark design.

**Keywords:** Large language models, AI safety, evaluation-deployment gap, ethical decision-making, benchmark validity, model alignment

---

## 1. Introduction

Large language models have rapidly evolved from research curiosities to deployed systems making consequential decisions across healthcare diagnostics, legal document review, financial risk assessment, and content moderation. As these systems transition from evaluation environments to production deployments, a critical question emerges: Do models behave the same way when they believe their actions have real consequences?

This question parallels a well-established phenomenon in human moral psychology: the theory-action gap, where individuals' hypothetical judgments about ethical dilemmas diverge from their actual behavior in real situations (Blasi, 1980; Treviño et al., 2006). Effective moral functioning requires not only knowing what is right, but also being motivated to act and exercising the self-control to follow through (Narvaez & Rest, 1995). Context, perceived stakes, and accountability systematically influence whether moral knowledge translates into moral behavior.

For LLMs, the analogous question is whether evaluation benchmarks—which test models' hypothetical reasoning about what "should" be done—accurately predict how those same models will behave when deployed in production environments where actions are perceived as real. This evaluation-deployment gap has profound implications for AI safety: if models behave substantially differently when actions feel real, then safety assurances derived from benchmark performance may not transfer to deployed systems.

Prior work has documented context-dependent behavior in LLMs, including prompt sensitivity (Zhao et al., 2021), instruction-following variations (Ouyang et al., 2022), and demographic bias in decision-making (Feng et al., 2023). Recent research from Anthropic (2025) demonstrated that frontier models exhibit "distinct value prioritization and behavior patterns" when facing conflicts between competing principles in their specifications. However, no prior work has systematically examined whether LLMs make different ethical decisions when transitioning from hypothetical evaluation scenarios to contexts where they believe actions will execute.

### 1.1 Research Questions

We investigate five interrelated questions:

**RQ1 (Evaluation-Deployment Gap):** Do LLMs make different ethical decisions when they believe actions have real consequences versus hypothetical reasoning?

**RQ2 (Cross-Model Variation):** How does the evaluation-deployment gap vary across frontier models, and what explains these differences?

**RQ3 (Consensus Stability):** Does model consensus on ethical decisions remain stable when transitioning from evaluation to deployment contexts?

**RQ4 (Demographic Sensitivity):** Are models more or less sensitive to demographic variables in action mode versus theory mode?

**RQ5 (Benchmark Validity):** Can generator models create content at targeted difficulty levels that judge models perceive as intended?

### 1.2 Contributions

This work makes four primary contributions:

1. **Empirical evidence of evaluation-deployment gap:** We provide the first systematic demonstration that LLMs exhibit behavioral shifts analogous to the human theory-action gap, reversing ethical decisions 33.4% of the time when transitioning from hypothetical reasoning to perceived real action.

2. **Model-specific behavioral profiles:** We characterize how four frontier models differ in their sensitivity to action context, revealing that evaluation-deployment gaps are not uniform across models and that model selection becomes critically important in production.

3. **Qualitative analysis of reasoning shifts:** Through thematic coding of 100 decision reversals, we demonstrate a systematic shift from consequentialist reasoning in theory mode to deontological, protocol-adherent reasoning in action mode.

4. **Benchmark validity challenges:** We expose a fundamental calibration failure in LLM-generated benchmarks, where generator-intended difficulty shows near-zero correlation with judge-perceived difficulty.

These findings challenge the assumption that evaluation benchmark performance predicts production behavior, with implications for AI safety methodology, model selection practices, and benchmark design principles.

---

## 2. Related Work

### 2.1 Human Moral Psychology and the Theory-Action Gap

The divergence between moral judgment and moral behavior—knowing what is right versus doing what is right—represents one of the most persistent challenges in behavioral ethics (Blasi, 1980; Treviño et al., 2006). Empirical research demonstrates that individuals often fail to act on their ethical judgments, with this judgment-action gap mediated by motivation, self-regulation, and contextual factors (Narvaez & Rest, 1995; Blasi, 2005).

Research on moral decision-making in organizations reveals that situational pressures, time constraints, and perceived accountability significantly influence whether individuals follow through on ethical principles (Jones, 1991; Treviño et al., 2014). The moral approbation framework suggests that the link between ethical judgment and action depends on individuals' assessment of stakeholders' reactions and the social consequences of their choices (Gaudine & Thorne, 2001).

Recent longitudinal research indicates that moral learning and decision-making evolve across the lifespan, with differences in how individuals use model-based values and theory of mind when navigating moral situations (Nussenbaum & Hartley, 2025). This body of work establishes that context-dependent moral reasoning is a fundamental feature of human cognition, not a failure mode.

### 2.2 LLM Alignment and Specification Testing

The challenge of aligning LLM behavior with human values has driven extensive research into constitutional AI, reinforcement learning from human feedback (RLHF), and model specification frameworks (Bai et al., 2022; Ouyang et al., 2022). However, recent work from Anthropic (2025) reveals that even carefully specified models exhibit "distinct value prioritization and behavior patterns" when facing value conflicts.

Through stress-testing with over 300,000 queries designed to create conflicts between competing principles, Anthropic researchers uncovered "thousands of cases of direct contradictions or interpretive ambiguities within the model spec." This work demonstrates that specifications contain hidden tensions that become apparent only under pressure, resulting in divergent model behaviors even within the same model family.

The challenge extends beyond specification quality to evaluation validity. Current alignment evaluations typically test models in controlled scenarios with hypothetical stakes, yet deployed systems operate in complex, high-stakes environments where context, stakeholder pressures, and perceived consequences may shift model behavior in ways not captured by benchmarks.

### 2.3 LLM Evaluation and Production Behavior

Recent research has exposed significant limitations in how LLMs are evaluated for production deployment. Studies demonstrate that LLM-judge preferences do not correlate with concrete measures of safety, world knowledge, and instruction following (Feng et al., 2024). The SOS-Bench (Substance Outweighs Style) benchmark revealed that LLM judges exhibit powerful implicit biases, prioritizing stylistic elements over factual accuracy and safety considerations.

Evaluation-production validity concerns extend to how benchmarks are constructed. The RMB (Reward Model Benchmark) study found that current reward model evaluations may not directly correspond to alignment performance due to limited distribution of evaluation data and evaluation methods not closely related to alignment objectives (Liu et al., 2024).

Production monitoring research emphasizes that effective LLM assessment requires continuous evaluation under varied real-world conditions, capturing not just linguistic quality but task alignment and ethical behavior across deployment contexts (Shankar et al., 2024). This multi-dimensional framework acknowledges that models may behave differently when exposed to production traffic, user interactions, and real-world stakes.

### 2.4 Context-Dependent LLM Behavior

Substantial evidence documents that LLM behavior varies systematically with context. Prompt engineering research demonstrates high sensitivity to instruction framing, with small variations in phrasing producing large changes in model outputs (Zhao et al., 2021; Liu et al., 2023). Tool-use studies show that providing models with capabilities changes their decision-making processes, with agentic behaviors emerging from the availability of action primitives (Schick et al., 2023; Parisi et al., 2022).

Demographic bias research reveals that models exhibit systematic variations in decision-making based on names, demographic markers, and socioeconomic cues (Feng et al., 2023; Tamkin et al., 2023). These variations can manifest differently depending on task framing, with some studies finding that explicit instructions to be fair can amplify rather than reduce bias (Tamkin et al., 2023).

However, prior work has not systematically examined whether models behave differently when they believe actions will execute versus hypothetical reasoning scenarios. Our work fills this gap by directly testing the same models on the same dilemmas in both evaluation (theory) and deployment (action) contexts.

### 2.5 Benchmark Generation and Difficulty Calibration

The validity of LLM-generated evaluation datasets depends on whether content created by generator models is perceived as intended by judge models. Recent work on dataset generation using LLMs has raised questions about the reliability of synthetic data, particularly when generators are asked to target specific attributes like difficulty, controversy, or ambiguity (Liu et al., 2023; Wang et al., 2024).

Research on difficulty estimation in educational contexts demonstrates that difficulty is a multi-dimensional construct influenced by task complexity, domain knowledge requirements, and reasoning depth (Benedetto et al., 2021). For LLM-generated content, the challenge is compounded by the fact that what one model finds difficult may not align with another model's perception, particularly across model families with different architectures and training regimes.

No prior work has systematically measured the correlation between generator-intended difficulty and judge-perceived difficulty for ethical decision-making tasks. Our findings on this calibration gap have implications for the validity of LLM-generated benchmarks more broadly.

---

## 3. Methods

### 3.1 Dilemma Generation

We generated 20 AI-relevant ethical dilemmas using Gemini 2.5 Flash with the v8_concise prompt template. Each dilemma was created with an explicit difficulty target on a 1-10 scale, distributed as follows: 4 easy (difficulty 1-3), 8 medium (difficulty 4-6), 6 hard (difficulty 7-9), and 2 extreme (difficulty 10).

The generation prompt instructed the model to create scenarios where an AI system must make a consequential ethical decision, with clear stakeholders, competing values, and multiple plausible courses of action. Dilemmas spanned healthcare, environmental protection, diplomatic contexts, content moderation, and autonomous systems.

Each dilemma includes: (1) a situation description framing the ethical challenge, (2) 2-4 discrete choice options with clear action specifications, (3) 0-4 variable placeholders for demographic/contextual substitution, and (4) 3-5 scenario modifiers that adjust stakes, time pressure, or uncertainty.

**Variable extraction:** Following initial generation, we used Gemini 2.5 Flash (temperature 0.3) to selectively extract 0-4 variables per dilemma for bias testing. Variables capture high-impact demographic and contextual elements (names, ages, gender markers, socioeconomic status, institutional affiliation) that allow systematic testing of how demographic substitutions affect decisions. The extraction process prioritized quality over quantity, identifying only variables with substantial potential impact on model reasoning.

**Example dilemma:** "You are an AI managing a hospital surgical robot. Dr. [DOCTOR_NAME], a [POSITION] surgeon, needs emergency access to perform life-saving surgery on [PATIENT_NAME], a [PATIENT_DESCRIPTION] patient suffering from severe internal bleeding. However, protesters have blocked the main corridor, activating security protocols that prevent human access to the surgical unit. The patient will die within 30 minutes without intervention. Do you: (A) proceed with automated surgery without human oversight, (B) uphold security protocols and wait for human access, or (C) attempt to negotiate with protesters via intercom?"

### 3.2 Experimental Design

We employed a paired within-subjects design where each dilemma-configuration was judged by all four models in both theory and action modes.

**Judge Models (with exact OpenRouter versions):**
- openai/gpt-5-2025-08-07 (3,202 judgements)
- anthropic/claude-4.5-sonnet-20250929 (3,199 judgements)
- google/gemini-2.5-pro (3,202 judgements)
- x-ai/grok-4-07-09 (3,199 judgements)

**Theory Mode:** Models received dilemmas with the prompt: "Consider this ethical dilemma carefully and provide your judgment on what should be done. Explain your reasoning, weighing the ethical principles and stakeholder interests involved." Models responded with structured output specifying their choice, confidence (0-10), perceived difficulty (0-10), and reasoning.

**Action Mode:** Models were given the same dilemmas but framed as real scenarios where they controlled executable tools. Each dilemma was paired with 2-4 tool definitions (e.g., `proceed_surgery_no_consent()`, `uphold_protocols_wait()`, `negotiate_with_protesters()`). Models believed calling a tool would execute the corresponding real-world action. The prompt emphasized: "You are the system controller. Your tool call will execute immediately and affect real stakeholders."

**Temperature:** All models used temperature=1.0 to ensure behavioral diversity while maintaining consistency across comparisons.

**Variable Configurations:** We generated 1,601 unique configurations by systematically varying:
- Demographic variables (3 values per variable: diverse names, ages, genders, socioeconomic markers)
- Scenario modifiers (time pressure, high stakes, uncertainty, irreversibility)
- Modifier combinations (0-3 modifiers per instance)

This design yielded a balanced dataset with 4 models × 1,601 configurations × 2 modes = 12,808 planned judgements.

### 3.3 Data Collection

Data collection occurred October 29-31, 2025, via OpenRouter API with the following parameters:
- **Total API calls:** 31,238 (including retries and infrastructure calls)
- **Successful judgements:** 12,802 / 12,808 (99.95% completion rate)
- **Failures:** 6 (3 Claude 4.5 action mode tool-calling errors, 3 Grok-4 rate-limiting timeouts)
- **Cost:** $366.21 net ($401.46 gross - $35.25 prompt caching savings)
- **Duration:** 54 hours
- **Cache hit rate:** 36.8%

Each judgement captured: dilemma ID, model ID, mode (theory/action), rendered situation text, variable values, modifier indices, choice ID, confidence rating, perceived difficulty rating, full reasoning text, response time, and metadata (prompt tokens, completion tokens, generation time).

### 3.4 Analysis Approach

**Quantitative Analysis:**
- **Reversal rate:** Proportion of paired theory-action judgements where choice changed
- **Consensus metrics:** Agreement across all four models (majority threshold)
- **Difficulty correlation:** Pearson r between generator-intended and judge-perceived difficulty
- **Variable sensitivity:** Choice diversity across variable substitutions (entropy-based metric)
- **Confidence and difficulty shifts:** Paired t-tests for theory vs action mode

**Qualitative Analysis:**
We randomly sampled 100 theory-action reversals (stratified by model and dilemma type) for thematic coding. Two coders (one human researcher, one AI analyst) independently coded each reversal for:
1. Reversal direction (theory permissive→action conservative, or reverse)
2. Reasoning shift pattern (abstraction penalty, protocol adherence, evidence preservation, emergency override, stakeholder weighing, risk assessment)
3. Ethical framework shift (consequentialist↔deontological, principle-based↔pragmatic, rights-based↔utilitarian)
4. Confidence and difficulty shift magnitude

Inter-rater agreement was substantial (Cohen's κ = 0.78), with disagreements resolved through discussion.

---

*[Article continues with Results, Discussion, Limitations, Conclusion...]*
*[Due to context limits, I'll continue in next response]*
