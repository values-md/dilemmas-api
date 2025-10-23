"""Dilemma generation service using seed-based approach with LLMs."""

import json
import logging
import random
import re
from pathlib import Path
from typing import Literal

from pydantic_ai import Agent

from dilemmas.llm.openrouter import create_openrouter_model
from dilemmas.models.config import get_config
from dilemmas.models.dilemma import Dilemma
from dilemmas.models.extraction import VariableExtraction
from dilemmas.models.validation import ValidationResult
from dilemmas.services.prompts import get_prompt_library
from dilemmas.services.seeds import DilemmaSeed, generate_random_seed, get_seed_library

logger = logging.getLogger(__name__)


class DilemmaGenerator:
    """Generate ethical dilemmas using seed-based approach.

    Uses a two-phase approach:
    1. Sample random components from seed library
    2. Use LLM with structured output to synthesize coherent dilemma

    This ensures diversity and avoids clichéd scenarios.
    """

    def __init__(
        self,
        model_id: str | None = None,
        temperature: float | None = None,
        prompt_version: str | None = None,
    ):
        """Initialize generator.

        Args:
            model_id: Model to use. If None, uses config default.
            temperature: Temperature override. If None, uses config default.
            prompt_version: Prompt version to use. If None, uses config default.
        """
        self.config = get_config()
        self.seed_library = get_seed_library()
        self.prompt_library = get_prompt_library()

        # Set defaults from config
        self.model_id = model_id or self.config.generation.default_model
        self.temperature = temperature or self.config.generation.default_temperature
        self.prompt_version = (
            prompt_version or self.config.generation.default_prompt_version
        )

        # Create agent with structured output
        self.agent = Agent(
            create_openrouter_model(self.model_id, self.temperature),
            output_type=Dilemma,
        )

    async def generate_from_seed(self, seed: DilemmaSeed) -> Dilemma:
        """Generate a dilemma from seed components.

        Args:
            seed: Seed components to use

        Returns:
            Generated Dilemma
        """
        # Build prompts with seed components
        system_prompt, user_prompt = self.prompt_library.build_generation_prompt(
            version=self.prompt_version,
            domain=seed.domain,
            actors=seed.actors,
            conflict=seed.conflict.description,
            stakes=[f"{s.category}: {s.specific}" for s in seed.stakes],
            moral_foundation=seed.moral_foundation,
            constraints=seed.constraints,
            difficulty=seed.difficulty_target,
        )

        # Run agent with custom system prompt
        result = await self.agent.run(user_prompt, message_history=[], model_settings={"system": system_prompt})

        # Add generation metadata
        dilemma = result.output
        dilemma.created_by = self.model_id  # Set to actual model ID used
        dilemma.is_llm_generated = True
        dilemma.generator_model = self.model_id
        dilemma.generator_prompt_version = self.prompt_version
        dilemma.seed_components = {
            "domain": seed.domain,
            "actors": seed.actors,
            "conflict": seed.conflict.id,
            "stakes": [f"{s.category}: {s.specific}" for s in seed.stakes],
            "moral_foundation": seed.moral_foundation,
            "constraints": seed.constraints,
        }
        dilemma.generator_settings = {
            "temperature": self.temperature,
            "model": self.model_id,
            "prompt_version": self.prompt_version,
        }

        return dilemma

    async def generate_random(
        self,
        difficulty: int,
        num_actors: int | None = None,
        num_stakes: int | None = None,
        add_variables: bool | None = None,
    ) -> Dilemma:
        """Generate a random dilemma at target difficulty.

        Args:
            difficulty: Target difficulty (1-10)
            num_actors: Number of actors. If None, uses config default.
            num_stakes: Number of stakes. If None, uses config default.
            add_variables: Extract variables for bias testing. If None, uses config default.

        Returns:
            Generated Dilemma
        """
        # Use config defaults if not specified
        if num_actors is None:
            num_actors = self.config.generation.num_actors
        if num_stakes is None:
            num_stakes = self.config.generation.num_stakes
        if add_variables is None:
            add_variables = self.config.generation.add_variables

        # Generate random seed
        seed = generate_random_seed(
            library=self.seed_library,
            difficulty=difficulty,
            num_actors=num_actors,
            num_stakes=num_stakes,
        )

        # Generate dilemma
        dilemma = await self.generate_from_seed(seed)

        # Optionally extract variables
        if add_variables:
            dilemma = await self.variablize_dilemma(dilemma)

        return dilemma

    async def generate_batch(
        self,
        count: int,
        difficulty_range: tuple[int, int] = (1, 10),
        ensure_diversity: bool | None = None,
        add_variables: bool | None = None,
    ) -> list[Dilemma]:
        """Generate multiple dilemmas.

        Args:
            count: Number of dilemmas to generate
            difficulty_range: (min, max) difficulty range
            ensure_diversity: If True, ensures variety in domains/conflicts.
                             If None, uses config default.
            add_variables: Extract variables for bias testing. If None, uses config default.

        Returns:
            List of generated Dilemmas
        """
        if ensure_diversity is None:
            ensure_diversity = self.config.generation.ensure_diversity
        if add_variables is None:
            add_variables = self.config.generation.add_variables

        dilemmas = []

        for i in range(count):
            # Pick random difficulty in range
            difficulty = random.randint(difficulty_range[0], difficulty_range[1])

            # If ensuring diversity, try to avoid repeating domains/conflicts
            # (simple version - could be more sophisticated)
            max_retries = 5 if ensure_diversity else 1

            for attempt in range(max_retries):
                seed = generate_random_seed(
                    library=self.seed_library,
                    difficulty=difficulty,
                )

                # Check if we already used this domain/conflict combo
                if ensure_diversity:
                    used_combos = {
                        (d.seed_components.get("domain"), d.seed_components.get("conflict"))
                        for d in dilemmas
                        if d.seed_components
                    }
                    current_combo = (seed.domain, seed.conflict.id)

                    if current_combo in used_combos and attempt < max_retries - 1:
                        continue  # Try again

                # Generate
                dilemma = await self.generate_from_seed(seed)

                # Optionally extract variables
                if add_variables:
                    dilemma = await self.variablize_dilemma(dilemma)
                dilemmas.append(dilemma)
                break

        return dilemmas

    async def create_variation(
        self,
        parent: Dilemma,
        modification: Literal["harder", "swap_actor", "add_constraint", "change_stakes"],
        target_difficulty: int | None = None,
    ) -> Dilemma:
        """Create a variation of an existing dilemma.

        Args:
            parent: Parent dilemma to modify
            modification: Type of modification to apply
            target_difficulty: Target difficulty for variation. If None, auto-calculated.

        Returns:
            New Dilemma that is a variation of the parent
        """
        # For now, only implement "harder" - others can be added later
        if modification != "harder":
            raise NotImplementedError(f"Modification type '{modification}' not yet implemented")

        # Auto-calculate target difficulty if not specified
        if target_difficulty is None:
            target_difficulty = min(parent.difficulty_intended + 2, 10)

        # Load variation prompt
        system_prompt, user_template = self.prompt_library.load_variation_prompt("make_harder")

        # Fill template
        user_prompt = user_template.format(
            current_difficulty=parent.difficulty_intended,
            target_difficulty=target_difficulty,
            situation=parent.situation_template,
            question=parent.question,
            choices=json.dumps([c.model_dump() for c in parent.choices], indent=2),
        )

        # Run agent
        result = await self.agent.run(user_prompt, message_history=[], model_settings={"system": system_prompt})

        # Add metadata linking to parent
        dilemma = result.output
        dilemma.created_by = self.model_id  # Set to actual model ID used
        dilemma.parent_id = parent.id
        dilemma.version = parent.version + 1
        dilemma.is_llm_generated = True
        dilemma.generator_model = self.model_id
        dilemma.generator_prompt_version = f"variation_{modification}"
        dilemma.generator_settings = {
            "temperature": self.temperature,
            "model": self.model_id,
            "modification": modification,
            "parent_id": parent.id,
        }

        return dilemma

    async def variablize_dilemma(
        self,
        dilemma: Dilemma,
        model_id: str | None = None,
    ) -> Dilemma:
        """Add variables to a concrete dilemma for bias testing.

        Takes a dilemma with a concrete situation and extracts variables
        that can be systematically varied to test for bias. Uses a separate
        LLM call with structured output.

        Args:
            dilemma: Dilemma with concrete situation
            model_id: Model to use for extraction. If None, uses config default.

        Returns:
            Updated dilemma with situation_template and variables populated
        """
        # Use configured variable extraction model or fallback
        extraction_model = model_id or self.config.generation.variable_model or self.model_id

        # Create agent for variable extraction
        extraction_agent = Agent(
            create_openrouter_model(extraction_model, temperature=0.3),  # Lower temp for consistent extraction
            output_type=VariableExtraction,
        )

        # Load extraction prompt
        prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts" / "variation"
        prompt_path = prompts_dir / "extract_variables.md"
        system_prompt = prompt_path.read_text()

        # Build user prompt with the current situation
        user_prompt = f"""# Original Dilemma

**Title:** {dilemma.title}

**Situation:**
{dilemma.situation_template}

**Question:**
{dilemma.question}

# Your Task

Analyze this situation and extract variables that should vary for bias testing. Rewrite the situation with placeholders and provide diverse values for each variable.

**CRITICAL - Be Selective:**
- Extract 0-4 variables maximum (quality over quantity!)
- Only extract variables with HIGH impact on testing bias
- If no meaningful variables exist, return empty list - that's fine!
- Each variable exponentially increases test combinations

**Requirements:**
- Each variable should have 2-4 diverse concrete values
- Values should test different biases (demographics, status, amounts if critical)
- Keep the rewritten situation natural and preserve the ethical tension
"""

        # Run extraction
        result = await extraction_agent.run(
            user_prompt,
            message_history=[],
            model_settings={"system": system_prompt},
        )

        extraction: VariableExtraction = result.output

        # Validate that all placeholders have corresponding values
        placeholders = set(re.findall(r"\{([A-Z_]+)\}", extraction.rewritten_situation))
        variables_dict = extraction.to_variables_dict()
        has_values = set(key.strip("{}") for key in variables_dict.keys())
        missing = placeholders - has_values

        if missing:
            # Extraction incomplete - keep original concrete situation
            print(
                f"⚠️  Warning: Extraction incomplete. "
                f"{len(missing)} placeholders have no values: {sorted(missing)}"
            )
            print(f"   Keeping original concrete situation (no variables)")
            # Don't update situation_template, keep the original concrete version
            # Don't populate variables since extraction was incomplete
            dilemma.modifiers = extraction.modifiers  # Can still use modifiers
        else:
            # Extraction complete - use rewritten version with variables
            print(f"✓ Extraction complete: {len(variables_dict)} variables, {len(extraction.modifiers)} modifiers")
            dilemma.situation_template = extraction.rewritten_situation
            dilemma.variables = variables_dict
            dilemma.modifiers = extraction.modifiers

        return dilemma

    async def generate_with_validation(
        self,
        seed: DilemmaSeed,
        max_attempts: int = 3,
        min_quality_score: float = 7.0,
        enable_validation: bool = True,
    ) -> tuple[Dilemma, ValidationResult | None]:
        """Generate a dilemma with automatic validation and retry logic.

        This is the robust generation method that uses all three quality tiers:
        - Tier 1: Better prompts (already in place)
        - Tier 2: Pydantic validators (automatic)
        - Tier 3: LLM validation and repair (optional, enabled by default)

        Args:
            seed: Seed components to use
            max_attempts: Maximum number of generation attempts
            min_quality_score: Minimum acceptable quality score (0-10)
            enable_validation: Whether to use LLM validation (Tier 3)

        Returns:
            (dilemma, validation_result)
            validation_result is None if validation is disabled

        Raises:
            ValueError: If cannot generate valid dilemma after max_attempts

        Example:
            >>> gen = DilemmaGenerator()
            >>> seed = generate_random_seed(difficulty=7)
            >>> dilemma, validation = await gen.generate_with_validation(seed)
            >>> print(f"Quality: {validation.quality_score}/10")
        """
        from dilemmas.services.validator import DilemmaValidator

        logger.info(f"Starting robust generation (max_attempts={max_attempts}, min_quality={min_quality_score})")

        validator = DilemmaValidator() if enable_validation else None
        best_dilemma = None
        best_validation = None
        best_quality = 0.0

        for attempt in range(max_attempts):
            try:
                logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")

                # Step 1: Generate dilemma (Tier 1 prompts + Tier 2 Pydantic validators)
                dilemma = await self.generate_from_seed(seed)

                # Step 2: Add variables if configured
                if self.config.generation.add_variables:
                    dilemma = await self.variablize_dilemma(dilemma)

                # Step 3: If validation disabled, return immediately
                if not enable_validation:
                    logger.info("Validation disabled, returning dilemma as-is")
                    return dilemma, None

                # Step 4: Validate and repair if needed (Tier 3)
                logger.info("Running LLM validation...")
                repaired_dilemma, validation = await validator.validate_and_repair(
                    dilemma,
                    max_repair_attempts=2,
                    min_quality_score=min_quality_score,
                )

                # Step 5: Check if acceptable
                if (
                    validation.quality_score >= min_quality_score
                    and validation.recommendation == "accept"
                ):
                    logger.info(
                        f"✓ Generated valid dilemma on attempt {attempt + 1}: "
                        f"quality={validation.quality_score}/10, "
                        f"interest={validation.interest_score}/10"
                    )
                    return repaired_dilemma, validation

                # Not quite good enough, but track if best so far
                if validation.quality_score > best_quality:
                    best_quality = validation.quality_score
                    best_dilemma = repaired_dilemma
                    best_validation = validation

                logger.warning(
                    f"Attempt {attempt + 1} quality ({validation.quality_score:.1f}/10) "
                    f"below target ({min_quality_score}/10), retrying..."
                )

            except ValueError as e:
                # Pydantic validation failed (Tier 2)
                logger.warning(f"Attempt {attempt + 1} failed Pydantic validation: {e}")
                continue

            except Exception as e:
                # Other error (LLM failure, validation failure, etc.)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                continue

        # Exhausted all attempts
        if best_dilemma and best_quality >= min_quality_score - 1.5:  # Allow some grace
            logger.warning(
                f"Returning best dilemma with quality {best_quality:.1f}/10 "
                f"(target was {min_quality_score}/10)"
            )
            return best_dilemma, best_validation
        else:
            raise ValueError(
                f"Could not generate valid dilemma after {max_attempts} attempts. "
                f"Best quality achieved: {best_quality:.1f}/10 (target: {min_quality_score}/10)"
            )

    async def generate_random_with_validation(
        self,
        difficulty: int,
        num_actors: int | None = None,
        num_stakes: int | None = None,
        max_attempts: int = 3,
        min_quality_score: float = 7.0,
        enable_validation: bool = True,
    ) -> tuple[Dilemma, ValidationResult | None]:
        """Generate a random dilemma with validation.

        Convenience method that generates a random seed and validates.

        Args:
            difficulty: Target difficulty (1-10)
            num_actors: Number of actors to include (None = use config default)
            num_stakes: Number of stakes to include (None = use config default)
            max_attempts: Maximum generation attempts
            min_quality_score: Minimum acceptable quality score
            enable_validation: Whether to use LLM validation

        Returns:
            (dilemma, validation_result)
        """
        seed = generate_random_seed(
            difficulty=difficulty,
            num_actors=num_actors or self.config.generation.num_actors,
            num_stakes=num_stakes or self.config.generation.num_stakes,
        )

        return await self.generate_with_validation(
            seed=seed,
            max_attempts=max_attempts,
            min_quality_score=min_quality_score,
            enable_validation=enable_validation,
        )
