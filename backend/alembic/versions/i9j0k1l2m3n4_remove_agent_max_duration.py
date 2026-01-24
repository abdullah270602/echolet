"""remove_agent_max_duration

Remove max_duration_seconds from agent_configs.
Usage limits are now handled globally at the user level.

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2025-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, Sequence[str], None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove max_duration_seconds column from agent_configs."""
    op.drop_column('agent_configs', 'max_duration_seconds')


def downgrade() -> None:
    """Re-add max_duration_seconds column to agent_configs."""
    op.add_column(
        'agent_configs',
        sa.Column(
            'max_duration_seconds',
            sa.Integer(),
            nullable=False,
            server_default='600'
        )
    )
