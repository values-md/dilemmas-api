"""Tests for configuration loading and validation."""

import sys
from pathlib import Path

# Add src to path for tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from dilemmas.models.config import (
    ExperimentConfig,
    ModelConfig,
    OpenRouterConfig,
    ProjectConfig,
    TestConfigs,
    get_config,
    load_config,
)


def test_model_config_validation():
    """Test ModelConfig validation."""
    config = ModelConfig(
        id="test/model",
        name="Test Model",
        provider="openrouter",
        default_temperature=0.7,
        supports_reasoning=True,
    )
    assert config.id == "test/model"
    assert config.name == "Test Model"
    assert config.default_temperature == 0.7
    assert config.supports_reasoning is True


def test_model_config_defaults():
    """Test ModelConfig default values."""
    config = ModelConfig(id="test/model", name="Test Model")
    assert config.provider == "openrouter"
    assert config.default_temperature == 1.0
    assert config.supports_reasoning is False


def test_model_config_temperature_validation():
    """Test temperature bounds validation."""
    # Valid temperatures
    ModelConfig(id="test/model", name="Test", default_temperature=0.0)
    ModelConfig(id="test/model", name="Test", default_temperature=2.0)

    # Invalid temperatures should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        ModelConfig(id="test/model", name="Test", default_temperature=-0.1)

    with pytest.raises(Exception):
        ModelConfig(id="test/model", name="Test", default_temperature=2.1)


def test_test_configs_defaults():
    """Test TestConfigs default values."""
    config = TestConfigs()
    assert config.temperatures == [0.0, 0.7, 1.0, 1.5]
    assert config.modes == ["theory", "action"]
    assert config.time_constraints == ["none", "moderate", "critical"]


def test_openrouter_config_defaults():
    """Test OpenRouterConfig default values."""
    config = OpenRouterConfig()
    assert config.base_url == "https://openrouter.ai/api/v1"
    assert config.default_max_tokens == 2000


def test_experiment_config_defaults():
    """Test ExperimentConfig default values."""
    config = ExperimentConfig()
    assert config.dilemmas_per_test == 50
    assert config.repetitions == 3
    assert config.save_full_responses is True
    assert config.save_reasoning_traces is True


def test_load_config_from_yaml():
    """Test loading full config from YAML file."""
    # Load the actual config.yaml from project root
    config = load_config()

    assert isinstance(config, ProjectConfig)
    assert len(config.models) > 0
    assert isinstance(config.models[0], ModelConfig)
    assert isinstance(config.test_configs, TestConfigs)
    assert isinstance(config.openrouter, OpenRouterConfig)
    assert isinstance(config.experiment, ExperimentConfig)


def test_config_has_expected_models():
    """Test that config has the expected models configured."""
    config = get_config()

    # Should have exactly 5 models as currently configured
    assert len(config.models) == 5

    model_ids = [m.id for m in config.models]
    assert "google/gemini-2.5-flash" in model_ids
    assert "anthropic/claude-sonnet-4.5" in model_ids
    assert "openai/gpt-4.1-mini" in model_ids


def test_config_singleton():
    """Test that get_config returns the same instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
