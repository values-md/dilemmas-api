#!/usr/bin/env python3
"""Test thinking/reasoning tokens with PydanticAI + OpenRouter.

This script tests all 9 models from the bench2 experiment config
to verify which ones support reasoning/thinking tokens.

Usage:
    uv run python scripts/test_thinking_tokens.py
"""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pydantic_ai import Agent
from pydantic_ai.messages import ThinkingPart
from pydantic_ai.models import ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

# All models from bench2 config
MODELS = [
    "anthropic/claude-opus-4.5",
    "openai/gpt-5",
    "openai/gpt-5-nano",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    "google/gemini-3-pro-preview",
    "google/gemini-2.5-flash",
    "x-ai/grok-4",
    "x-ai/grok-4-fast",
]

# Simple prompt for testing
TEST_PROMPT = """What is 15 * 17? Think through this step by step before giving your answer."""


async def test_model_thinking(model_id: str, provider: OpenRouterProvider) -> dict:
    """Test a single model for thinking token support.

    Returns dict with results.
    """
    result = {
        "model": model_id,
        "success": False,
        "has_thinking": False,
        "thinking_content": None,
        "thinking_full": None,  # Full thinking content
        "response_preview": None,
        "response_full": None,  # Full response
        "error": None,
    }

    try:
        model = OpenAIChatModel(model_id, provider=provider)

        # Try with reasoning enabled
        settings = ModelSettings(
            extra_body={"reasoning": {"effort": "medium"}}
        )

        agent = Agent(model, model_settings=settings)
        response = await agent.run(TEST_PROMPT)

        result["success"] = True
        result["response_preview"] = str(response.output)[:150]
        result["response_full"] = str(response.output)

        # Look for ThinkingPart
        for message in response.all_messages():
            if hasattr(message, "parts"):
                for part in message.parts:
                    if isinstance(part, ThinkingPart):
                        result["has_thinking"] = True
                        result["thinking_content"] = str(part.content)[:200] if part.content else "(empty)"
                        result["thinking_full"] = str(part.content) if part.content else None
                        break
            if result["has_thinking"]:
                break

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:100]}"

    return result


async def test_all_models() -> list[dict]:
    """Test all models for thinking token support."""

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return []

    print("=" * 70)
    print("Testing Thinking Tokens - All 9 Bench2 Models")
    print("=" * 70)
    print(f"\nPrompt: {TEST_PROMPT}\n")

    provider = OpenRouterProvider(api_key=api_key)

    results = []

    for i, model_id in enumerate(MODELS, 1):
        print(f"\n[{i}/9] Testing: {model_id}")
        print("-" * 50)

        result = await test_model_thinking(model_id, provider)
        results.append(result)

        if result["error"]:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Response: {result['response_preview']}...")
            if result["has_thinking"]:
                print(f"  THINKING: {result['thinking_content']}...")
            else:
                print(f"  THINKING: (none found)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"\n{'Model':<35} {'Status':<12} {'Thinking':<10}")
    print("-" * 60)

    for r in results:
        status = "OK" if r["success"] else "FAILED"
        thinking = "YES" if r["has_thinking"] else "no"
        print(f"{r['model']:<35} {status:<12} {thinking:<10}")

    # Models with thinking
    thinking_models = [r["model"] for r in results if r["has_thinking"]]
    failed_models = [r["model"] for r in results if not r["success"]]

    print(f"\nModels with thinking tokens: {len(thinking_models)}/{len(MODELS)}")
    if thinking_models:
        for m in thinking_models:
            print(f"  - {m}")

    if failed_models:
        print(f"\nFailed models: {len(failed_models)}")
        for m in failed_models:
            print(f"  - {m}")

    return results


async def test_direct_api():
    """Test direct OpenRouter API to see raw response format."""
    import httpx

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return

    print("\n" + "=" * 70)
    print("Direct API Test (anthropic/claude-sonnet-4.5)")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "anthropic/claude-sonnet-4.5",
                "messages": [
                    {"role": "user", "content": TEST_PROMPT}
                ],
                "reasoning": {"effort": "medium"},
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n[OK] Response received")

            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                print(f"\nMessage keys: {list(message.keys())}")

                # Check for reasoning fields
                for key in ["reasoning", "reasoning_content", "thinking"]:
                    if key in message:
                        print(f"\n[FOUND] {key}: {str(message[key])[:200]}...")

                content = message.get("content", "")
                print(f"\nContent: {content[:200]}...")

            usage = data.get("usage", {})
            print(f"\nUsage: {usage}")
        else:
            print(f"\n[ERROR] Status {response.status_code}")
            print(f"Body: {response.text[:300]}")


def save_results(results: list[dict], output_dir: str):
    """Save test results to files for inspection."""
    import json
    from datetime import datetime

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save JSON with all data
    json_path = os.path.join(output_dir, f"thinking_tokens_test_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] JSON: {json_path}")

    # Save human-readable markdown
    md_path = os.path.join(output_dir, f"thinking_tokens_test_{timestamp}.md")
    with open(md_path, "w") as f:
        f.write("# Thinking Tokens Test Results\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Prompt:** {TEST_PROMPT}\n\n")
        f.write("## Summary\n\n")
        f.write("| Model | Status | Thinking |\n")
        f.write("|-------|--------|----------|\n")
        for r in results:
            status = "OK" if r["success"] else "FAILED"
            thinking = "YES" if r["has_thinking"] else "no"
            f.write(f"| {r['model']} | {status} | {thinking} |\n")

        f.write("\n## Detailed Results\n\n")
        for r in results:
            f.write(f"### {r['model']}\n\n")
            if r["error"]:
                f.write(f"**ERROR:** {r['error']}\n\n")
            else:
                f.write("**Response:**\n```\n")
                f.write(r.get("response_full", "(no response)") or "(empty)")
                f.write("\n```\n\n")
                if r["has_thinking"]:
                    f.write("**Thinking:**\n```\n")
                    f.write(r.get("thinking_full", "(no thinking)") or "(empty)")
                    f.write("\n```\n\n")
                else:
                    f.write("**Thinking:** (none captured)\n\n")
            f.write("---\n\n")

    print(f"[SAVED] Markdown: {md_path}")


if __name__ == "__main__":
    print("Loading environment...")

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"Loaded .env")

    # Run tests and save results
    results = asyncio.run(test_all_models())
    if results:
        output_dir = os.path.join(
            os.path.dirname(__file__), "..", "research", "2025-11-27-when-agents-act"
        )
        save_results(results, output_dir)

    asyncio.run(test_direct_api())
