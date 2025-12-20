from app.config import DAILY_TALK_LIMIT_SECONDS
from app.db.repos import usage_repo


def check_user_limit(user_id: str) -> dict:
    """
    Check if user has remaining talk time for today.

    Returns:
        dict with:
        - allowed: bool - whether user can start a session
        - remaining_seconds: int - seconds remaining today
        - used_seconds: int - seconds already used today
        - limit_seconds: int - total daily limit
    """
    used_seconds = usage_repo.get_daily_usage(user_id)
    remaining_seconds = max(0, DAILY_TALK_LIMIT_SECONDS - used_seconds)

    return {
        "allowed": remaining_seconds > 0,
        "remaining_seconds": remaining_seconds,
        "used_seconds": used_seconds,
        "limit_seconds": DAILY_TALK_LIMIT_SECONDS,
    }


def record_usage(user_id: str, seconds: int) -> dict:
    """
    Record talk time usage for a user.

    Returns:
        dict with updated usage status
    """
    new_total = usage_repo.increment_usage(user_id, seconds)
    remaining_seconds = max(0, DAILY_TALK_LIMIT_SECONDS - new_total)

    return {
        "remaining_seconds": remaining_seconds,
        "used_seconds": new_total,
        "limit_seconds": DAILY_TALK_LIMIT_SECONDS,
    }
