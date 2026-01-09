"""add_analysis_fields

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analysis columns to call_sessions."""
    # Add sentiment column (Positive, Neutral, Frustrated, Angry)
    op.add_column(
        'call_sessions',
        sa.Column('sentiment', sa.String(20), nullable=True)
    )

    # Add action_items column (JSONB array of strings)
    op.add_column(
        'call_sessions',
        sa.Column('action_items', JSONB, nullable=True)
    )

    # Add category column (Appointment, Inquiry, Complaint, Spam, Urgent Service, Other)
    op.add_column(
        'call_sessions',
        sa.Column('category', sa.String(30), nullable=True)
    )

    # Add urgency column (High, Medium, Low)
    op.add_column(
        'call_sessions',
        sa.Column('urgency', sa.String(10), nullable=True)
    )

    # Add action_required column (boolean)
    op.add_column(
        'call_sessions',
        sa.Column('action_required', sa.Boolean(), nullable=True)
    )


def downgrade() -> None:
    """Remove analysis columns from call_sessions."""
    op.drop_column('call_sessions', 'action_required')
    op.drop_column('call_sessions', 'urgency')
    op.drop_column('call_sessions', 'category')
    op.drop_column('call_sessions', 'action_items')
    op.drop_column('call_sessions', 'sentiment')
