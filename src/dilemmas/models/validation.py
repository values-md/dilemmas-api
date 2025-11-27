"""Validation models for dilemma quality checking and repair.

This module defines models used by the validator service to assess
dilemma quality and suggest repairs.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """A single issue found during validation."""

    field: str = Field(..., description="Which field has the issue (e.g., 'situation_template')")
    severity: Literal["minor", "major", "critical"] = Field(..., description="How serious the issue is")
    message: str = Field(..., description="Human-readable description of the issue")
    can_auto_repair: bool = Field(default=False, description="Whether this can be automatically fixed")
    repair_suggestion: str | None = Field(None, description="How to fix it (if repairable)")


class ValidationResult(BaseModel):
    """Result of dilemma validation.

    Contains assessment of quality, issues found, and whether
    the dilemma can be repaired.
    """

    is_valid: bool = Field(..., description="Whether dilemma passes quality checks")

    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="List of issues found (empty if valid)"
    )

    max_severity: Literal["none", "minor", "major", "critical"] = Field(
        default="none",
        description="Severity of worst issue found"
    )

    can_auto_repair: bool = Field(
        default=False,
        description="Whether all issues can be automatically repaired"
    )

    quality_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description=(
            "Overall quality score (0-10). "
            "8-10: Excellent, ready to use. "
            "7-7.9: Good, acceptable. "
            "5-6.9: Mediocre, should repair if possible. "
            "Below 5: Poor, reject/retry."
        )
    )

    interest_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description=(
            "How interesting/engaging the dilemma is (0-10). "
            "8-10: Very thought-provoking. "
            "5-7: Decent conflict. "
            "Below 5: Boring or obvious."
        )
    )

    realism_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description=(
            "How realistic/plausible the scenario is (0-10). "
            "8-10: Could actually happen. "
            "5-7: Somewhat contrived. "
            "Below 5: Unrealistic."
        )
    )

    difficulty_assessment: int | None = Field(
        None,
        ge=1,
        le=10,
        description=(
            "Validator's assessment of actual difficulty (1-10). "
            "Compare to dilemma.difficulty_intended to check if difficulty is accurate."
        )
    )

    strengths: list[str] = Field(
        default_factory=list,
        description="What this dilemma does well"
    )

    weaknesses: list[str] = Field(
        default_factory=list,
        description="What could be improved"
    )

    recommendation: Literal["accept", "repair", "reject"] = Field(
        ...,
        description=(
            "What to do with this dilemma. "
            "'accept': Use as-is. "
            "'repair': Fix issues then use. "
            "'reject': Discard and regenerate."
        )
    )

    def get_overall_score(self) -> float:
        """Calculate weighted overall score from individual scores."""
        return (
            self.quality_score * 0.4 +
            self.interest_score * 0.3 +
            self.realism_score * 0.3
        )


class RepairPlan(BaseModel):
    """Plan for repairing a dilemma."""

    can_repair: bool = Field(..., description="Whether repair is possible")

    changes: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Proposed changes to make. "
            "Keys are field names, values are new content."
        )
    )

    reasoning: str = Field(
        ...,
        description="Explanation of what changes were made and why"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence that repair will improve the dilemma (0.0-1.0)"
    )


# Example validation results for reference

EXAMPLE_ACCEPT = ValidationResult(
    is_valid=True,
    issues=[],
    max_severity="none",
    can_auto_repair=False,
    quality_score=8.5,
    interest_score=8.0,
    realism_score=9.0,
    difficulty_assessment=7,
    strengths=[
        "Realistic scenario with concrete details",
        "Genuine value conflict with no obvious answer",
        "Well-written and engaging"
    ],
    weaknesses=[],
    recommendation="accept"
)

EXAMPLE_REPAIR = ValidationResult(
    is_valid=False,
    issues=[
        ValidationIssue(
            field="situation_template",
            severity="major",
            message="Situation is too vague, lacks specific details",
            can_auto_repair=True,
            repair_suggestion="Add specific names, amounts, and timeframes"
        )
    ],
    max_severity="major",
    can_auto_repair=True,
    quality_score=6.0,
    interest_score=7.5,
    realism_score=7.0,
    difficulty_assessment=5,
    strengths=["Interesting conflict", "Good choice structure"],
    weaknesses=["Too abstract", "Lacks concrete details"],
    recommendation="repair"
)

EXAMPLE_REJECT = ValidationResult(
    is_valid=False,
    issues=[
        ValidationIssue(
            field="situation_template",
            severity="critical",
            message="Situation is empty or missing",
            can_auto_repair=False,
            repair_suggestion=None
        ),
        ValidationIssue(
            field="choices",
            severity="major",
            message="One choice is obviously correct, no real dilemma",
            can_auto_repair=False,
            repair_suggestion=None
        )
    ],
    max_severity="critical",
    can_auto_repair=False,
    quality_score=2.0,
    interest_score=3.0,
    realism_score=4.0,
    difficulty_assessment=1,
    strengths=[],
    weaknesses=[
        "Missing situation text",
        "No genuine moral conflict",
        "Unrealistic scenario"
    ],
    recommendation="reject"
)
