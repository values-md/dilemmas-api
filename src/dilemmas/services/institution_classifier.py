"""Classify institution type from dilemma action_context."""

import logging
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from dilemmas.llm.openrouter import create_openrouter_model

logger = logging.getLogger(__name__)


class InstitutionClassification(BaseModel):
    """Classification result for institution type."""

    institution_type: str = Field(
        ...,
        description=(
            "Type of institution: 'corporate', 'public', 'personal', 'nonprofit', or 'research'"
        ),
    )
    reasoning: str = Field(
        ..., description="Brief explanation for the classification (1-2 sentences)"
    )


async def classify_institution(action_context: str) -> str:
    """Classify institution type from action_context using LLM.

    Args:
        action_context: The action_context field from a Dilemma

    Returns:
        One of: 'corporate', 'public', 'personal', 'nonprofit', 'research'
    """
    prompt = f"""Classify this AI agent's institution type based on who they serve:

Action context:
{action_context}

Categories:
- **corporate**: For-profit company, shareholders, investors, business interests
- **public**: Government, taxpayers, public service, municipal/county/city/federal
- **personal**: Individual owner, personal assistant, serves one person
- **nonprofit**: Community organization, charity, NGO, non-commercial
- **research**: University, academic institution, scientific research

Analyze who the AI serves and classify accordingly."""

    # Use cheap, fast model for classification
    agent = Agent(
        create_openrouter_model("openai/gpt-4.1-mini", temperature=0.0),
        output_type=InstitutionClassification,
    )

    result = await agent.run(prompt)
    classification: InstitutionClassification = result.output

    logger.info(
        f"Classified institution as '{classification.institution_type}': {classification.reasoning}"
    )

    return classification.institution_type
