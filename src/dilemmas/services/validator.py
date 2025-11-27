"""Dilemma validation and repair service.

This service uses an LLM to validate generated dilemmas and automatically
repair minor issues.
"""

import logging
from pathlib import Path

from pydantic_ai import Agent

from dilemmas.llm.openrouter import create_openrouter_model
from dilemmas.models.config import get_config
from dilemmas.models.dilemma import Dilemma
from dilemmas.models.validation import RepairPlan, ValidationResult

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when a dilemma cannot be validated or repaired."""

    pass


class DilemmaValidator:
    """Validates and repairs generated dilemmas using LLM quality checks.

    This is the "Tier 3" quality control layer that catches semantic issues
    that Pydantic validators can't detect.
    """

    def __init__(
        self,
        validator_model: str | None = None,
        repairer_model: str | None = None,
        temperature: float = 0.3,  # Lower temp for more consistent validation
    ):
        """Initialize validator with LLM models.

        Args:
            validator_model: Model to use for validation (defaults to config)
            repairer_model: Model to use for repairs (defaults to config)
            temperature: Temperature for LLM calls (lower = more consistent)
        """
        config = get_config()

        self.validator_model = validator_model or config.generation.variable_model
        self.repairer_model = repairer_model or config.generation.variable_model
        self.temperature = temperature

        # Load prompts
        prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts" / "validation"
        self.system_prompt = (prompts_dir / "system.md").read_text()
        self.validate_prompt_template = (prompts_dir / "validate.md").read_text()
        self.repair_prompt_template = (prompts_dir / "repair.md").read_text()

        # Create pydantic-ai agents
        self.validator_agent = Agent(
            create_openrouter_model(self.validator_model),
            output_type=ValidationResult,
            system_prompt=self.system_prompt,
        )

        self.repairer_agent = Agent(
            create_openrouter_model(self.repairer_model),
            output_type=RepairPlan,
            system_prompt=self.system_prompt,
        )

    async def validate(self, dilemma: Dilemma) -> ValidationResult:
        """Validate a dilemma using LLM quality assessment.

        Args:
            dilemma: The dilemma to validate

        Returns:
            ValidationResult with scores, issues, and recommendation
        """
        logger.info(f"Validating dilemma: {dilemma.title}")

        # Format choices for prompt WITH tool_name
        choices_formatted = "\n".join(
            f"- **{c.label}** (tool: {c.tool_name or 'MISSING'}): {c.description}"
            for c in dilemma.choices
        )

        # Format tools for prompt
        if dilemma.available_tools:
            tools_formatted = "\n".join(
                f"- **{t.name}**: {t.description}" for t in dilemma.available_tools
            )
        else:
            tools_formatted = "(no tools defined)"

        # Format variables/modifiers presence
        has_variables = f"Yes ({len(dilemma.variables)} variables)" if dilemma.variables else "No"
        has_modifiers = f"Yes ({len(dilemma.modifiers)} modifiers)" if dilemma.modifiers else "No"

        # Build prompt using manual replacement to avoid issues with braces in content
        # Cannot use .format() because dilemma text might contain {PLACEHOLDERS}
        prompt = self.validate_prompt_template
        prompt = prompt.replace("{title}", dilemma.title)
        prompt = prompt.replace("{situation_template}", dilemma.situation_template)
        prompt = prompt.replace("{question}", dilemma.question)
        prompt = prompt.replace("{choices_formatted}", choices_formatted)
        prompt = prompt.replace("{tools_formatted}", tools_formatted)
        prompt = prompt.replace("{action_context}", dilemma.action_context or "(not provided)")
        prompt = prompt.replace("{has_variables}", has_variables)
        prompt = prompt.replace("{has_modifiers}", has_modifiers)
        prompt = prompt.replace("{difficulty_intended}", str(dilemma.difficulty_intended))

        # Run validation
        try:
            result = await self.validator_agent.run(prompt)
        except Exception as e:
            logger.error(f"Validation agent crashed: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise

        # DEBUG: Log validation results
        logger.info(f"\n{'='*60}")
        logger.info(f"VALIDATION RESULT")
        logger.info(f"{'='*60}")
        logger.info(f"Recommendation: {result.output.recommendation}")
        logger.info(f"Quality: {result.output.quality_score}/10")
        logger.info(f"Interest: {result.output.interest_score}/10")
        logger.info(f"Realism: {result.output.realism_score}/10")
        logger.info(f"Issues found: {len(result.output.issues)}")
        for issue in result.output.issues:
            logger.info(f"  - [{issue.severity}] {issue.field}: {issue.message[:80]}...")
        logger.info(f"Can auto-repair: {result.output.can_auto_repair}")
        logger.info(f"{'='*60}\n")

        return result.output

    async def repair(self, dilemma: Dilemma, validation: ValidationResult) -> Dilemma:
        """Attempt to repair a dilemma based on validation issues.

        Args:
            dilemma: The dilemma to repair
            validation: The validation result with issues to fix

        Returns:
            Repaired dilemma

        Raises:
            ValidationError: If repair is not possible
        """
        logger.info(f"Attempting to repair dilemma: {dilemma.title}")

        if not validation.can_auto_repair:
            raise ValidationError(
                f"Dilemma cannot be auto-repaired. Issues: {[i.message for i in validation.issues]}"
            )

        # Format choices for prompt WITH tool_name
        choices_formatted = "\n".join(
            f"- **{c.label}** (tool: {c.tool_name or 'MISSING'}): {c.description}"
            for c in dilemma.choices
        )

        # Format tools for prompt
        if dilemma.available_tools:
            tools_formatted = "\n".join(
                f"- **{t.name}**: {t.description}" for t in dilemma.available_tools
            )
        else:
            tools_formatted = "(no tools defined)"

        # Format issues for prompt
        issues_formatted = "\n".join(
            f"- **{i.field}** ({i.severity}): {i.message}\n  Suggestion: {i.repair_suggestion or 'No specific suggestion'}"
            for i in validation.issues
        )

        # Build repair prompt using manual replacement to avoid issues with braces
        prompt = self.repair_prompt_template
        prompt = prompt.replace("{title}", dilemma.title)
        prompt = prompt.replace("{situation_template}", dilemma.situation_template)
        prompt = prompt.replace("{question}", dilemma.question)
        prompt = prompt.replace("{choices_formatted}", choices_formatted)
        prompt = prompt.replace("{tools_formatted}", tools_formatted)
        prompt = prompt.replace("{action_context}", dilemma.action_context or "(not provided)")
        prompt = prompt.replace("{issues_formatted}", issues_formatted)

        # Run repair
        result = await self.repairer_agent.run(prompt)
        repair_plan = result.output

        # DEBUG: Log repair plan
        logger.info(f"\n{'='*60}")
        logger.info(f"REPAIR PLAN")
        logger.info(f"{'='*60}")
        logger.info(f"Can repair: {repair_plan.can_repair}")
        logger.info(f"Confidence: {repair_plan.confidence:.2f}")
        logger.info(f"Changes suggested: {list(repair_plan.changes.keys())}")
        for field, new_value in repair_plan.changes.items():
            preview = new_value[:100] + "..." if len(new_value) > 100 else new_value
            logger.info(f"  - {field}: {preview}")
        logger.info(f"Reasoning: {repair_plan.reasoning[:200]}...")
        logger.info(f"{'='*60}\n")

        if not repair_plan.can_repair:
            raise ValidationError(
                f"Repairer determined dilemma cannot be fixed: {repair_plan.reasoning}"
            )

        if repair_plan.confidence < 0.6:
            logger.warning(
                f"Low confidence repair (confidence={repair_plan.confidence}): {repair_plan.reasoning}"
            )

        # Apply repairs to create new dilemma
        repaired_data = dilemma.model_dump()

        # DEBUG: Log what repair plan suggests
        logger.info(f"Repair plan suggests changes to: {list(repair_plan.changes.keys())}")

        for field, new_value in repair_plan.changes.items():
            if field in repaired_data:
                repaired_data[field] = new_value
                logger.info(f"Applied repair to {field}")
            else:
                logger.warning(
                    f"Repair suggested invalid field '{field}' (not in Dilemma model) - ignoring. "
                    f"Valid fields: {list(repaired_data.keys())[:10]}..."
                )
                # Don't apply repairs to non-existent fields

        # Create repaired dilemma (this might fail if changes dict has issues)
        try:
            repaired = Dilemma(**repaired_data)
        except Exception as e:
            logger.error(f"Failed to create repaired dilemma: {e}")
            logger.error(f"Repair changes attempted: {repair_plan.changes}")
            raise

        logger.info(
            f"Repair complete: {len(repair_plan.changes)} fields changed. "
            f"Confidence: {repair_plan.confidence:.2f}"
        )

        return repaired

    async def validate_and_repair(
        self,
        dilemma: Dilemma,
        max_repair_attempts: int = 2,
        min_quality_score: float = 7.0,
    ) -> tuple[Dilemma, ValidationResult]:
        """Validate a dilemma and attempt repair if needed.

        This is the main entry point for the validation pipeline.

        Args:
            dilemma: The dilemma to validate
            max_repair_attempts: Maximum number of repair attempts
            min_quality_score: Minimum acceptable quality score

        Returns:
            (final_dilemma, final_validation_result)

        Raises:
            ValidationError: If dilemma cannot be validated/repaired

        Example:
            >>> validator = DilemmaValidator()
            >>> dilemma, validation = await validator.validate_and_repair(raw_dilemma)
            >>> if validation.recommendation == "accept":
            ...     # Use the dilemma
            ...     save_to_database(dilemma)
        """
        logger.info(f"Starting validation pipeline for: {dilemma.title}")

        # Step 1: Initial validation
        validation = await self.validate(dilemma)

        # Step 2: If valid and high quality, return immediately
        if validation.is_valid and validation.quality_score >= min_quality_score:
            logger.info(f"✓ Dilemma passed validation (quality={validation.quality_score}/10)")
            return dilemma, validation

        # Step 3: If critical issues, reject immediately (don't waste time repairing)
        if validation.max_severity == "critical":
            raise ValidationError(
                f"Dilemma has critical issues that cannot be repaired: "
                f"{[i.message for i in validation.issues if i.severity == 'critical']}"
            )

        # Step 4: If recommendation is reject, don't try to repair
        if validation.recommendation == "reject":
            raise ValidationError(
                f"Validation recommends rejection. "
                f"Quality: {validation.quality_score}/10. "
                f"Issues: {[i.message for i in validation.issues]}"
            )

        # Step 5: Attempt repairs if repairable
        if not validation.can_auto_repair:
            raise ValidationError(
                f"Dilemma has issues that cannot be auto-repaired: "
                f"{[i.message for i in validation.issues]}"
            )

        # Step 6: Try repairing
        current_dilemma = dilemma
        best_quality = validation.quality_score
        best_dilemma = dilemma
        best_validation = validation

        for attempt in range(max_repair_attempts):
            logger.info(f"Repair attempt {attempt + 1}/{max_repair_attempts}")

            try:
                # Repair
                repaired = await self.repair(current_dilemma, validation)

                # Re-validate repaired version
                new_validation = await self.validate(repaired)

                # Check if repair improved quality
                if new_validation.quality_score > best_quality:
                    best_quality = new_validation.quality_score
                    best_dilemma = repaired
                    best_validation = new_validation

                    logger.info(
                        f"Repair improved quality: {validation.quality_score:.1f} → "
                        f"{new_validation.quality_score:.1f}"
                    )

                # If now acceptable, return
                if (
                    new_validation.is_valid
                    and new_validation.quality_score >= min_quality_score
                    and new_validation.recommendation == "accept"
                ):
                    logger.info(
                        f"✓ Dilemma repaired successfully after {attempt + 1} attempt(s)"
                    )
                    return repaired, new_validation

                # Prepare for next attempt
                current_dilemma = repaired
                validation = new_validation

            except Exception as e:
                logger.warning(f"Repair attempt {attempt + 1} failed: {e}")
                # Continue with next attempt if we have tries left
                if attempt == max_repair_attempts - 1:
                    # Last attempt failed, raise error
                    raise ValidationError(
                        f"Could not repair dilemma after {max_repair_attempts} attempts. "
                        f"Best quality achieved: {best_quality:.1f}/10"
                    ) from e

        # Exhausted all attempts
        # Return best version if it meets minimum quality, otherwise fail
        if best_quality >= min_quality_score - 1.0:  # Allow 1 point grace
            logger.warning(
                f"Returning best version with quality {best_quality:.1f}/10 "
                f"(below target {min_quality_score}/10)"
            )
            return best_dilemma, best_validation
        else:
            raise ValidationError(
                f"Could not achieve acceptable quality after {max_repair_attempts} repair attempts. "
                f"Best quality: {best_quality:.1f}/10 (target: {min_quality_score}/10)"
            )


# Convenience function for one-off validation
async def validate_dilemma(dilemma: Dilemma, attempt_repair: bool = True) -> tuple[Dilemma, ValidationResult]:
    """Convenience function to validate a single dilemma.

    Args:
        dilemma: The dilemma to validate
        attempt_repair: Whether to attempt repairs if issues are found

    Returns:
        (final_dilemma, validation_result)

    Example:
        >>> dilemma, validation = await validate_dilemma(my_dilemma)
        >>> if validation.recommendation == "accept":
        ...     print(f"Quality: {validation.quality_score}/10")
    """
    validator = DilemmaValidator()

    if attempt_repair:
        return await validator.validate_and_repair(dilemma)
    else:
        validation = await validator.validate(dilemma)
        return dilemma, validation
