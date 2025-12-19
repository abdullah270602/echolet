"""
LiveKit Voice Agent using the modern AgentServer pattern.
This is the recommended approach for LiveKit Agents SDK v1.0+.

Run with:
    uv run agent.py dev      # Development mode
    uv run agent.py console  # Console mode for testing
    uv run agent.py start    # Production mode
"""

import logging
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
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

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Assistant(Agent):
    """
    Voice assistant agent class.

    The Agent class defines the behavior and instructions for your AI assistant.
    You can customize the instructions and add tool functions as methods.
    """

    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)


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

    # Create the agent session with the STT-LLM-TTS pipeline
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

    # Start the session with room configuration
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    logger.info("Session started, sending greeting...")

    # Generate the initial greeting
    await session.generate_reply(instructions=GREETING_INSTRUCTIONS)


if __name__ == "__main__":
    agents.cli.run_app(server)
