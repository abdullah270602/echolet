"""
Database module for the LiveKit agent.
Provides async queries to fetch session and agent configuration.
"""

import ssl
import json
import logging
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

import asyncpg

from config import DATABASE_URL, DAILY_TALK_LIMIT_SECONDS

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """Configuration data loaded from CallSession + AgentConfig."""

    session_id: int
    agent_id: int
    user_id: str

    # Agent Identity
    name: str
    business_name: str
    voice_id: str
    greeting_message: str

    # Agent Behavior
    tone: str
    custom_instructions: Optional[str]

    # Knowledge
    knowledge_base_text: Optional[str]


def get_database_url() -> str:
    """Convert DATABASE_URL to asyncpg-compatible format."""
    if DATABASE_URL is None:
        raise ValueError("DATABASE_URL environment variable is not set")

    url = DATABASE_URL
    # asyncpg expects postgres:// instead of postgresql://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgres://", 1)
    return url


async def get_session_config(room_name: str) -> Optional[SessionConfig]:
    """
    Query CallSession and AgentConfig by room_name (UUID).

    Args:
        room_name: The UUID room name from ctx.room.name

    Returns:
        SessionConfig if found, None otherwise
    """
    try:
        url = get_database_url()

        # Handle SSL for cloud databases (e.g., Supabase, Neon)
        ssl_context = None
        if "sslmode=require" in url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            # Remove sslmode from URL since we're handling it separately
            url = url.replace("?sslmode=require", "").replace("&sslmode=require", "")

        conn = await asyncpg.connect(url, ssl=ssl_context)

        try:
            row = await conn.fetchrow(
                """
                SELECT
                    cs.id as session_id,
                    cs.agent_id,
                    cs.user_id,
                    ac.name,
                    ac.business_name,
                    ac.voice_id,
                    ac.greeting_message,
                    ac.tone,
                    ac.custom_instructions,
                    ac.knowledge_base_text
                FROM call_sessions cs
                JOIN agent_configs ac ON cs.agent_id = ac.id
                WHERE cs.room_name = $1
                """,
                room_name,
            )

            if row is None:
                logger.warning(f"No session found for room_name: {room_name}")
                return None

            return SessionConfig(
                session_id=row["session_id"],
                agent_id=row["agent_id"],
                user_id=str(row["user_id"]),  # Convert UUID to string
                name=row["name"],
                business_name=row["business_name"],
                voice_id=row["voice_id"],
                greeting_message=row["greeting_message"],
                tone=row["tone"],
                custom_instructions=row["custom_instructions"],
                knowledge_base_text=row["knowledge_base_text"],
            )
        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Database error fetching session config: {e}")
        return None


async def get_user_remaining_seconds(user_id: str) -> Optional[int]:
    """
    Query user's remaining talk seconds for today from database.

    Args:
        user_id: The user's UUID (from session_config.user_id)

    Returns:
        Remaining seconds for today, or None if error
    """
    try:
        url = get_database_url()

        # Handle SSL for cloud databases
        ssl_context = None
        if "sslmode=require" in url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            url = url.replace("?sslmode=require", "").replace("&sslmode=require", "")

        conn = await asyncpg.connect(url, ssl=ssl_context)

        try:
            today = datetime.now(timezone.utc).date()

            # Get today's usage for this user
            row = await conn.fetchrow(
                """
                SELECT talk_seconds_used
                FROM user_daily_usage
                WHERE user_id = $1 AND usage_date = $2
                """,
                user_id,
                today,
            )

            used_seconds = row["talk_seconds_used"] if row else 0
            remaining = max(0, DAILY_TALK_LIMIT_SECONDS - used_seconds)

            logger.debug(
                f"User {user_id}: used={used_seconds}s, limit={DAILY_TALK_LIMIT_SECONDS}s, remaining={remaining}s"
            )
            return remaining

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Database error fetching user remaining seconds: {e}")
        return None


async def save_call_log(
    room_name: str,
    transcript: list[dict[str, Any]],
    duration_seconds: int,
    status: str = "completed",
    summary: Optional[str] = "Pending",
    priority: str = "normal",
) -> bool:
    """
    Save call transcript and metadata to the database, and update user's daily usage.

    Args:
        room_name: The UUID room name (used to identify the call session)
        transcript: List of message dicts with role, content, timestamp
        duration_seconds: Total call duration in seconds
        status: Session status (default: "completed")
        summary: AI-generated summary (default: "Pending")
        priority: Call priority level (default: "normal")

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        url = get_database_url()

        # Handle SSL for cloud databases
        ssl_context = None
        if "sslmode=require" in url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            url = url.replace("?sslmode=require", "").replace("&sslmode=require", "")

        conn = await asyncpg.connect(url, ssl=ssl_context)

        try:
            # Convert transcript to JSON string for asyncpg
            transcript_json = json.dumps(transcript)

            # Update call session and get the user_id
            row = await conn.fetchrow(
                """
                UPDATE call_sessions
                SET
                    transcript = $1::jsonb,
                    duration_seconds = $2,
                    status = $3,
                    summary = $4,
                    priority = $5,
                    ended_at = $6
                WHERE room_name = $7
                RETURNING user_id
                """,
                transcript_json,
                duration_seconds,
                status,
                summary,
                priority,
                datetime.utcnow(),
                room_name,
            )

            if row is None:
                logger.warning(f"No call session found: {room_name}")
                return False

            user_id = row["user_id"]

            # Update user's daily usage
            today = datetime.now(timezone.utc).date()
            await conn.execute(
                """
                INSERT INTO user_daily_usage (user_id, usage_date, talk_seconds_used, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $4)
                ON CONFLICT ON CONSTRAINT uq_user_daily_usage_user_date
                DO UPDATE SET
                    talk_seconds_used = user_daily_usage.talk_seconds_used + $3,
                    updated_at = $4
                """,
                user_id,
                today,
                duration_seconds,
                datetime.utcnow(),
            )

            return True

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Database error saving call log: {e}")
        return False
