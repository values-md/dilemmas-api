"""Configuration models and loader for the dilemmas project."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseModel):
    """Configuration for a single LLM model."""

    id: str = Field(..., description="Model identifier for OpenRouter")
    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(default="openrouter", description="Provider name")
    default_temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    supports_reasoning: bool = Field(
        default=False, description="Whether model supports extended reasoning"
    )


class TestConfigs(BaseModel):
    """Test configuration options."""

    temperatures: list[float] = Field(default_factory=lambda: [0.0, 0.7, 1.0, 1.5])
    modes: list[Literal["theory", "action"]] = Field(
        default_factory=lambda: ["theory", "action"]
    )
    time_constraints: list[Literal["none", "moderate", "critical"]] = Field(
        default_factory=lambda: ["none", "moderate", "critical"]
    )


class OpenRouterConfig(BaseModel):
    """OpenRouter API configuration."""

    base_url: str = Field(default="https://openrouter.ai/api/v1")
    default_max_tokens: int = Field(default=2000, ge=1)


class GenerationConfig(BaseModel):
    """Dilemma generation settings."""

    generator_models: list[str] | None = Field(
        default=None,
        description="Models to use for generation. If None, uses all models from the main models list.",
    )
    default_model: str = Field(default="google/gemini-2.5-flash")
    default_temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=3000, ge=1)
    default_prompt_version: str = Field(default="v2_structured")

    prompt_versions: list[str] = Field(
        default_factory=lambda: ["v1_basic", "v2_structured", "v3_creative"]
    )

    num_actors: int = Field(default=3, ge=1)
    num_stakes: int = Field(default=2, ge=1)

    enable_validation: bool = Field(default=False)
    min_quality_score: float = Field(default=7.0, ge=0.0, le=10.0)
    min_originality_score: float = Field(default=6.0, ge=0.0, le=10.0)

    batch_size: int = Field(default=10, ge=1)
    ensure_diversity: bool = Field(default=True)
    max_retries_per_dilemma: int = Field(default=3, ge=1)

    # Variable extraction settings (two-step generation)
    add_variables: bool = Field(
        default=True,
        description="Extract variables for bias testing after generation",
    )
    variable_model: str | None = Field(
        default="moonshotai/kimi-k2-0905",
        description="Model to use for variable extraction. Fast model recommended. None = use generator model.",
    )


class ExperimentConfig(BaseModel):
    """Experiment settings."""

    dilemmas_per_test: int = Field(default=50, ge=1)
    repetitions: int = Field(default=3, ge=1)
    save_full_responses: bool = Field(default=True)
    save_reasoning_traces: bool = Field(default=True)


class ProjectConfig(BaseModel):
    """Complete project configuration loaded from YAML."""

    models: list[ModelConfig]
    test_configs: TestConfigs
    openrouter: OpenRouterConfig
    generation: GenerationConfig
    experiment: ExperimentConfig

    @model_validator(mode="after")
    def populate_generator_models(self) -> "ProjectConfig":
        """Auto-populate generator_models from models list if not specified."""
        if not self.generation.generator_models:
            self.generation.generator_models = [m.id for m in self.models]
        return self


class Settings(BaseSettings):
    """Environment settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    default_model: str = Field(
        default="google/gemini-2.5-flash",
        description="Default model to use if not specified",
    )


def load_config(config_path: Path | str | None = None) -> ProjectConfig:
    """Load project configuration from YAML file.

    Args:
        config_path: Path to config.yaml. If None, looks in project root.

    Returns:
        ProjectConfig instance with all settings loaded.
    """
    if config_path is None:
        # Look for config.yaml in project root
        config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    return ProjectConfig(**config_data)


def load_settings() -> Settings:
    """Load environment settings from .env file.

    Returns:
        Settings instance with environment variables.
    """
    return Settings()


# Singleton instances for easy access
_config: ProjectConfig | None = None
_settings: Settings | None = None


def get_config() -> ProjectConfig:
    """Get or create the project config singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_settings() -> Settings:
    """Get or create the settings singleton."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
