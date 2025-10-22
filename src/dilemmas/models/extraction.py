"""Models for variable extraction from dilemmas."""

from pydantic import BaseModel, Field


class Variable(BaseModel):
    """A single variable with its possible values."""

    name: str = Field(
        ...,
        description="Variable name in UPPER_SNAKE_CASE (without braces). Example: 'DOCTOR_NAME'",
    )
    values: list[str] = Field(
        ...,
        min_length=2,
        description="List of 2-4 concrete values for bias testing. Should span meaningful diversity.",
    )


class VariableExtraction(BaseModel):
    """Result of extracting variables from a dilemma.

    This is used as structured output for the variable extraction step.
    The LLM analyzes a concrete situation and identifies elements that
    should vary for bias testing.
    """

    rewritten_situation: str = Field(
        ...,
        description=(
            "The situation rewritten with {PLACEHOLDERS} for variables. "
            "Use {VARIABLE_NAME} format. Preserve the original meaning and ethical tension. "
            "Example: 'You are managing {DOCTOR_NAME}, a {SPECIALTY}, who made an error affecting {PATIENT_TYPE}.'"
        ),
    )

    variables: list[Variable] = Field(
        ...,
        min_length=1,
        description=(
            "List of variables extracted from the situation. "
            "Each variable should have 2-4 diverse concrete values for testing bias."
        ),
    )

    def to_variables_dict(self) -> dict[str, list[str]]:
        """Convert to dict format for Dilemma model.

        Returns:
            Dict mapping {VARIABLE_NAME} to list of values
        """
        return {f"{{{var.name}}}": var.values for var in self.variables}
