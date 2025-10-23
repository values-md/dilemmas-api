"""Action tools for ethical dilemma agents.

In action mode, we dynamically create mock tools from the dilemma's
ToolSchema definitions. The agent calls these tools to execute decisions.
"""

from typing import Any, Callable

from dilemmas.models.dilemma import ToolSchema


def create_mock_tool(tool_schema: ToolSchema) -> Callable:
    """Create a mock tool function from a ToolSchema.

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
