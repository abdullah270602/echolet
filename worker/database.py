"""
Database Operations for Worker

Handles fetching transcripts and updating analysis results.
"""

import json
import logging
import ssl
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import asyncpg

from config import DATABASE_URL

logger = logging.getLogger(__name__)


def get_ssl_context(url: str) -> Optional[ssl.SSLContext]:
    """Create SSL context if sslmode=require is in URL."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    if "sslmode" in query_params:
        sslmode = query_params["sslmode"][0]
        if sslmode in ("require", "verify-ca", "verify-full"):
            return ssl.create_default_context()
    return None


def get_clean_url(url: str) -> str:
    """Remove sslmode from URL for asyncpg (handled separately)."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    if "sslmode" in query_params:
        del query_params["sslmode"]
        new_query = "&".join(f"{k}={v[0]}" for k, v in query_params.items())
        parsed = parsed._replace(query=new_query)

    return parsed.geturl()


async def fetch_call_data(room_name: str) -> Optional[dict[str, Any]]:
    """
    Fetch transcript and agent output config for a call session.

    Args:
        room_name: The UUID room name (session identifier)

    Returns:
        Dict with 'transcript' and 'output_config', or None if not found
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return None

    ssl_context = get_ssl_context(DATABASE_URL)
    clean_url = get_clean_url(DATABASE_URL)

    try:
        conn = await asyncpg.connect(clean_url, ssl=ssl_context)

        try:
            row = await conn.fetchrow(
                """
                SELECT
                    cs.transcript,
                    ac.config->'output' as output_config
                FROM call_sessions cs
                LEFT JOIN agent_configs ac ON cs.agent_id = ac.id
                WHERE cs.room_name = $1
                """,
                room_name,
            )

            if row is None:
                return None

            transcript = None
            if row["transcript"]:
                transcript = json.loads(row["transcript"]) if isinstance(row["transcript"], str) else row["transcript"]

            output_config = row["output_config"] or {}
            if isinstance(output_config, str):
                output_config = json.loads(output_config)

            return {
                "transcript": transcript,
                "output_config": output_config,
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Failed to fetch call data for {room_name}: {e}")
        return None


# Legacy function for backward compatibility
async def fetch_transcript(room_name: str) -> Optional[list[dict[str, Any]]]:
    """
    Fetch transcript for a call session by room name.

    DEPRECATED: Use fetch_call_data() instead to also get output config.
    """
    result = await fetch_call_data(room_name)
    return result["transcript"] if result else None


async def update_analysis(
    room_name: str,
    summary: str,
    category: str,
    urgency: str,
    sentiment: str,
    action_required: bool,
    action_items: list[str],
) -> bool:
    """
    Update call session with analysis results.

    Args:
        room_name: The UUID room name (session identifier)
        summary: AI-generated summary
        category: Call type (Appointment, Inquiry, Complaint, etc.)
        urgency: Priority level (High, Medium, Low)
        sentiment: Caller mood (Positive, Neutral, Frustrated, Angry)
        action_required: Whether human follow-up is needed
        action_items: List of action item strings

    Returns:
        True if update succeeded, False otherwise
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return False

    ssl_context = get_ssl_context(DATABASE_URL)
    clean_url = get_clean_url(DATABASE_URL)

    try:
        conn = await asyncpg.connect(clean_url, ssl=ssl_context)

        try:
            result = await conn.execute(
                """
                UPDATE call_sessions
                SET summary = $1,
                    category = $2,
                    urgency = $3,
                    sentiment = $4,
                    action_required = $5,
                    action_items = $6
                WHERE room_name = $7
                """,
                summary,
                category,
                urgency,
                sentiment,
                action_required,
                json.dumps(action_items),
                room_name,
            )

            updated = result.split()[-1] != "0"
            if updated:
                logger.info(f"Updated analysis for {room_name}")
            else:
                logger.warning(f"No session found for {room_name}")
            return updated

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Failed to update analysis for {room_name}: {e}")
        return False
