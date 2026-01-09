"""add_missing_analysis_fields

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2025-01-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add category, urgency, and action_required columns to call_sessions."""
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
    """Remove category, urgency, and action_required columns from call_sessions."""
    op.drop_column('call_sessions', 'action_required')
    op.drop_column('call_sessions', 'urgency')
    op.drop_column('call_sessions', 'category')
