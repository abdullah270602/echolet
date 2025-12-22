"""create agent_configs table

Revision ID: a1b2c3d4e5f6
Revises: e732e7445193
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e732e7445193'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('agent_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('voice_id', sa.String(length=50), nullable=False),
        sa.Column('greeting_message', sa.Text(), nullable=False),
        sa.Column('tone', sa.String(length=20), nullable=False),
        sa.Column('custom_instructions', sa.Text(), nullable=True),
        sa.Column('knowledge_base_text', sa.Text(), nullable=True),
        sa.Column('max_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_configs_user_id', 'agent_configs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_agent_configs_user_id', table_name='agent_configs')
    op.drop_table('agent_configs')
