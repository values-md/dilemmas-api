"""Database models using SQLModel.

Design Approach
---------------

We use a JSON hybrid approach:
- Store complex nested objects (Dilemma, Judgement) as JSON
- Index key fields for querying (id, tags, difficulty, etc.)
- Keep our Pydantic models for validation and business logic
- Database models are thin persistence layer

This approach gives us:
- Full Pydantic validation on our domain models
- Easy querying/filtering on indexed fields
- Simple database schema
- Easy migration from SQLite → Postgres → D1

The pattern:
1. Domain model (Dilemma) - rich Pydantic model with validation
2. DB model (DilemmaDB) - thin SQLModel with JSON storage
3. Conversion methods: to_domain() and from_domain()
"""

import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Column, Field, SQLModel
from sqlalchemy import JSON, String, Text

from dilemmas.models.dilemma import Dilemma
from dilemmas.models.judgement import Judgement


class DilemmaDB(SQLModel, table=True):
    """Database model for storing Dilemma records.

    Stores the full Dilemma as JSON while indexing key fields for querying.
    """

    __tablename__ = "dilemmas"

    # Primary key and core fields
    id: str = Field(primary_key=True, description="Unique dilemma identifier")

    # Full dilemma data as JSON
    data: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Complete Dilemma model as JSON string"
    )

    # Indexed fields for querying (extracted from data)
    title: str = Field(index=True, description="Dilemma title")
    difficulty_intended: int = Field(index=True, description="Intended difficulty 1-10")
    created_by: str = Field(index=True, description="Creator (human or model ID)")
    created_at: datetime = Field(index=True, description="Creation timestamp")

    # Searchable fields
    tags_json: str = Field(
        sa_column=Column(Text, nullable=False, default="[]"),
        description="Tags as JSON array for querying"
    )
    version: int = Field(default=1, description="Version number")
    parent_id: str | None = Field(default=None, index=True, description="Parent dilemma ID if variation")

    # Collection & Batch (for organizing dilemmas into test sets)
    collection: str | None = Field(default=None, index=True, description="Collection/battery name")
    batch_id: str | None = Field(default=None, index=True, description="Batch generation run ID")

    @classmethod
    def from_domain(cls, dilemma: Dilemma) -> "DilemmaDB":
        """Convert domain Dilemma model to database model.

        Args:
            dilemma: Domain Dilemma instance

        Returns:
            DilemmaDB instance ready to save
        """
        # Normalize datetime to naive UTC for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
        created_at = dilemma.created_at
        if created_at.tzinfo is not None:
            # Convert to UTC and remove timezone info
            created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)

        return cls(
            id=dilemma.id,
            data=dilemma.model_dump_json(),
            title=dilemma.title,
            difficulty_intended=dilemma.difficulty_intended,
            created_by=dilemma.created_by,
            created_at=created_at,
            tags_json=json.dumps(dilemma.tags),
            version=dilemma.version,
            parent_id=dilemma.parent_id,
            collection=dilemma.collection,
            batch_id=dilemma.batch_id,
        )

    def to_domain(self) -> Dilemma:
        """Convert database model to domain Dilemma model.

        Returns:
            Validated Dilemma instance
        """
        return Dilemma.model_validate_json(self.data)

    @property
    def tags(self) -> list[str]:
        """Get tags as list."""
        return json.loads(self.tags_json)


class JudgementDB(SQLModel, table=True):
    """Database model for storing Judgement/decision records (human and AI).

    Stores the full Judgement as JSON while indexing key fields for querying.
    Supports both human and AI judges through the judge_type discriminator.
    """

    __tablename__ = "judgements"

    # Primary key
    id: str = Field(primary_key=True, description="Unique judgement identifier")

    # Foreign key
    dilemma_id: str = Field(index=True, description="Which dilemma was judged")

    # Full judgement data as JSON
    data: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Complete Judgement model as JSON string"
    )

    # Judge identification (indexed for querying)
    judge_type: str = Field(index=True, description="human or ai")
    judge_id: str = Field(
        index=True,
        description="Judge identifier (model_id for AI, participant_id for human)"
    )

    # Presentation & decision (indexed for querying)
    mode: str = Field(index=True, description="theory or action")
    choice_id: str | None = Field(index=False, description="Which choice was selected")
    created_at: datetime = Field(index=True, description="When judgement was made")

    # Experimental conditions (for filtering results)
    variation_key: str | None = Field(
        index=True,
        description="Hash/key identifying which variation (variables + modifiers) was used"
    )
    experiment_id: str | None = Field(
        index=True,
        description="Experiment run ID for batch experiments"
    )
    repetition_number: int | None = Field(
        default=None,
        index=True,
        description="If same config repeated multiple times, which repetition (1-based)"
    )

    # AI-specific (nullable for human judges)
    temperature: float | None = Field(
        default=None,
        index=True,
        description="Model temperature (AI only)"
    )

    system_prompt_type: str | None = Field(
        default=None,
        index=True,
        description="Type of system prompt: none, default, custom_values, other (AI only)"
    )

    values_file_name: str | None = Field(
        default=None,
        index=True,
        description="Name of VALUES.md file if system_prompt_type='custom_values' (AI only)"
    )

    @classmethod
    def from_domain(cls, judgement: Judgement) -> "JudgementDB":
        """Convert domain Judgement model to database model.

        Args:
            judgement: Domain Judgement instance

        Returns:
            JudgementDB instance ready to save
        """
        # Normalize datetime to naive UTC for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
        created_at = judgement.created_at
        if created_at.tzinfo is not None:
            # Convert to UTC and remove timezone info
            created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)

        return cls(
            id=judgement.id,
            data=judgement.model_dump_json(),
            dilemma_id=judgement.dilemma_id,
            judge_type=judgement.judge_type,
            judge_id=judgement.get_judge_id(),
            mode=judgement.mode,
            choice_id=judgement.choice_id,
            created_at=created_at,
            variation_key=judgement.variation_key,
            experiment_id=judgement.experiment_id,
            repetition_number=judgement.repetition_number,
            temperature=(
                judgement.ai_judge.temperature
                if judgement.judge_type == "ai" and judgement.ai_judge
                else None
            ),
            system_prompt_type=(
                judgement.ai_judge.system_prompt_type
                if judgement.judge_type == "ai" and judgement.ai_judge
                else None
            ),
            values_file_name=(
                judgement.ai_judge.values_file_name
                if judgement.judge_type == "ai" and judgement.ai_judge
                else None
            ),
        )

    def to_domain(self) -> Judgement:
        """Convert database model to domain Judgement model.

        Returns:
            Validated Judgement instance
        """
        return Judgement.model_validate_json(self.data)


class ValuesMdDB(SQLModel, table=True):
    """Database model for caching generated VALUES.md files.

    Stores the complete VALUES.md markdown along with metadata.
    Cache persists forever until explicitly regenerated.
    """

    __tablename__ = "values_md"

    # Primary key
    participant_id: str = Field(primary_key=True, description="Participant identifier")

    # VALUES.md content
    markdown_text: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Complete VALUES.md file as markdown text"
    )

    # Structured data (optional, for analysis)
    structured_json: str = Field(
        sa_column=Column(Text, nullable=False),
        description="ValuesMarkdown model as JSON"
    )

    # Metadata
    generated_at: datetime = Field(description="When VALUES.md was generated")
    model_id: str = Field(description="LLM model used for generation")
    judgement_count: int = Field(description="Number of judgements analyzed")

    # Update tracking
    version: int = Field(default=1, description="Version number (increments on regeneration)")


# Future: Add ExperimentRun, ResultSet, etc. as needed
