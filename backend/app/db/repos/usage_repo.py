import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.usage import UserDailyUsage


async def get_daily_usage(
    session: AsyncSession,
    user_id: uuid.UUID,
    usage_date: date | None = None,
) -> int:
    """
    Get total seconds used by user for a given date (defaults to today UTC).

    Args:
        session: Database session
        user_id: The user's identifier
        usage_date: The date to check (defaults to today UTC)

    Returns:
        Total seconds used, or 0 if no record exists
    """
    if usage_date is None:
        usage_date = datetime.now(timezone.utc).date()

    stmt = select(UserDailyUsage.talk_seconds_used).where(
        UserDailyUsage.user_id == user_id,
        UserDailyUsage.usage_date == usage_date,
    )

    result = await session.execute(stmt)
    row = result.scalar_one_or_none()

    return row if row is not None else 0


