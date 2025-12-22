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
)
from prompts import ASSISTANT_INSTRUCTIONS, GREETING_INSTRUCTIONS

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

FAREWELL_MESSAGE = (
    "You've reached your daily talk limit. "
    "Thanks for chatting today — see you tomorrow!"
)


class Assistant(Agent):
    """
    Voice assistant agent class.

    The Agent class defines the behavior and instructions for your AI assistant.
    You can customize the instructions and add tool functions as methods.
    """

    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)


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
        farewell = session.generate_reply(
            instructions=f"Say exactly this to the user: '{FAREWELL_MESSAGE}'"
        )
        await asyncio.wait_for(farewell, timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("Farewell message timed out")
    except Exception as e:
        logger.error(f"Error during farewell: {e}")

    logger.info("Disconnecting from room...")
    try:
        await ctx.room.disconnect()
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
    is dispatched to the room. It sets up the voice pipeline and starts
    the conversation.

    Args:
        ctx: The job context containing room and participant info.
    """
    logger.info(f"Starting agent session in room: {ctx.room.name}")

    # Connect to the room first
    await ctx.connect()
    logger.info("Connected to room")

    # Wait for the participant to join and get their metadata
    logger.info("Waiting for participant...")
    participant = await ctx.wait_for_participant()
    logger.info(
        f"Participant joined: {participant.identity}, metadata = {participant.metadata}"
    )

    # Track session start time
    session_start_time = time.time()

    # Get remaining_seconds from participant metadata
    remaining_seconds = get_remaining_seconds_from_metadata(participant)
    if remaining_seconds is not None:
        logger.info(f"Got remaining_seconds from participant: {remaining_seconds}s")
    else:
        logger.warning("No remaining_seconds found in participant metadata")

    # Create the agent session with the STT-LLM-TTS pipeline
    session = AgentSession(
        stt=deepgram.STT(model=STT_MODEL),
        llm=openai.LLM(
            api_key=OPENROUTER_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
        ),
        tts=inworld.TTS(model="inworld-tts-1-max", voice="Ashley"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # Start the session with room configuration
    await session.start(
        room=ctx.room,
        agent=Assistant(),
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

    # Start usage monitoring if we have remaining_seconds
    usage_monitor_task: asyncio.Task | None = None
    if remaining_seconds is not None:
        logger.info(f"Starting usage monitor task with {remaining_seconds}s limit")
        usage_monitor_task = asyncio.create_task(
            monitor_usage(session, ctx, remaining_seconds, session_start_time)
        )
    else:
        logger.warning("Usage monitor NOT started - no remaining_seconds available")

    # Generate the initial greeting
    await session.generate_reply(instructions=GREETING_INSTRUCTIONS)


if __name__ == "__main__":
    agents.cli.run_app(server)
