import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import DAILY_TALK_LIMIT_SECONDS
from app.db.repos import usage_repo


async def check_user_limit(session: AsyncSession, user_id: uuid.UUID) -> dict:
    """
    Check if user has remaining talk time for today.

    Args:
        session: Database session
        user_id: The user's identifier

    Returns:
        dict with:
        - allowed: bool - whether user can start a session
        - remaining_seconds: int - seconds remaining today
        - used_seconds: int - seconds already used today
        - limit_seconds: int - total daily limit
    """
    used_seconds = await usage_repo.get_daily_usage(session, user_id)
    remaining_seconds = max(0, DAILY_TALK_LIMIT_SECONDS - used_seconds)

    return {
        "allowed": remaining_seconds > 0,
        "remaining_seconds": remaining_seconds,
        "used_seconds": used_seconds,
        "limit_seconds": DAILY_TALK_LIMIT_SECONDS,
    }


async def record_usage(session: AsyncSession, user_id: uuid.UUID, seconds: int) -> dict:
    """
    Record talk time usage for a user.

    Args:
        session: Database session
        user_id: The user's identifier
        seconds: Number of seconds to record

    Returns:
        dict with updated usage status
    """
    new_total = await usage_repo.increment_usage(session, user_id, seconds)
    remaining_seconds = max(0, DAILY_TALK_LIMIT_SECONDS - new_total)

    return {
        "remaining_seconds": remaining_seconds,
        "used_seconds": new_total,
        "limit_seconds": DAILY_TALK_LIMIT_SECONDS,
    }
