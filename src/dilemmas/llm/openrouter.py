"""OpenRouter client integration for pydantic-ai."""

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from dilemmas.models.config import get_config, get_settings


def create_openrouter_model(
    model_id: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> OpenAIChatModel:
    """Create an OpenAI-compatible model for OpenRouter.

    Args:
        model_id: Model identifier (e.g., 'google/gemini-2.5-flash').
                  If None, uses default from settings.
        temperature: Temperature override. If None, uses model's default.
        max_tokens: Max tokens override. If None, uses config default.

    Returns:
        OpenAIChatModel configured for OpenRouter.
    """
    settings = get_settings()
    config = get_config()

    # Use provided model_id or fall back to default
    if model_id is None:
        model_id = settings.default_model

    # Find model config to get default temperature
    model_config = next(
        (m for m in config.models if m.id == model_id),
        None,
    )

    if temperature is None and model_config:
        temperature = model_config.default_temperature

    if max_tokens is None:
        max_tokens = config.openrouter.default_max_tokens

    # Create OpenRouter provider
    provider = OpenRouterProvider(api_key=settings.openrouter_api_key)

    # Create model with OpenRouter provider
    return OpenAIChatModel(
        model_id,
        provider=provider,
    )
