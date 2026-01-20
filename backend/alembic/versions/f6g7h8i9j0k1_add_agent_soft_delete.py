"""add_agent_soft_delete

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, Sequence[str], None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deleted_at column to agent_configs for soft delete."""
    op.add_column(
        'agent_configs',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'ix_agent_configs_deleted_at',
        'agent_configs',
        ['deleted_at']
    )


def downgrade() -> None:
    """Remove deleted_at column from agent_configs."""
    op.drop_index('ix_agent_configs_deleted_at', 'agent_configs')
    op.drop_column('agent_configs', 'deleted_at')
