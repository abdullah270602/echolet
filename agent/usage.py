"""
Usage monitoring module for the voice agent.
Handles session time limits and graceful disconnection.
"""

import asyncio
import json
import logging
import time

from livekit import agents, rtc
from livekit.agents import AgentSession

from prompts import FAREWELL_MESSAGE

logger = logging.getLogger(__name__)


def get_remaining_seconds_from_metadata(
    participant: rtc.RemoteParticipant,
) -> int | None:
    """
    Extract remaining_seconds from participant metadata.

    Args:
        participant: The remote participant to extract metadata from

    Returns:
        Remaining seconds if found, None otherwise
    """
    if not participant.metadata:
        return None

    try:
        metadata = json.loads(participant.metadata)
        return metadata.get("remaining_seconds")
    except (json.JSONDecodeError, TypeError):
        return None


async def handle_limit_reached(
    session: AgentSession,
    ctx: agents.JobContext,
) -> None:
    """
    Handle graceful disconnection when usage limit is reached.
    Says farewell message and disconnects from the room.

    Args:
        session: The agent session to interrupt
        ctx: The job context for room disconnection
    """
    logger.info("Usage limit reached, saying farewell...")
    try:
        session.interrupt()
        await asyncio.sleep(0.3)

        session.say(FAREWELL_MESSAGE, allow_interruptions=False)
        await asyncio.sleep(5.0)
    except Exception as e:
        logger.error(f"Error during farewell: {e}")

    try:
        await asyncio.wait_for(ctx.room.disconnect(), timeout=3.0)
    except asyncio.TimeoutError:
        logger.warning("Room disconnect timed out")
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")


async def monitor_usage(
    session: AgentSession,
    ctx: agents.JobContext,
    max_seconds: int,
    start_time: float,
) -> None:
    """
    Background task to monitor session duration and enforce limits.

    Args:
        session: The agent session to monitor
        ctx: The job context for disconnection
        max_seconds: Maximum allowed session duration
        start_time: Session start timestamp
    """
    logger.debug(f"Usage monitor started: {max_seconds}s limit")

    while True:
        await asyncio.sleep(5)

        elapsed = time.time() - start_time
        remaining = max_seconds - elapsed

        if remaining <= 0:
            logger.info(f"Time limit reached after {elapsed:.0f}s")
            await handle_limit_reached(session, ctx)
            break

        if remaining <= 30:
            logger.warning(f"Low time remaining: {remaining:.0f}s")
