"""
LiveKit Voice Agent - Main Entry Point

Run with:
    uv run agent.py dev      # Development mode
    uv run agent.py console  # Console mode for testing
    uv run agent.py start    # Production mode
"""

import asyncio
import logging
import time
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, room_io
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
    FALLBACK_INSTRUCTIONS,
    FALLBACK_GREETING,
    DynamicPrompts,
    build_prompts,
)
from database import get_session_config, get_user_remaining_seconds, save_call_log
from usage import monitor_usage
from transcript import create_dynamic_assistant, create_user_transcript_handler
from sqs import send_to_analysis_queue

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the AgentServer
server = AgentServer()


@server.rtc_session()
async def agent_session(ctx: agents.JobContext) -> None:
    """
    Handle an RTC session with a participant.
    Sets up the voice pipeline with dynamic configuration from the database.
    """
    room_name = ctx.room.name
    session_start_time = time.time()
    transcript_messages: list[dict] = []
    call_status = "completed"
    cleanup_done = {"value": False}  # Track if end_call tool handled cleanup

    logger.info(f"Session started: {room_name}")

    try:
        await ctx.connect()

        # Load session configuration
        session_config = await get_session_config(room_name)

        if session_config:
            logger.debug(f"Loaded config: {session_config.name}")
            prompts = build_prompts(
                name=session_config.name,
                business_name=session_config.business_name,
                tone=session_config.tone,
                custom_instructions=session_config.custom_instructions,
                knowledge_base_text=session_config.knowledge_base_text,
                greeting_message=session_config.greeting_message,
            )
            voice_id = session_config.voice_id
            user_id = session_config.user_id
        else:
            logger.error(f"No config for room: {room_name}, using fallback")
            prompts = DynamicPrompts(
                system_instructions=FALLBACK_INSTRUCTIONS,
                greeting_instructions=FALLBACK_GREETING,
            )
            voice_id = TTS_VOICE
            user_id = None

        # Create dynamic agent with transcript logging and cleanup capabilities
        DynamicAssistant = create_dynamic_assistant(
            instructions=prompts.system_instructions,
            transcript_log=transcript_messages,
            room_name=room_name,
            session_start_time=session_start_time,
            save_call_log_fn=save_call_log,
            send_to_queue_fn=send_to_analysis_queue,
            cleanup_done=cleanup_done,
        )

        # Wait for participant
        participant = await ctx.wait_for_participant()

        # Get user's remaining talk time from database (global daily limit)
        remaining_seconds = None
        if user_id:
            remaining_seconds = await get_user_remaining_seconds(user_id)
            logger.info(f"User {user_id} has {remaining_seconds}s remaining today")

        # Create the agent session
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

        # Register transcript handlers
        session.on("user_input_transcribed")(
            create_user_transcript_handler(transcript_messages)
        )

        # Start the session
        await session.start(
            room=ctx.room,
            agent=DynamicAssistant(),
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

        # Start usage monitoring (if we have a remaining limit)
        usage_task: asyncio.Task | None = None
        if remaining_seconds is not None and remaining_seconds > 0:
            usage_task = asyncio.create_task(
                monitor_usage(session, ctx, remaining_seconds, session_start_time)
            )

        # Send greeting
        await session.generate_reply(instructions=prompts.greeting_instructions)

        # Wait for session close
        session_closed = asyncio.Event()

        @session.on("close")
        def on_close():
            session_closed.set()

        await session_closed.wait()

        # Cleanup usage monitor
        if usage_task and not usage_task.done():
            usage_task.cancel()
            try:
                await usage_task
            except asyncio.CancelledError:
                pass

        # Note: Cleanup (save logs, SQS, room deletion) is handled by end_call tool
        # This on_close just cleans up the usage monitor

    except Exception as e:
        logger.error(f"Session error: {e}")
        call_status = "failed"
        raise

    finally:
        # Always save call log if end_call tool didn't handle it
        if not cleanup_done["value"]:
            logger.info(f"Cleanup: saving call log")
            duration = int(time.time() - session_start_time)
            try:
                await save_call_log(
                    room_name=room_name,
                    transcript=transcript_messages,
                    duration_seconds=duration,
                    status=call_status,
                )
                logger.info(f"Call log saved: {duration}s, {len(transcript_messages)} messages")

                # Send to analysis queue
                try:
                    await send_to_analysis_queue(room_name)
                    logger.debug(f"Sent to analysis queue: {room_name}")
                except Exception as sqs_error:
                    logger.error(f"SQS send error: {sqs_error}")

            except Exception as save_error:
                logger.error(f"Cleanup save failed: {save_error}")


if __name__ == "__main__":
    agents.cli.run_app(server)
