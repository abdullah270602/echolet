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
    DAILY_TALK_LIMIT_SECONDS,
)
from prompts import FAREWELL_MESSAGE, build_prompts_from_config
from database import SessionConfig, get_session_config, get_user_remaining_seconds, save_call_log
from usage import monitor_usage
from transcript import create_dynamic_assistant, create_user_transcript_handler
from sqs import send_to_analysis_queue
from demo import (
    DEMO_FAREWELL,
    is_demo_room,
    parse_demo_metadata,
    skip_analysis_queue,
    skip_save_call_log,
)

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_tts(voice_config: dict):
    """
    Create TTS instance based on provider selection from config.

    Args:
        voice_config: Voice configuration dict with provider, voice_id, etc.

    Returns:
        TTS instance for the selected provider
    """
    provider = voice_config.get("provider", "inworld")
    voice_id = voice_config.get("voice_id", TTS_VOICE)

    logger.info(f"Creating TTS: provider={provider}, voice={voice_id}")

    if provider == "inworld":
        return inworld.TTS(model=TTS_MODEL, voice=voice_id)
    elif provider == "deepgram":
        return deepgram.TTS(model=voice_id)
    else:
        logger.warning(f"Unknown TTS provider '{provider}', falling back to inworld")
        return inworld.TTS(model=TTS_MODEL, voice=TTS_VOICE)


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
    cleanup_done = {"value": False}  # Set by the end_call tool once it has saved the log
    demo = is_demo_room(room_name)
    save_fn = skip_save_call_log if demo else save_call_log
    queue_fn = skip_analysis_queue if demo else send_to_analysis_queue

    logger.info(f"Session started: {room_name} (demo={demo})")

    try:
        await ctx.connect()
        participant = await ctx.wait_for_participant()

        # Resolve config and the hard time cap for this call.
        if demo:
            parsed = parse_demo_metadata(participant.metadata)
            session_config, time_cap = None, None
            if parsed:
                demo_config, time_cap = parsed
                session_config = SessionConfig(session_id=0, agent_id=0, user_id="", config=demo_config)
            farewell = DEMO_FAREWELL
        else:
            session_config = await get_session_config(room_name)
            time_cap = None
            if session_config:
                if session_config.user_id:
                    time_cap = await get_user_remaining_seconds(session_config.user_id)
                # Fail closed: every real call is capped. If today's usage can't be
                # read, fall back to a full day's allowance instead of no limit.
                if time_cap is None:
                    logger.warning(f"Usage unavailable for room {room_name}; capping at the daily limit")
                    time_cap = DAILY_TALK_LIMIT_SECONDS
                logger.info(f"Room {room_name}: {time_cap}s of talk time allowed")
            farewell = FAREWELL_MESSAGE

        # Every legitimate room is created by the backend with a session row (or a
        # signed demo token). Anything else gets no agent, so there is never an
        # unmetered conversation.
        if session_config is None:
            logger.error(f"No config for room {room_name}; leaving without answering")
            cleanup_done["value"] = True  # nothing to persist
            ctx.shutdown(reason="unknown room")
            return
        if time_cap is not None and time_cap <= 0:
            logger.info(f"No talk time left for room {room_name}; leaving")
            cleanup_done["value"] = True
            ctx.shutdown(reason="usage limit reached")
            return

        prompts = build_prompts_from_config(session_config, saved=not demo)

        DynamicAssistant = create_dynamic_assistant(
            instructions=prompts.system_instructions,
            transcript_log=transcript_messages,
            room_name=room_name,
            session_start_time=session_start_time,
            save_call_log_fn=save_fn,
            send_to_queue_fn=queue_fn,
            cleanup_done=cleanup_done,
        )

        # Create the agent session
        session = AgentSession(
            stt=deepgram.STT(model=STT_MODEL),
            llm=openai.LLM(
                api_key=OPENROUTER_API_KEY,
                base_url=LLM_BASE_URL,
                model=LLM_MODEL,
            ),
            tts=create_tts(session_config.voice),
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

        # Enforce the time cap (daily allowance, or the demo call length)
        usage_task: asyncio.Task | None = None
        if time_cap is not None:
            usage_task = asyncio.create_task(
                monitor_usage(session, ctx, time_cap, session_start_time, farewell)
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
        logger.exception(f"Session error: {e}")
        call_status = "failed"
        raise

    finally:
        # Always save call log if end_call tool didn't handle it
        if not cleanup_done["value"]:
            logger.info("Cleanup: saving call log")
            duration = int(time.time() - session_start_time)
            try:
                await save_fn(
                    room_name=room_name,
                    transcript=transcript_messages,
                    duration_seconds=duration,
                    status=call_status,
                )
                logger.info(f"Call log saved: {duration}s, {len(transcript_messages)} messages")

                # Send to analysis queue
                try:
                    await queue_fn(room_name)
                    logger.debug(f"Sent to analysis queue: {room_name}")
                except Exception as sqs_error:
                    logger.error(f"SQS send error: {sqs_error}")

            except Exception as save_error:
                logger.error(f"Cleanup save failed: {save_error}")


if __name__ == "__main__":
    agents.cli.run_app(server)
