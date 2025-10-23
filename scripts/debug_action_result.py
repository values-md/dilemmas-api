"""Debug script to see what's in the agent result for action mode."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic_ai import Agent
from dilemmas.llm.openrouter import create_openrouter_model
from dilemmas.models.dilemma import Dilemma, DilemmaChoice
from dilemmas.tools.actions import execute_decision


async def debug():
    # Create a simple test dilemma
    dilemma = Dilemma(
        title="Test Dilemma",
        situation_template="You must choose.",
        question="What will you do?",
        choices=[
            DilemmaChoice(id="option_a", label="Option A", description="Do A"),
            DilemmaChoice(id="option_b", label="Option B", description="Do B"),
        ],
        tags=["test"],
        difficulty_level=5,
        created_by="test",
    )

    # Create agent with tool
    agent = Agent(
        create_openrouter_model("openai/gpt-4.1-mini", 1.0),
        tools=[execute_decision],
        deps_type=Dilemma,
    )

    # Run
    result = await agent.run(
        "You must choose between option_a and option_b. Use the execute_decision tool.",
        deps=dilemma
    )

    print("Result type:", type(result))
    print("\nAttributes:")
    for attr in dir(result):
        if not attr.startswith('_'):
            print(f"  - {attr}")

    print("\ndata attribute:", hasattr(result, 'data'))
    if hasattr(result, 'data'):
        print("data:", result.data)

    print("\nall_messages attribute:", hasattr(result, 'all_messages'))
    if hasattr(result, 'all_messages'):
        print("all_messages count:", len(result.all_messages()))
        for msg in result.all_messages():
            print(f"  Message type: {type(msg).__name__}")
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    print(f"    Part type: {type(part).__name__}")
                    if hasattr(part, 'tool_name'):
                        print(f"      Tool: {part.tool_name}")
                        print(f"      Args: {part.args if hasattr(part, 'args') else 'N/A'}")


if __name__ == "__main__":
    asyncio.run(debug())
