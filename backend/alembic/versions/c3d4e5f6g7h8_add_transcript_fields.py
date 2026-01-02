"""add_transcript_fields

Revision ID: c3d4e5f6g7h8
Revises: 8bdaee2cadd2
Create Date: 2025-12-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = '8bdaee2cadd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transcript, summary, and priority columns to call_sessions."""
    # Add transcript column (JSONB for storing conversation messages)
    op.add_column(
        'call_sessions',
        sa.Column('transcript', JSONB, nullable=True)
    )

    # Add summary column (AI-generated summary, initially "Pending")
    op.add_column(
        'call_sessions',
        sa.Column('summary', sa.String(1000), nullable=True)
    )

    # Add priority column with default value
    op.add_column(
        'call_sessions',
        sa.Column('priority', sa.String(20), nullable=False, server_default='normal')
    )


def downgrade() -> None:
    """Remove transcript, summary, and priority columns from call_sessions."""
    op.drop_column('call_sessions', 'priority')
    op.drop_column('call_sessions', 'summary')
    op.drop_column('call_sessions', 'transcript')
