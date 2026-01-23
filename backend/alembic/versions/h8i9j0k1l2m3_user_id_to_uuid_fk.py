"""user_id_to_uuid_fk

Convert user_id from clerk_id string to internal UUID with FK constraints.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2025-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, Sequence[str], None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert user_id from clerk_id string to internal UUID with FK."""
    # 1. Add new UUID columns (nullable initially)
    op.add_column('agent_configs', sa.Column('user_uuid', UUID(as_uuid=True), nullable=True))
    op.add_column('call_sessions', sa.Column('user_uuid', UUID(as_uuid=True), nullable=True))
    op.add_column('user_daily_usage', sa.Column('user_uuid', UUID(as_uuid=True), nullable=True))

    # 2. Populate new columns from users table lookup
    op.execute("""
        UPDATE agent_configs ac
        SET user_uuid = u.id
        FROM users u
        WHERE ac.user_id = u.clerk_id
    """)
    op.execute("""
        UPDATE call_sessions cs
        SET user_uuid = u.id
        FROM users u
        WHERE cs.user_id = u.clerk_id
    """)
    op.execute("""
        UPDATE user_daily_usage udu
        SET user_uuid = u.id
        FROM users u
        WHERE udu.user_id = u.clerk_id
    """)

    # 2b. Delete orphaned records (no matching user in users table)
    # This is consistent with CASCADE delete behavior we're implementing
    op.execute("DELETE FROM agent_configs WHERE user_uuid IS NULL")
    op.execute("DELETE FROM call_sessions WHERE user_uuid IS NULL")
    op.execute("DELETE FROM user_daily_usage WHERE user_uuid IS NULL")

    # 3. Drop old indexes and constraints
    op.drop_index('ix_agent_configs_user_id', table_name='agent_configs')
    op.drop_index('ix_call_sessions_user_id', table_name='call_sessions')
    op.drop_index('idx_user_daily_usage_lookup', table_name='user_daily_usage')
    op.drop_constraint('uq_user_daily_usage_user_date', 'user_daily_usage', type_='unique')

    # 4. Drop old columns
    op.drop_column('agent_configs', 'user_id')
    op.drop_column('call_sessions', 'user_id')
    op.drop_column('user_daily_usage', 'user_id')

    # 5. Rename new columns to user_id and make non-nullable
    op.alter_column('agent_configs', 'user_uuid', new_column_name='user_id', nullable=False)
    op.alter_column('call_sessions', 'user_uuid', new_column_name='user_id', nullable=False)
    op.alter_column('user_daily_usage', 'user_uuid', new_column_name='user_id', nullable=False)

    # 6. Add FK constraints with CASCADE
    op.create_foreign_key(
        'fk_agent_configs_user_id',
        'agent_configs', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_call_sessions_user_id',
        'call_sessions', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_user_daily_usage_user_id',
        'user_daily_usage', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    # 7. Recreate indexes
    op.create_index('ix_agent_configs_user_id', 'agent_configs', ['user_id'])
    op.create_index('ix_call_sessions_user_id', 'call_sessions', ['user_id'])
    op.create_index('idx_user_daily_usage_lookup', 'user_daily_usage', ['user_id', 'usage_date'])
    op.create_unique_constraint(
        'uq_user_daily_usage_user_date',
        'user_daily_usage',
        ['user_id', 'usage_date']
    )


def downgrade() -> None:
    """Revert user_id back to clerk_id string."""
    # 1. Drop FK constraints
    op.drop_constraint('fk_agent_configs_user_id', 'agent_configs', type_='foreignkey')
    op.drop_constraint('fk_call_sessions_user_id', 'call_sessions', type_='foreignkey')
    op.drop_constraint('fk_user_daily_usage_user_id', 'user_daily_usage', type_='foreignkey')

    # 2. Drop indexes and constraints
    op.drop_index('ix_agent_configs_user_id', table_name='agent_configs')
    op.drop_index('ix_call_sessions_user_id', table_name='call_sessions')
    op.drop_index('idx_user_daily_usage_lookup', table_name='user_daily_usage')
    op.drop_constraint('uq_user_daily_usage_user_date', 'user_daily_usage', type_='unique')

    # 3. Add new string columns
    op.add_column('agent_configs', sa.Column('user_clerk_id', sa.String(255), nullable=True))
    op.add_column('call_sessions', sa.Column('user_clerk_id', sa.String(255), nullable=True))
    op.add_column('user_daily_usage', sa.Column('user_clerk_id', sa.String(255), nullable=True))

    # 4. Populate from users table
    op.execute("""
        UPDATE agent_configs ac
        SET user_clerk_id = u.clerk_id
        FROM users u
        WHERE ac.user_id = u.id
    """)
    op.execute("""
        UPDATE call_sessions cs
        SET user_clerk_id = u.clerk_id
        FROM users u
        WHERE cs.user_id = u.id
    """)
    op.execute("""
        UPDATE user_daily_usage udu
        SET user_clerk_id = u.clerk_id
        FROM users u
        WHERE udu.user_id = u.id
    """)

    # 5. Drop UUID columns
    op.drop_column('agent_configs', 'user_id')
    op.drop_column('call_sessions', 'user_id')
    op.drop_column('user_daily_usage', 'user_id')

    # 6. Rename to user_id
    op.alter_column('agent_configs', 'user_clerk_id', new_column_name='user_id', nullable=False)
    op.alter_column('call_sessions', 'user_clerk_id', new_column_name='user_id', nullable=False)
    op.alter_column('user_daily_usage', 'user_clerk_id', new_column_name='user_id', nullable=False)

    # 7. Recreate original indexes
    op.create_index('ix_agent_configs_user_id', 'agent_configs', ['user_id'])
    op.create_index('ix_call_sessions_user_id', 'call_sessions', ['user_id'])
    op.create_index('idx_user_daily_usage_lookup', 'user_daily_usage', ['user_id', 'usage_date'])
    op.create_unique_constraint(
        'uq_user_daily_usage_user_date',
        'user_daily_usage',
        ['user_id', 'usage_date']
    )
