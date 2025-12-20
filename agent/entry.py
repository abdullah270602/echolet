"""
Entry point module for LiveKit Agent using WorkerOptions pattern.
This module provides the entry_point function that gets called when a new session starts.
"""

import asyncio
import json
import logging
import time

from livekit import agents, rtc
from livekit.agents import JobContext, AgentSession, room_io
from livekit.plugins import noise_cancellation, silero, openai, deepgram
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config import (
    OPENROUTER_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    STT_MODEL,
    TTS_MODEL,
)
from prompts import ASSISTANT_INSTRUCTIONS, GREETING_INSTRUCTIONS

logger = logging.getLogger(__name__)

FAREWELL_MESSAGE = (
    "You've reached your daily talk limit. "
    "Thanks for chatting today — see you tomorrow!"
)


class VoiceAssistant(agents.Agent):
    """Voice assistant agent with configurable behavior."""

    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)


async def handle_limit_reached(session: AgentSession, ctx: JobContext) -> None:
    """Handle graceful disconnection when usage limit is reached."""
    logger.info("Usage limit reached, saying farewell...")
    try:
        # Use generate_reply to speak the farewell message
        farewell = session.generate_reply(
            instructions=f"Say exactly this to the user: '{FAREWELL_MESSAGE}'"
        )
        await asyncio.wait_for(farewell, timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("Farewell message timed out")
    except Exception as e:
        logger.error(f"Error during farewell: {e}")

    # Disconnect by leaving the room
    logger.info("Disconnecting from room...")
    try:
        await ctx.room.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")


async def monitor_usage(
    session: AgentSession,
    ctx: JobContext,
    max_seconds: int,
    start_time: float,
) -> None:
    """
    Background task to monitor session duration and enforce limits.

    Args:
        session: The active agent session
        ctx: The job context for room access
        max_seconds: Maximum allowed seconds for this session
        start_time: Session start timestamp
    """
    logger.info(f"Starting usage monitor with {max_seconds}s limit")

    while True:
        await asyncio.sleep(5)

        elapsed = time.time() - start_time
        remaining = max_seconds - elapsed

        logger.debug(f"Usage check: elapsed={elapsed:.0f}s, remaining={remaining:.0f}s")

        if remaining <= 0:
            logger.info(f"Time limit reached after {elapsed:.0f}s")
            await handle_limit_reached(session, ctx)
            break

        if remaining <= 30:
            logger.info(f"Warning: Only {remaining:.0f}s remaining")


def get_remaining_seconds_from_metadata(participant: rtc.RemoteParticipant) -> int | None:
    """Extract remaining_seconds from participant metadata."""
    if not participant.metadata:
        return None

    try:
        metadata = json.loads(participant.metadata)
        return metadata.get("remaining_seconds")
    except (json.JSONDecodeError, TypeError):
        return None


async def entry_point(ctx: JobContext) -> None:
    """
    Main entry point for the LiveKit agent.

    This function is called when a new participant joins a room and
    the agent is dispatched to handle the session.

    Args:
        ctx: The job context containing room info and connection details.
    """
    logger.info(f"Agent connecting to room: {ctx.room.name}")

    # Wait for the room connection to be established
    await ctx.connect()

    logger.info(f"Connected to room: {ctx.room.name}")

    # Track session start time
    session_start_time = time.time()
    remaining_seconds: int | None = None

    # Try to get remaining_seconds from existing participants
    logger.info(f"Checking {len(ctx.room.remote_participants)} remote participants for metadata")
    for identity, participant in ctx.room.remote_participants.items():
        logger.info(f"Participant {identity}: metadata = {participant.metadata}")
        remaining_seconds = get_remaining_seconds_from_metadata(participant)
        if remaining_seconds is not None:
            logger.info(f"Got remaining_seconds from participant {identity}: {remaining_seconds}s")
            break

    if remaining_seconds is None:
        logger.warning("No remaining_seconds found in any participant metadata")

    # Create the agent session with STT, LLM, TTS pipeline
    session = AgentSession(
        stt=deepgram.STT(model=STT_MODEL),
        llm=openai.LLM(
            api_key=OPENROUTER_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
        ),
        tts=deepgram.TTS(model=TTS_MODEL),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # Usage monitoring task
    usage_monitor_task: asyncio.Task | None = None

    # Set up event handlers for session lifecycle
    @session.on("agent_started")
    def on_agent_started():
        logger.info("Agent session started")

    @session.on("agent_stopped")
    def on_agent_stopped():
        logger.info("Agent session stopped")

    @session.on("user_started_speaking")
    def on_user_started_speaking():
        logger.debug("User started speaking")

    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        logger.debug("User stopped speaking")

    # Listen for new participants to get remaining_seconds if not already set
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        nonlocal remaining_seconds, usage_monitor_task

        logger.info(f"New participant connected: {participant.identity}, metadata = {participant.metadata}")

        if remaining_seconds is None:
            remaining_seconds = get_remaining_seconds_from_metadata(participant)
            if remaining_seconds is not None:
                logger.info(f"Got remaining_seconds from new participant: {remaining_seconds}s")
                # Start usage monitoring
                usage_monitor_task = asyncio.create_task(
                    monitor_usage(session, ctx, remaining_seconds, session_start_time)
                )
            else:
                logger.warning(f"No remaining_seconds in metadata for {participant.identity}")

    # Configure audio input with noise cancellation
    def get_noise_cancellation(params: room_io.AudioInputParams):
        """Select appropriate noise cancellation based on participant type."""
        if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            return noise_cancellation.BVCTelephony()
        return noise_cancellation.BVC()

    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=get_noise_cancellation,
            ),
        ),
    )

    logger.info("Agent session started, generating greeting...")

    # Start usage monitoring if we already have remaining_seconds
    if remaining_seconds is not None and usage_monitor_task is None:
        logger.info(f"Starting usage monitor task with {remaining_seconds}s limit")
        usage_monitor_task = asyncio.create_task(
            monitor_usage(session, ctx, remaining_seconds, session_start_time)
        )
    else:
        logger.info(f"Usage monitor not started yet (remaining_seconds={remaining_seconds})")

    # Generate initial greeting
    await session.generate_reply(instructions=GREETING_INSTRUCTIONS)
