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

    @classmethod
    def from_domain(cls, dilemma: Dilemma) -> "DilemmaDB":
        """Convert domain Dilemma model to database model.

        Args:
            dilemma: Domain Dilemma instance

        Returns:
            DilemmaDB instance ready to save
        """
        return cls(
            id=dilemma.id,
            data=dilemma.model_dump_json(),
            title=dilemma.title,
            difficulty_intended=dilemma.difficulty_intended,
            created_by=dilemma.created_by,
            created_at=dilemma.created_at,
            tags_json=json.dumps(dilemma.tags),
            version=dilemma.version,
            parent_id=dilemma.parent_id,
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
    """Database model for storing Judgement/decision records.

    Will store LLM responses, choices, reasoning, and metadata.
    This is a placeholder - we'll define the full schema after creating the Judgement domain model.
    """

    __tablename__ = "judgements"

    # Primary key
    id: str = Field(primary_key=True, description="Unique judgement identifier")

    # Foreign keys
    dilemma_id: str = Field(index=True, description="Which dilemma was judged")
    model_id: str = Field(index=True, description="Which model made the judgement")

    # Full judgement data as JSON
    data: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Complete Judgement model as JSON string"
    )

    # Indexed fields for querying
    mode: str = Field(index=True, description="theory or action")
    choice_id: str | None = Field(index=True, description="Which choice was selected")
    created_at: datetime = Field(index=True, description="When judgement was made")

    # Experimental conditions (for filtering results)
    temperature: float = Field(index=True, description="Model temperature used")
    variation_key: str | None = Field(
        index=True,
        description="Hash/key identifying which variation (variables + modifiers) was used"
    )

    # Note: to_domain() and from_domain() will be added after we create the Judgement domain model


# Future: Add ExperimentRun, ResultSet, etc. as needed
