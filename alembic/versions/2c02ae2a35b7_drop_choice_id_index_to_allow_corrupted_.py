"""drop choice_id index to allow corrupted data migration

Revision ID: 2c02ae2a35b7
Revises: 31cf3d9c5179
Create Date: 2025-11-01 10:52:53.163092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c02ae2a35b7'
down_revision: Union[str, Sequence[str], None] = '31cf3d9c5179'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop choice_id index temporarily to allow migration of corrupted data.

    Production has corrupted choice_id values (from x-ai/grok-4) that exceed
    Postgres B-tree index size limit. We'll drop the index, migrate fixed data,
    then decide whether to recreate it.
    """
    op.drop_index('ix_judgements_choice_id', table_name='judgements', if_exists=True)


def downgrade() -> None:
    """Recreate choice_id index."""
    op.create_index('ix_judgements_choice_id', 'judgements', ['choice_id'], unique=False)
