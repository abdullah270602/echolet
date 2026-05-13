"""
SQLAlchemy model for agent configurations.

Uses a hybrid approach:
- Columns for relational data (user_id, status, phone, timestamps)
- Single JSONB column for all configuration data
"""
import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import String, Integer, DateTime, Index, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentConfig(Base):
    """Model for storing user agent configurations."""

    __tablename__ = "agent_configs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to users table
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status for filtering (kept as column for efficient queries)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="inactive",
    )  # active, inactive, paused

    # Phone number (may link to telephony integrations)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Single JSONB column for all configuration
    # Structure defined in app.schemas.agent.AgentConfigData
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

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
        agent_name = self.config.get("agent", {}).get("name", "Unknown") if self.config else "Unknown"
        return (
            f"<AgentConfig(id={self.id}, user_id={self.user_id}, "
            f"name={agent_name}, status={self.status})>"
        )

    @property
    def name(self) -> str:
        """Convenience accessor for agent name from config."""
        if self.config and "agent" in self.config:
            return self.config["agent"].get("name", "")
        return ""

    @property
    def business_name(self) -> str:
        """Convenience accessor for business name from config."""
        if self.config and "agent" in self.config:
            return self.config["agent"].get("business_name", "")
        return ""
