from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Integer, Date, DateTime, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserDailyUsage(Base):
    """Model for tracking daily talk time usage per user."""

    __tablename__ = "user_daily_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
    )
    talk_seconds_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_user_daily_usage_user_date"),
        Index("idx_user_daily_usage_lookup", "user_id", "usage_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserDailyUsage(id={self.id}, user_id={self.user_id}, "
            f"date={self.usage_date}, seconds={self.talk_seconds_used})>"
        )
