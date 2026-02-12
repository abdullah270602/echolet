"""replace_agent_columns_with_config_jsonb

Replace individual agent config columns with a single JSONB config column.
This is a clean break - existing agent data will be lost.

Columns removed: name, business_name, voice_id, greeting_message, tone,
                 custom_instructions, knowledge_base_text
Columns added: config (JSONB)
Columns kept: id, user_id, status, phone, created_at, updated_at, deleted_at

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2025-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, Sequence[str], None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace individual columns with JSONB config column."""
    # Add the new config JSONB column
    op.add_column(
        'agent_configs',
        sa.Column('config', JSONB, nullable=False, server_default='{}')
    )

    # Drop the old columns (clean break, no data migration)
    op.drop_column('agent_configs', 'name')
    op.drop_column('agent_configs', 'business_name')
    op.drop_column('agent_configs', 'voice_id')
    op.drop_column('agent_configs', 'greeting_message')
    op.drop_column('agent_configs', 'tone')
    op.drop_column('agent_configs', 'custom_instructions')
    op.drop_column('agent_configs', 'knowledge_base_text')


def downgrade() -> None:
    """Restore individual columns and remove JSONB config column."""
    # Re-add the old columns
    op.add_column(
        'agent_configs',
        sa.Column('name', sa.String(255), nullable=False, server_default='Agent')
    )
    op.add_column(
        'agent_configs',
        sa.Column('business_name', sa.String(255), nullable=False, server_default='Business')
    )
    op.add_column(
        'agent_configs',
        sa.Column('voice_id', sa.String(50), nullable=False, server_default='Ashley')
    )
    op.add_column(
        'agent_configs',
        sa.Column('greeting_message', sa.Text(), nullable=False, server_default='Hello! How can I help you today?')
    )
    op.add_column(
        'agent_configs',
        sa.Column('tone', sa.String(20), nullable=False, server_default='professional')
    )
    op.add_column(
        'agent_configs',
        sa.Column('custom_instructions', sa.Text(), nullable=True)
    )
    op.add_column(
        'agent_configs',
        sa.Column('knowledge_base_text', sa.Text(), nullable=True)
    )

    # Drop the config column
    op.drop_column('agent_configs', 'config')
