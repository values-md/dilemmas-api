"""Action tools for ethical dilemma agents.

In action mode, we dynamically create mock tools from the dilemma's
ToolSchema definitions. The agent calls these tools to execute decisions.

v2 methodology:
- Tools have `reasoning` and `confidence` as required parameters
- Parameters are extracted directly from the tool call
- No follow-up prompt needed
"""

from typing import Any, Callable

from pydantic_ai import Tool

from dilemmas.models.dilemma import ToolSchema


def create_mock_tool(tool_schema: ToolSchema) -> Callable:
    """Create a mock tool from a ToolSchema.

    Creates a properly typed function that PydanticAI can use.
    All v2 tools have reasoning + confidence as required parameters.

    Args:
        tool_schema: The tool schema defining the tool

    Returns:
        A callable function that can be used as a pydantic-ai tool
    """
    # Create a function with proper type annotations
    # PydanticAI extracts the schema from function signature
    async def mock_tool_impl(reasoning: str, confidence: int) -> str:
        """Execute this action.

        Args:
            reasoning: Your reasoning for this choice (2-4 sentences)
            confidence: How confident you are (1-10 scale)

        Returns:
            Confirmation message
        """
        return (
            f"Action executed successfully.\n"
            f"Reasoning recorded: {reasoning[:50]}...\n"
            f"Confidence: {confidence}/10"
        )

    # Set the function name and docstring
    mock_tool_impl.__name__ = tool_schema.name
    mock_tool_impl.__doc__ = f"""{tool_schema.description}

Args:
    reasoning: Your reasoning for this choice (2-4 sentences explaining why you chose this action)
    confidence: How confident you are in this choice (1=very uncertain, 10=completely certain)
"""

    return mock_tool_impl


def create_mock_tool_v1(tool_schema: ToolSchema) -> Callable:
    """Create a mock tool function from a ToolSchema (legacy v1 style).

    The tool will accept any keyword arguments and return a success message.
    This simulates the agent making a real API call.

    Args:
        tool_schema: The tool schema defining the tool

    Returns:
        A callable function that can be used as a pydantic-ai tool
    """

    async def mock_tool(**kwargs: Any) -> str:
        """Mock implementation of the tool.

        Args:
            **kwargs: Any parameters defined in the tool schema

        Returns:
            Success confirmation message
        """
        # Format the parameters
        params_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())

        return (
            f"✓ {tool_schema.name} executed successfully\n"
            f"Parameters: {params_str}\n\n"
            f"Your action has been implemented."
        )

    # Set function metadata for pydantic-ai
    mock_tool.__name__ = tool_schema.name
    mock_tool.__doc__ = tool_schema.description

    return mock_tool
