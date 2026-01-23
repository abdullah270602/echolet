import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, Index, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentConfig(Base):
    """Model for storing user agent configurations."""

    __tablename__ = "agent_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(50), nullable=False, default="Ashley")
    greeting_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Hello! How can I help you today?",
    )

    # Behavior
    tone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="professional",
    )  # professional, friendly, urgent
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Knowledge
    knowledge_base_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Limits
    max_duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=600,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="inactive",
    )  # active, inactive, paused
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (Index("ix_agent_configs_user_id", "user_id"),)

    def __repr__(self) -> str:
        return (
            f"<AgentConfig(id={self.id}, user_id={self.user_id}, "
            f"name={self.name}, status={self.status})>"
        )
