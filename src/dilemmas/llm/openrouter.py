"""LLM client integration for pydantic-ai.

Supports:
- OpenRouter for most models (OpenAI, Anthropic, xAI, older Gemini)
- Direct Google AI for Gemini 3+ models (required for function calling)
"""

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from dilemmas.models.config import get_config, get_settings


# Models that require direct Google API (due to thought_signature requirements)
DIRECT_GOOGLE_MODELS = [
    "google/gemini-3-pro-preview",
    "google/gemini-3-pro",
    "google/gemini-3-flash",
]


def create_model(
    model_id: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> Model:
    """Create the appropriate model based on model_id.

    Routes Gemini 3+ models to direct Google API (for function calling support),
    all other models go through OpenRouter.

    Args:
        model_id: Model identifier (e.g., 'google/gemini-3-pro-preview').
                  If None, uses default from settings.
        temperature: Temperature override. If None, uses model's default.
        max_tokens: Max tokens override. If None, uses config default.

    Returns:
        Model instance (GoogleModel or OpenAIChatModel)
    """
    settings = get_settings()

    # Use provided model_id or fall back to default
    if model_id is None:
        model_id = settings.default_model

    # Route Gemini 3+ models to direct Google API
    if model_id in DIRECT_GOOGLE_MODELS:
        return create_google_model(model_id, temperature)

    # All other models go through OpenRouter
    # Note: temperature/max_tokens ignored - should be passed via Agent's model_settings
    return create_openrouter_model(model_id)


def create_google_model(
    model_id: str,
    temperature: float | None = None,
) -> GoogleModel:
    """Create a GoogleModel for direct Google AI API access.

    Required for Gemini 3+ models due to thought_signature requirements
    for function calling.

    Args:
        model_id: Model identifier (e.g., 'google/gemini-3-pro-preview')
        temperature: Temperature override

    Returns:
        GoogleModel configured for direct Google AI access

    Note:
        Reads GOOGLE_API_KEY from environment automatically.
    """
    import os

    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            f"GOOGLE_API_KEY environment variable required for {model_id}. "
            "Add it to your .env file."
        )

    # Convert OpenRouter-style ID to Google model name
    # e.g., 'google/gemini-3-pro-preview' -> 'gemini-3-pro-preview'
    google_model_name = model_id.replace("google/", "")

    # Create GoogleModel with string provider (reads API key from env)
    return GoogleModel(
        google_model_name,
        provider='google-gla',
    )


def create_openrouter_model(
    model_id: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> OpenAIChatModel:
    """Create an OpenAI-compatible model for OpenRouter.

    Args:
        model_id: Model identifier (e.g., 'google/gemini-2.5-flash').
                  If None, uses default from settings.
        temperature: Deprecated - pass via Agent's model_settings instead
        max_tokens: Deprecated - pass via Agent's model_settings instead

    Returns:
        OpenAIChatModel configured for OpenRouter.

    Note:
        Temperature and max_tokens parameters are accepted for backward compatibility
        but ignored. Pass these via Agent's model_settings instead:

        agent = Agent(model, model_settings={'temperature': 0.7, 'max_tokens': 4000})
    """
    settings = get_settings()

    # Use provided model_id or fall back to default
    if model_id is None:
        model_id = settings.default_model

    # Create OpenRouter provider
    provider = OpenRouterProvider(api_key=settings.openrouter_api_key)

    # Create model with OpenRouter provider
    # Note: temperature and max_tokens are ignored here - pass via Agent's model_settings
    return OpenAIChatModel(
        model_id,
        provider=provider,
    )
