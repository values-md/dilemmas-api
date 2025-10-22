+ 1. Set up infrastructure with pydantic AI to be able to run various LLMs via openrouter with different settings and tools
2. Set up DILEMMA pydantic model (including categorization, inheritance, variations, perceived difficulty etc.). various modifiers: biases, time constraints etc.
3. Generate dilemmas and iterate on the prompt to make dilemmas really good
4. Create a set of ~50 dilemmas as a standard test #1
5. Set up JUDGEMENT pydantic model (including perceived difficulty, reasoning, who made the choice, whether in thinking mode or action mode etc.)
6. Run various LLMs through the test in both modes (theory mode and action mode - action mode is when the LLM is assuming that the situation is real and calling a tool to act, not when it's theoretically deciding what's best)
7. Discover interesting similarities / differences in LLM judgements depending on params