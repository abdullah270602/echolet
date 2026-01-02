from datetime import datetime
from typing import Optional, Any
import uuid

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CallSession(Base):
    """Model for tracking active voice call sessions."""

    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # UUID used as LiveKit room_name
    room_name: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )

    # Foreign keys
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Session state: pending, active, completed, failed
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Duration tracking
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Transcript - JSON array of messages
    # Format: [{"role": "user"|"agent", "content": "...", "timestamp": 1234567890}]
    transcript: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )

    # AI-generated summary (set to "Pending" initially, populated later)
    summary: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
    )

    # Priority classification: "urgent", "normal", "low"
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
    )

    __table_args__ = (
        Index("ix_call_sessions_room_name", "room_name"),
        Index("ix_call_sessions_user_id", "user_id"),
        Index("ix_call_sessions_agent_id", "agent_id"),
    )

    def __repr__(self) -> str:
        return f"<CallSession(id={self.id}, room_name={self.room_name}, status={self.status})>"
