"""
LiveKit Voice Agent using the modern AgentServer pattern.
This is the recommended approach for LiveKit Agents SDK v1.0+.

Run with:
    uv run agent.py dev      # Development mode
    uv run agent.py console  # Console mode for testing
    uv run agent.py start    # Production mode
"""

import asyncio
import json
import logging
import time
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, inference
from livekit.plugins import noise_cancellation, silero, openai, deepgram, inworld
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config import (
    OPENROUTER_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE,
)
from prompts import (
    FAREWELL_MESSAGE,
    FALLBACK_INSTRUCTIONS,
    FALLBACK_GREETING,
    DynamicPrompts,
    build_prompts,
)
from database import get_session_config

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_remaining_seconds_from_metadata(
    participant: rtc.RemoteParticipant,
) -> int | None:
    """Extract remaining_seconds from participant metadata."""
    if not participant.metadata:
        return None

    try:
        metadata = json.loads(participant.metadata)
        return metadata.get("remaining_seconds")
    except (json.JSONDecodeError, TypeError):
        return None


async def handle_limit_reached(session: AgentSession, ctx: agents.JobContext) -> None:
    """Handle graceful disconnection when usage limit is reached."""
    logger.info("Usage limit reached, saying farewell...")
    try:
        # Interrupt any ongoing speech/processing
        session.interrupt()
        await asyncio.sleep(0.3)

        # Say farewell - don't wait for full playout, just wait for TTS to start
        session.say(FAREWELL_MESSAGE, allow_interruptions=False)

        # Wait briefly for audio to start playing (not full playout)
        # This gives ~5s for the short farewell message
        await asyncio.sleep(5.0)
        logger.info("Farewell audio sent")
    except Exception as e:
        logger.error(f"Error during farewell: {e}")

    # Disconnect - this will end the session
    logger.info("Disconnecting from room...")
    try:
        await asyncio.wait_for(ctx.room.disconnect(), timeout=3.0)
    except asyncio.TimeoutError:
        logger.warning("Room disconnect timed out, forcing exit")
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")


async def monitor_usage(
    session: AgentSession,
    ctx: agents.JobContext,
    max_seconds: int,
    start_time: float,
) -> None:
    """Background task to monitor session duration and enforce limits."""
    logger.info(f"Starting usage monitor with {max_seconds}s limit")

    while True:
        await asyncio.sleep(5)

        elapsed = time.time() - start_time
        remaining = max_seconds - elapsed

        logger.info(f"Usage check: elapsed={elapsed:.0f}s, remaining={remaining:.0f}s")

        if remaining <= 0:
            logger.info(f"Time limit reached after {elapsed:.0f}s")
            await handle_limit_reached(session, ctx)
            break

        if remaining <= 30:
            logger.info(f"Warning: Only {remaining:.0f}s remaining")


# Initialize the AgentServer
server = AgentServer()


@server.rtc_session()
async def agent_session(ctx: agents.JobContext) -> None:
    """
    Handle an RTC session with a participant.

    This function is called when a new participant joins and the agent
    is dispatched to the room. It sets up the voice pipeline with dynamic
    configuration loaded from the database.

    Args:
        ctx: The job context containing room and participant info.
    """
    room_name = ctx.room.name
    logger.info(f"Starting agent session in room: {room_name}")

    # Connect to the room first
    await ctx.connect()
    logger.info("Connected to room")

    # Query session configuration from database
    session_config = await get_session_config(room_name)

    # Build prompts and determine voice based on session config
    if session_config:
        logger.info(f"Loaded session config for agent: {session_config.name}")
        prompts = build_prompts(
            name=session_config.name,
            business_name=session_config.business_name,
            tone=session_config.tone,
            custom_instructions=session_config.custom_instructions,
            knowledge_base_text=session_config.knowledge_base_text,
            greeting_message=session_config.greeting_message,
        )
        voice_id = session_config.voice_id
        max_duration = session_config.max_duration_seconds
    else:
        logger.error(f"No session config found for room: {room_name}, using fallback")
        prompts = DynamicPrompts(
            system_instructions=FALLBACK_INSTRUCTIONS,
            greeting_instructions=FALLBACK_GREETING,
        )
        voice_id = TTS_VOICE  # Default voice from config
        max_duration = 600  # Default 10 minutes

    # Create dynamic agent class with loaded instructions
    class DynamicAssistant(Agent):
        def __init__(self) -> None:
            super().__init__(instructions=prompts.system_instructions)

    # Wait for the participant to join and get their metadata
    logger.info("Waiting for participant...")
    participant = await ctx.wait_for_participant()
    logger.info(
        f"Participant joined: {participant.identity}, metadata = {participant.metadata}"
    )

    # Track session start time
    session_start_time = time.time()

    # Get remaining_seconds from participant metadata (for usage limits)
    remaining_seconds = get_remaining_seconds_from_metadata(participant)
    if remaining_seconds is not None:
        logger.info(f"Got remaining_seconds from participant: {remaining_seconds}s")
    else:
        logger.warning("No remaining_seconds found in participant metadata")

    # Use the smaller of remaining_seconds and max_duration
    effective_limit = remaining_seconds
    if effective_limit is None:
        effective_limit = max_duration
    elif max_duration:
        effective_limit = min(effective_limit, max_duration)

    # Create the agent session with dynamic TTS voice
    session = AgentSession(
        stt=deepgram.STT(model=STT_MODEL),
        llm=openai.LLM(
            api_key=OPENROUTER_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
        ),
        tts=inworld.TTS(model=TTS_MODEL, voice=voice_id),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # Start the session with room configuration
    await session.start(
        room=ctx.room,
        agent=DynamicAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    logger.info("Session started, sending greeting...")

    # Start usage monitoring if we have an effective limit
    usage_monitor_task: asyncio.Task | None = None
    if effective_limit is not None:
        logger.info(f"Starting usage monitor task with {effective_limit}s limit")
        usage_monitor_task = asyncio.create_task(
            monitor_usage(session, ctx, effective_limit, session_start_time)
        )
    else:
        logger.warning("Usage monitor NOT started - no limit available")

    # Generate the dynamic greeting
    await session.generate_reply(instructions=prompts.greeting_instructions)


if __name__ == "__main__":
    agents.cli.run_app(server)
