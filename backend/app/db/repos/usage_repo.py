import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
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


async def increment_usage(
    session: AsyncSession,
    user_id: uuid.UUID,
    seconds: int,
    usage_date: date | None = None,
) -> int:
    """
    Add seconds to user's daily usage. Creates record if doesn't exist.
    Uses PostgreSQL UPSERT for atomicity.

    Args:
        session: Database session
        user_id: The user's identifier
        seconds: Number of seconds to add
        usage_date: The date to record (defaults to today UTC)

    Returns:
        The new total seconds used
    """
    if usage_date is None:
        usage_date = datetime.now(timezone.utc).date()

    # PostgreSQL INSERT ... ON CONFLICT (UPSERT)
    stmt = insert(UserDailyUsage).values(
        user_id=user_id,
        usage_date=usage_date,
        talk_seconds_used=seconds,
    )

    # On conflict, add to existing value
    # Use naive UTC datetime to match TIMESTAMP WITHOUT TIME ZONE column
    stmt = stmt.on_conflict_do_update(
        constraint="uq_user_daily_usage_user_date",
        set_={
            "talk_seconds_used": UserDailyUsage.talk_seconds_used + seconds,
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
        },
    ).returning(UserDailyUsage.talk_seconds_used)

    result = await session.execute(stmt)
    new_total = result.scalar_one()

    return new_total
