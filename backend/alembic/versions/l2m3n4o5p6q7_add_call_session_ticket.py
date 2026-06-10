"""Add call_sessions.ticket: the agent's configured ticket fields and tags, as filled by the worker.

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "l2m3n4o5p6q7"
down_revision: Union[str, Sequence[str], None] = "k1l2m3n4o5p6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "call_sessions",
        sa.Column(
            "ticket",
            postgresql.JSONB(),
            nullable=True,
            comment="Configured ticket fields and tags as filled by the worker: {fields, tags}",
        ),
    )


def downgrade() -> None:
    op.drop_column("call_sessions", "ticket")
