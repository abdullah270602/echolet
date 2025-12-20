from datetime import date, datetime

from app.db import get_db


def get_daily_usage(user_id: str, usage_date: date | None = None) -> int:
    """Get total seconds used by user for a given date (defaults to today UTC)."""
    if usage_date is None:
        usage_date = datetime.utcnow().date()

    with get_db() as conn:
        result = conn.execute(
            """
            SELECT talk_seconds_used
            FROM user_daily_usage
            WHERE user_id = %s AND usage_date = %s
            """,
            (user_id, usage_date),
        ).fetchone()

    return result["talk_seconds_used"] if result else 0


def increment_usage(user_id: str, seconds: int, usage_date: date | None = None) -> int:
    """
    Add seconds to user's daily usage. Creates record if doesn't exist.
    Returns the new total seconds used.
    """
    if usage_date is None:
        usage_date = datetime.utcnow().date()

    with get_db() as conn:
        result = conn.execute(
            """
            INSERT INTO user_daily_usage (user_id, usage_date, talk_seconds_used, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, usage_date)
            DO UPDATE SET
                talk_seconds_used = user_daily_usage.talk_seconds_used + EXCLUDED.talk_seconds_used,
                updated_at = NOW()
            RETURNING talk_seconds_used
            """,
            (user_id, usage_date, seconds),
        ).fetchone()

    return result["talk_seconds_used"]
