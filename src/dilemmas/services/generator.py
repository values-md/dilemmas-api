"""Dilemma generation service using seed-based approach with LLMs."""

import json
import logging
import random
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry

from dilemmas.llm.openrouter import create_openrouter_model
from dilemmas.models.config import get_config
from dilemmas.models.dilemma import Dilemma
from dilemmas.models.extraction import VariableExtraction
from dilemmas.models.validation import ValidationResult
from dilemmas.services.prompts import get_prompt_library
from dilemmas.services.seeds import DilemmaSeed, generate_random_seed, get_seed_library
from dilemmas.services.institution_classifier import classify_institution

logger = logging.getLogger(__name__)


class ChoiceToolPair(BaseModel):
    """A single choice-to-tool mapping."""

    choice_id: str = Field(..., description="The choice ID (e.g., 'notify', 'wait')")
    tool_name: str = Field(..., description="The tool name this choice should call")


class ToolMapping(BaseModel):
    """Mapping from choice IDs to tool names."""

    mappings: list[ChoiceToolPair] = Field(
        ...,
        description="List of choice-to-tool mappings. Each choice must map to exactly one tool.",
    )


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
            output_retries=3,  # Allow up to 3 retries for output validation
        )

        # Add output validator to catch corrupted output
        @self.agent.output_validator
        async def validate_no_corruption(ctx, dilemma: Dilemma) -> Dilemma:
            """Validate that the dilemma doesn't have corrupted fields."""
            from pydantic_ai.exceptions import ModelRetry

            # Check for XML/template corruption in title
            if '<' in dilemma.title or '>' in dilemma.title or '</parameter' in dilemma.title:
                raise ModelRetry(
                    "Title contains XML/template tags. Generate clean text only, no XML formatting. "
                    f"Current title: {dilemma.title[:100]}"
                )

            # Check that title is reasonable length
            if len(dilemma.title) > 200:
                raise ModelRetry(
                    f"Title is too long ({len(dilemma.title)} chars). Keep it concise (max 200 chars). "
                    f"Current title: {dilemma.title[:100]}..."
                )

            # Check that situation_template is not empty
            if not dilemma.situation_template or len(dilemma.situation_template) < 100:
                raise ModelRetry(
                    f"Situation is too short ({len(dilemma.situation_template)} chars). "
                    "Provide a detailed concrete scenario (at least 100 chars)."
                )

            return dilemma

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

        # Validate and auto-fix tool mapping if tools are present
        if dilemma.available_tools:
            try:
                self._validate_tool_mapping(dilemma)
            except ValueError as e:
                logger.warning(f"Tool mapping validation failed: {e}. Auto-fixing...")
                await self._fix_tool_mapping(dilemma)
                # Re-validate after fix
                self._validate_tool_mapping(dilemma)
                logger.info("Tool mapping fixed successfully")

        # Classify institution type from action_context
        if not dilemma.institution_type:
            dilemma.institution_type = await classify_institution(dilemma.action_context)

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
        failed_count = 0

        for i in range(count):
            # Pick random difficulty in range
            difficulty = random.randint(difficulty_range[0], difficulty_range[1])

            # If ensuring diversity, try to avoid repeating domains/conflicts
            # (simple version - could be more sophisticated)
            max_retries = 5 if ensure_diversity else 1

            dilemma_generated = False

            for attempt in range(max_retries):
                try:
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
                    dilemma_generated = True
                    break

                except Exception as e:
                    # Log the error but continue trying
                    if attempt == max_retries - 1:
                        # All retries exhausted - skip this dilemma
                        print(f"⚠️  Failed to generate dilemma {i+1}/{count} after {max_retries} attempts: {str(e)[:100]}")
                        failed_count += 1
                    continue

        # Print summary if any failures
        if failed_count > 0:
            print(f"\n⚠️  {failed_count}/{count} dilemmas failed to generate")
            print(f"✓  Successfully generated {len(dilemmas)}/{count} dilemmas")

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

        # Create agent for variable extraction with output validator
        extraction_agent = Agent(
            create_openrouter_model(extraction_model, temperature=0.3),  # Lower temp for consistent extraction
            output_type=VariableExtraction,
            output_retries=3,  # Allow up to 3 retries for output validation (placeholder consistency)
        )

        # Add output validator to ensure placeholder consistency
        @extraction_agent.output_validator
        async def validate_placeholder_consistency(ctx, output: VariableExtraction) -> VariableExtraction:
            """Validate that all placeholders in rewritten_situation have corresponding variable values."""
            # Extract placeholders from rewritten situation
            placeholders = set(re.findall(r"\{([A-Z_]+)\}", output.rewritten_situation))

            # Get variable names from the list
            variable_names = {var.name for var in output.variables}

            # Check for mismatches
            missing = placeholders - variable_names
            extra = variable_names - placeholders

            if missing or extra:
                error_msg = ["Placeholder mismatch detected:"]
                if missing:
                    error_msg.append(f"- Placeholders in text without variables: {sorted(missing)}")
                if extra:
                    error_msg.append(f"- Variables without placeholders in text: {sorted(extra)}")
                error_msg.append("\nRemember:")
                error_msg.append("1. Decide which variables to extract (max 4)")
                error_msg.append("2. Rewrite using ONLY those placeholders")
                error_msg.append("3. Provide 2-4 values for each variable")
                error_msg.append("\nEvery {PLACEHOLDER} in the text must have a matching variable entry!")

                raise ModelRetry("\n".join(error_msg))

            # Also validate that each variable has at least 2 values
            insufficient = [var.name for var in output.variables if len(var.values) < 2]
            if insufficient:
                raise ModelRetry(
                    f"Variables with insufficient values (<2): {insufficient}\n"
                    f"Each variable must have 2-4 diverse concrete values for bias testing."
                )

            return output

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

        # DEBUG: Log what we got
        print(f"\n[DEBUG] Extraction result:")
        print(f"  - Variables returned: {len(extraction.variables)}")
        for var in extraction.variables:
            print(f"    - {var.name}: {len(var.values)} values")
            if not var.values:
                print(f"      ⚠️  EMPTY VALUES ARRAY!")
        print(f"  - Modifiers: {len(extraction.modifiers)}")
        print()

        # Filter out variables with empty or insufficient values
        valid_variables = [
            var for var in extraction.variables
            if var.values and len(var.values) >= 2
        ]

        # Rebuild variables dict with only valid ones
        variables_dict = {f"{{{var.name}}}": var.values for var in valid_variables}

        # Validate that all placeholders have corresponding values
        placeholders = set(re.findall(r"\{([A-Z_]+)\}", extraction.rewritten_situation))
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

    def _validate_tool_mapping(self, dilemma: Dilemma) -> None:
        """Validate that tool mappings are correct.

        Raises:
            ValueError: If validation fails
        """
        if not dilemma.available_tools:
            return

        # Check 1: Number of tools should match number of choices
        num_tools = len(dilemma.available_tools)
        num_choices = len(dilemma.choices)
        if num_tools != num_choices:
            raise ValueError(
                f"Tool count mismatch: {num_tools} tools but {num_choices} choices. "
                f"Each choice should map to exactly one tool."
            )

        # Check 2: All choices should have tool_name set
        unmapped_choices = [c.id for c in dilemma.choices if not c.tool_name]
        if unmapped_choices:
            raise ValueError(
                f"Choices missing tool_name: {unmapped_choices}. "
                f"Each choice must have tool_name field set."
            )

        # Check 3: All tool_names should reference valid tools
        tool_names = {t.name for t in dilemma.available_tools}
        invalid_mappings = [
            (c.id, c.tool_name)
            for c in dilemma.choices
            if c.tool_name and c.tool_name not in tool_names
        ]
        if invalid_mappings:
            raise ValueError(
                f"Invalid tool mappings: {invalid_mappings}. "
                f"Available tools: {sorted(tool_names)}"
            )

    async def _fix_tool_mapping(self, dilemma: Dilemma) -> None:
        """Auto-fix broken tool mappings using LLM inference.

        Args:
            dilemma: Dilemma with broken tool mappings (modified in place)
        """
        # Format choices
        choices_text = "\n".join([
            f"- **{c.id}**: {c.label} - {c.description}"
            for c in dilemma.choices
        ])

        # Format tools
        tools_text = "\n".join([
            f"- **{t.name}**: {t.description}"
            for t in dilemma.available_tools
        ])

        prompt = f"""Map each choice to the most appropriate tool.

**Dilemma**: {dilemma.title}

**Choices** (need tool_name):
{choices_text}

**Available Tools**:
{tools_text}

---

For each choice, determine which tool would be called to execute that action.
The mapping should be semantically coherent - the tool should make sense for the choice.

Return a list of (choice_id, tool_name) tuples. Each choice must map to exactly one tool.
"""

        # Create agent for tool mapping (use fast, cheap model)
        agent = Agent(
            create_openrouter_model("openai/gpt-4.1-mini", temperature=0.3),
            output_type=ToolMapping,
        )

        result = await agent.run(prompt)
        mapping: ToolMapping = result.output

        # Apply mappings
        mapping_dict = {pair.choice_id: pair.tool_name for pair in mapping.mappings}
        for choice in dilemma.choices:
            if choice.id in mapping_dict:
                choice.tool_name = mapping_dict[choice.id]

        logger.info(f"Auto-fixed tool mapping for: {dilemma.title}")
