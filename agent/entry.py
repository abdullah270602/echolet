"""
Entry point module for LiveKit Agent using WorkerOptions pattern.
This module provides the entry_point function that gets called when a new session starts.
"""

import logging
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


class VoiceAssistant(agents.Agent):
    """Voice assistant agent with configurable behavior."""

    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)


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

    # Generate initial greeting
    await session.generate_reply(instructions=GREETING_INSTRUCTIONS)
