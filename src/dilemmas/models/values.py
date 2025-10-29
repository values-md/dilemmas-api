"""Pydantic models for VALUES.md generation and storage."""

from datetime import datetime

from pydantic import BaseModel, Field


class DecisionRule(BaseModel):
    """A single decision rule with context and examples."""

    category: str = Field(..., description="Category name (e.g., 'Resource Allocation')")
    when: str = Field(..., description="WHEN clause - situation trigger")
    do: list[str] = Field(..., description="DO - actionable guidance (list of rules)")
    dont: list[str] = Field(..., description="DON'T - anti-patterns to avoid")
    example: str = Field(..., description="Concrete example scenario")


class ValueHierarchy(BaseModel):
    """Value conflict resolution with exceptions."""

    conflict: str = Field(..., description="Value A vs Value B")
    preference: str = Field(..., description="Which value takes priority and by how much")
    exceptions: list[str] = Field(
        default_factory=list, description="Situations where preference reverses"
    )


class ContextFactor(BaseModel):
    """How a context factor affects decision-making."""

    factor: str = Field(..., description="Context factor name (e.g., 'Urgency', 'Vulnerability')")
    adjustments: list[str] = Field(..., description="How to adjust approach based on this factor")


class ValuesMarkdown(BaseModel):
    """Structured representation of a VALUES.md file for LLM generation."""

    # Header
    generated_from_count: int = Field(..., description="Number of judgements analyzed")
    last_updated: str = Field(..., description="ISO date string")

    # Core content
    core_principles: list[str] = Field(
        ..., description="Ordered list of core values (most important first)"
    )
    decision_rules: list[DecisionRule] = Field(..., description="Decision rules by category")
    value_hierarchies: list[ValueHierarchy] = Field(
        ..., description="How to resolve value conflicts"
    )
    context_sensitivity: list[ContextFactor] = Field(
        ..., description="How context affects decisions"
    )

    # Metadata
    known_limitations: list[str] = Field(
        default_factory=list, description="Areas with lower confidence or limited data"
    )
    unresolved_tensions: list[str] = Field(
        default_factory=list, description="Value conflicts without clear resolution"
    )
    usage_notes: list[str] = Field(
        default_factory=list,
        description="Instructions for AI agents on how to use this file",
    )

    def to_markdown(self) -> str:
        """Convert structured data to markdown format."""
        lines = [
            "# Personal Values & Decision Framework",
            f"**Generated from**: {self.generated_from_count} judgements across multiple ethical dilemmas",
            f"**Last updated**: {self.last_updated}",
            "",
            "---",
            "",
            "## Core Principles",
            "",
            "When acting on behalf of this person, prioritize these values in order:",
            "",
        ]

        # Core principles
        for i, principle in enumerate(self.core_principles, 1):
            lines.append(f"{i}. {principle}")

        lines.extend(["", "---", "", "## Decision Rules", ""])

        # Decision rules
        for rule in self.decision_rules:
            lines.extend(
                [
                    f"### {rule.category}",
                    "",
                    f"**WHEN:** {rule.when}",
                    "",
                    "**DO:**",
                ]
            )
            for item in rule.do:
                lines.append(f"- {item}")

            lines.append("")
            lines.append("**DON'T:**")
            for item in rule.dont:
                lines.append(f"- {item}")

            lines.extend(["", f"**EXAMPLE:** {rule.example}", "", "---", ""])

        # Value hierarchies
        lines.extend(["## Value Hierarchies", "", "When these values conflict, apply this ordering:", ""])

        for i, hierarchy in enumerate(self.value_hierarchies, 1):
            lines.append(f"{i}. **{hierarchy.conflict}** ({hierarchy.preference})")
            if hierarchy.exceptions:
                for exception in hierarchy.exceptions:
                    lines.append(f"   - Exception: {exception}")
            lines.append("")

        lines.extend(["---", "", "## Context Sensitivity", "", "Adjust approach based on:", ""])

        # Context factors
        for factor in self.context_sensitivity:
            lines.append(f"**{factor.factor}:**")
            for adjustment in factor.adjustments:
                lines.append(f"- {adjustment}")
            lines.append("")

        lines.extend(["---", "", "## Known Limitations", ""])

        # Limitations
        if self.known_limitations:
            for limitation in self.known_limitations:
                lines.append(f"- {limitation}")
        else:
            lines.append("- None identified (sufficient data across all categories)")

        lines.append("")

        # Unresolved tensions
        if self.unresolved_tensions:
            lines.extend(["**Unresolved tensions:**", ""])
            for tension in self.unresolved_tensions:
                lines.append(f"- {tension}")
            lines.append("")

        lines.extend(["---", "", "## Usage Notes for AI Agents", ""])

        # Usage notes
        for note in self.usage_notes:
            lines.append(f"- {note}")

        return "\n".join(lines)
