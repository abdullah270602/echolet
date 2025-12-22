"""
Database module for the LiveKit agent.
Provides async queries to fetch session and agent configuration.
"""

import ssl
import logging
from typing import Optional
from dataclasses import dataclass

import asyncpg

from config import DATABASE_URL

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

    # Limits
    max_duration_seconds: int


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
                    ac.knowledge_base_text,
                    ac.max_duration_seconds
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
                user_id=row["user_id"],
                name=row["name"],
                business_name=row["business_name"],
                voice_id=row["voice_id"],
                greeting_message=row["greeting_message"],
                tone=row["tone"],
                custom_instructions=row["custom_instructions"],
                knowledge_base_text=row["knowledge_base_text"],
                max_duration_seconds=row["max_duration_seconds"],
            )
        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Database error fetching session config: {e}")
        return None
