"""
Database module for the LiveKit agent.
Provides async queries to fetch session and agent configuration.
"""

import ssl
import asyncio
import json
import logging
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg

from config import DATABASE_URL, DAILY_TALK_LIMIT_SECONDS

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """
    Configuration data loaded from CallSession + AgentConfig.

    The config field contains the full JSONB configuration from agent_configs.config.
    Property accessors provide convenient typed access to nested values.
    """

    session_id: int
    agent_id: int
    user_id: str
    config: dict[str, Any]  # The entire agent_configs.config JSONB

    # Convenience accessors for common fields
    @property
    def name(self) -> str:
        """Agent name from config.agent.name"""
        return self.config.get("agent", {}).get("name", "Assistant")

    @property
    def business_name(self) -> str:
        """Business name from config.agent.business_name"""
        return self.config.get("agent", {}).get("business_name", "")

    @property
    def greeting_message(self) -> str:
        """Greeting message from config.agent.greeting_message"""
        return self.config.get("agent", {}).get("greeting_message", "Hello! How can I help you today?")

    @property
    def voice(self) -> dict[str, Any]:
        """Voice configuration from config.voice"""
        return self.config.get("voice", {})

    @property
    def services(self) -> list[dict[str, Any]]:
        """Services list from config.services"""
        return self.config.get("services", [])

    @property
    def knowledge_base(self) -> dict[str, Any]:
        """Knowledge base configuration from config.knowledge_base"""
        return self.config.get("knowledge_base", {})

    @property
    def guardrails(self) -> dict[str, Any]:
        """Guardrails configuration from config.guardrails"""
        return self.config.get("guardrails", {})

    @property
    def conversation(self) -> dict[str, Any]:
        """Conversation configuration from config.conversation"""
        return self.config.get("conversation", {})

    @property
    def output(self) -> dict[str, Any]:
        """Output configuration from config.output"""
        return self.config.get("output", {})

    @property
    def custom_instructions(self) -> Optional[str]:
        """Custom instructions from config.custom_instructions"""
        return self.config.get("custom_instructions")


def _normalize_url(url: str) -> tuple[str, Optional[ssl.SSLContext]]:
    """Return an asyncpg-compatible URL and a verifying SSL context (or None)."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgres://", 1)
    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    sslmode = next((v for k, v in query if k == "sslmode"), None)
    # asyncpg rejects libpq-only params; sslmode is replaced by an explicit context
    kept = [(k, v) for k, v in query if k not in ("sslmode", "channel_binding")]
    url = urlunsplit(parts._replace(query=urlencode(kept)))
    ctx = ssl.create_default_context() if sslmode in ("require", "verify-ca", "verify-full") else None
    return url, ctx


def get_database_url() -> str:
    """Convert DATABASE_URL to asyncpg-compatible format (sslmode stripped)."""
    if DATABASE_URL is None:
        raise ValueError("DATABASE_URL environment variable is not set")
    return _normalize_url(DATABASE_URL)[0]


_pool: Optional[asyncpg.Pool] = None
_pool_lock = asyncio.Lock()


async def _get_pool() -> asyncpg.Pool:
    """Lazily create one pool per process."""
    global _pool
    if _pool is None:
        async with _pool_lock:
            if _pool is None:
                if DATABASE_URL is None:
                    raise ValueError("DATABASE_URL environment variable is not set")
                url, ctx = _normalize_url(DATABASE_URL)
                # statement_cache_size=0: Neon's -pooler endpoint is PgBouncer in
                # transaction mode, which breaks asyncpg's prepared-statement cache.
                _pool = await asyncpg.create_pool(
                    url, ssl=ctx, min_size=1, max_size=5, command_timeout=30,
                    statement_cache_size=0,
                )
    return _pool


async def close_pool() -> None:
    """Close the shared pool (no shutdown hook calls this yet)."""
    global _pool
    if _pool is not None:
        pool, _pool = _pool, None
        await pool.close()


async def get_session_config(room_name: str) -> Optional[SessionConfig]:
    """
    Query CallSession and AgentConfig by room_name (UUID).

    Args:
        room_name: The UUID room name from ctx.room.name

    Returns:
        SessionConfig if found, None otherwise
    """
    try:
        pool = await _get_pool()
        conn = await pool.acquire()

        try:
            row = await conn.fetchrow(
                """
                SELECT
                    cs.id as session_id,
                    cs.agent_id,
                    cs.user_id,
                    ac.config
                FROM call_sessions cs
                JOIN agent_configs ac ON cs.agent_id = ac.id
                WHERE cs.room_name = $1
                """,
                room_name,
            )

            if row is None:
                logger.warning(f"No session found for room_name: {room_name}")
                return None

            # Parse the JSONB config
            config_data = row["config"] or {}

            return SessionConfig(
                session_id=row["session_id"],
                agent_id=row["agent_id"],
                user_id=str(row["user_id"]),
                config=config_data,
            )
        finally:
            await pool.release(conn)

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
        pool = await _get_pool()
        conn = await pool.acquire()

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
            await pool.release(conn)

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
        pool = await _get_pool()
        conn = await pool.acquire()

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
            await pool.release(conn)

    except Exception as e:
        logger.error(f"Database error saving call log: {e}")
        return False
