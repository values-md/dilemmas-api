#!/usr/bin/env python3
"""Test OpenRouter connectivity with pydantic-ai."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.llm.agents import create_test_agent
from dilemmas.models.config import get_config


async def test_connection():
    """Test connection to OpenRouter with each configured model."""
    print("Testing OpenRouter connectivity with pydantic-ai...\n")

    config = get_config()

    # Test with default model first
    print(f"Testing default model: {config.models[0].name} ({config.models[0].id})")
    try:
        agent = create_test_agent()
        result = await agent.run("Say 'Hello! I am working.' in one sentence.")
        print(f"✓ Success! Response: {result.output}\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
        return 1

    # Optionally test one more model
    if len(config.models) > 1:
        test_model = config.models[-1]  # Test last model (Gemini)
        print(f"Testing {test_model.name} ({test_model.id})")
        try:
            agent = create_test_agent(test_model.id)
            result = await agent.run("Say 'Hello! I am working.' in one sentence.")
            print(f"✓ Success! Response: {result.output}\n")
        except Exception as e:
            print(f"✗ Failed: {e}\n")
            return 1

    print("✓ All OpenRouter connectivity tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(test_connection()))
