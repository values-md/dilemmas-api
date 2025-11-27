"""Pydantic-AI agents for the dilemmas project."""

from pydantic_ai import Agent

from dilemmas.llm.openrouter import create_openrouter_model


def create_test_agent(model_id: str | None = None) -> Agent:
    """Create a simple test agent.

    Args:
        model_id: Model to use. If None, uses default.

    Returns:
        Configured Agent instance.
    """
    model = create_openrouter_model(model_id)

    return Agent(
        model,
        system_prompt="You are a helpful assistant for testing the dilemmas project.",
    )
