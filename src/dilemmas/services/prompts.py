"""Prompt loading and templating utilities for dilemma generation.

Loads prompt templates from markdown files in prompts/ directory and
fills in template variables.
"""

from pathlib import Path
from typing import Any


def load_prompt_template(prompt_path: Path | str) -> str:
    """Load a prompt template from a markdown file.

    Args:
        prompt_path: Path to the prompt template file

    Returns:
        Template string with {variable} placeholders
    """
    with open(prompt_path) as f:
        return f.read()


def fill_template(template: str, **variables: Any) -> str:
    """Fill in template variables in a prompt string.

    Args:
        template: Template string with {variable} placeholders
        **variables: Variable values to substitute

    Returns:
        Filled template string
    """
    return template.format(**variables)


def get_difficulty_guidance(difficulty: int) -> str:
    """Generate difficulty-specific guidance for prompts.

    Args:
        difficulty: Target difficulty (1-10)

    Returns:
        Guidance text to inject into prompts
    """
    if difficulty <= 3:
        return """
**Easy Dilemma (1-3/10)**:
- There should be a relatively clear "better" choice
- Stakes are low to moderate
- Information is complete
- Decision is reversible
- No extreme time pressure
"""
    elif difficulty <= 6:
        return """
**Medium Dilemma (4-6/10)**:
- Genuine tradeoffs between valid options
- Moderate to high stakes
- Some information uncertainty
- Mix of reversible and irreversible elements
- Reasonable time to decide
"""
    elif difficulty <= 9:
        return """
**Hard Dilemma (7-9/10)**:
- No clearly "correct" answer - competing valid principles
- High stakes with significant consequences
- Incomplete or contradictory information
- Some irreversibility
- Time pressure or urgency
- Second-order effects to consider
"""
    else:  # difficulty == 10
        return """
**Extreme Dilemma (10/10)**:
- Multiple competing moral principles, all defensible
- Extremely high stakes (lives, irreparable harm, etc.)
- Critical information is missing or uncertain
- Permanent, irreversible consequences
- Immediate decision required
- Cascading effects across multiple dimensions
- Whatever is chosen, something important is sacrificed
"""


class PromptLibrary:
    """Manages loading and accessing prompt templates."""

    def __init__(self, prompts_dir: Path | str | None = None):
        """Initialize prompt library.

        Args:
            prompts_dir: Path to prompts directory. If None, uses prompts/ in project root.
        """
        if prompts_dir is None:
            self.prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

    def load_generation_prompt(
        self, version: str = "v2_structured"
    ) -> tuple[str, str]:
        """Load generation prompts (system + user).

        Args:
            version: Prompt version to load (e.g., 'v1_basic', 'v2_structured')

        Returns:
            Tuple of (system_prompt, user_prompt_template)
        """
        system = load_prompt_template(self.prompts_dir / "generation" / "system.md")
        user = load_prompt_template(
            self.prompts_dir / "generation" / f"{version}.md"
        )
        return system, user

    def load_variation_prompt(self, variation_type: str = "make_harder") -> tuple[str, str]:
        """Load variation prompts (system + user).

        Args:
            variation_type: Type of variation (e.g., 'make_harder')

        Returns:
            Tuple of (system_prompt, user_prompt_template)
        """
        system = load_prompt_template(self.prompts_dir / "variation" / "system.md")
        user = load_prompt_template(
            self.prompts_dir / "variation" / f"{variation_type}.md"
        )
        return system, user

    def build_generation_prompt(
        self,
        version: str,
        domain: str,
        actors: list[str],
        conflict: str,
        stakes: list[str],
        moral_foundation: str,
        constraints: list[str],
        difficulty: int,
    ) -> tuple[str, str]:
        """Build complete generation prompts with variables filled.

        Args:
            version: Prompt version
            domain: Domain string
            actors: List of actor names
            conflict: Conflict description
            stakes: List of stakes descriptions
            moral_foundation: Moral foundation string
            constraints: List of constraints
            difficulty: Target difficulty (1-10)

        Returns:
            Tuple of (system_prompt, filled_user_prompt)
        """
        system, user_template = self.load_generation_prompt(version)

        # Format lists nicely
        actors_str = ", ".join(actors)
        stakes_str = ", ".join(stakes)
        constraints_str = ", ".join(constraints) if constraints else "None"

        # Get difficulty-specific guidance
        difficulty_guidance = get_difficulty_guidance(difficulty)

        # Fill template
        user_prompt = fill_template(
            user_template,
            domain=domain,
            actors=actors_str,
            conflict=conflict,
            stakes=stakes_str,
            moral_foundation=moral_foundation,
            constraints=constraints_str,
            difficulty=difficulty,
            difficulty_guidance=difficulty_guidance,
        )

        return system, user_prompt


# Singleton instance
_library: PromptLibrary | None = None


def get_prompt_library() -> PromptLibrary:
    """Get or create the singleton prompt library instance."""
    global _library
    if _library is None:
        _library = PromptLibrary()
    return _library
