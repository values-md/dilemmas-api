"""Service for generating VALUES.md files from human judgements."""

from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai import Agent
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.llm.openrouter import create_openrouter_model
from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.models.judgement import Judgement
from dilemmas.models.values import ValuesMarkdown


class ValuesGenerator:
    """Generate VALUES.md files from human judgements."""

    def __init__(self):
        """Initialize the generator."""
        # Navigate from src/dilemmas/services/ -> project_root/prompts/
        self.prompt_path = (
            Path(__file__).parent.parent.parent.parent / "prompts" / "values" / "generate_values_md.md"
        )

    async def generate(
        self,
        session: AsyncSession,
        participant_id: str,
        model_id: str = "google/gemini-2.5-flash",
        temperature: float = 0.3,
    ) -> tuple[str, ValuesMarkdown]:
        """Generate VALUES.md from participant's judgements.

        Args:
            session: Database session
            participant_id: Participant identifier
            model_id: LLM model to use (default: gemini-2.5-flash)
            temperature: Generation temperature (default: 0.3 for consistency)

        Returns:
            Tuple of (markdown_text, structured_data)

        Raises:
            ValueError: If participant has fewer than 10 judgements
        """
        # Load judgements
        judgements = await self._load_judgements(session, participant_id)

        if len(judgements) < 10:
            raise ValueError(
                f"Insufficient judgements for VALUES.md generation. "
                f"Found {len(judgements)}, minimum 10 required."
            )

        # Load system prompt
        system_prompt = self.prompt_path.read_text()

        # Format judgement data
        judgement_data = await self._format_judgements(session, judgements)

        # Create agent
        model = create_openrouter_model(model_id=model_id, temperature=temperature)
        agent = Agent(model, output_type=ValuesMarkdown, system_prompt=system_prompt)

        # Generate VALUES.md
        result = await agent.run(
            f"""Analyze these ethical judgements and generate a VALUES.md file.

{judgement_data}

Extract patterns, formulate actionable decision rules, and create a framework that AI agents can use to make decisions on behalf of this person.

Remember: Be specific, provide concrete examples, and acknowledge limitations."""
        )

        # Convert to markdown
        values_md = result.output
        markdown_text = values_md.to_markdown()

        return markdown_text, values_md

    async def _load_judgements(
        self, session: AsyncSession, participant_id: str
    ) -> list[Judgement]:
        """Load all judgements for a participant.

        Args:
            session: Database session
            participant_id: Participant identifier

        Returns:
            List of judgements (domain models)
        """
        # Query for human judgements with this participant_id
        # Note: participant_id is stored in judge_id field for human judgements
        result = await session.execute(
            select(JudgementDB)
            .where(JudgementDB.judge_type == "human")
            .where(JudgementDB.judge_id == participant_id)
        )

        judgements_db = result.scalars().all()
        return [j.to_domain() for j in judgements_db]

    async def _format_judgements(
        self, session: AsyncSession, judgements: list[Judgement]
    ) -> str:
        """Format judgements for LLM analysis.

        Args:
            session: Database session
            judgements: List of judgements to format

        Returns:
            Formatted string for LLM prompt
        """
        lines = [f"# Analysis of {len(judgements)} Ethical Judgements\n"]

        # Load all unique dilemmas
        dilemma_ids = list({j.dilemma_id for j in judgements})
        result = await session.execute(select(DilemmaDB).where(DilemmaDB.id.in_(dilemma_ids)))
        dilemmas_db = result.scalars().all()
        dilemmas = {d.id: d.to_domain() for d in dilemmas_db}

        # Format each judgement
        for i, judgement in enumerate(judgements, 1):
            dilemma = dilemmas.get(judgement.dilemma_id)
            if not dilemma:
                continue

            lines.extend(
                [
                    f"## Judgement {i}: {dilemma.title}",
                    "",
                    "**Situation:**",
                    judgement.rendered_situation or dilemma.situation_template,
                    "",
                    "**Available Choices:**",
                ]
            )

            for choice in dilemma.choices:
                marker = "✓" if choice.id == judgement.choice_id else " "
                lines.append(f"[{marker}] {choice.id}: {choice.description}")

            lines.extend(["", f"**Their Choice:** {judgement.choice_id}", ""])

            if judgement.confidence:
                lines.append(f"**Confidence:** {judgement.confidence}/10\n")

            if judgement.reasoning:
                lines.extend(["**Their Reasoning:**", judgement.reasoning, ""])

            if judgement.variable_values:
                lines.extend(["**Context Variables:**"])
                for var, value in judgement.variable_values.items():
                    lines.append(f"- {var}: {value}")
                lines.append("")

            lines.append("---\n")

        return "\n".join(lines)
