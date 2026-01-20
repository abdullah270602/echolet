"""
Transcript capture module for the voice agent.
Handles capturing and logging agent/user speech.
"""

import random
import asyncio
import logging
import os
import time
from typing import AsyncIterable, Annotated, Callable, Awaitable

from livekit import api
from livekit.agents import Agent, ModelSettings, function_tool
from livekit.agents.voice import RunContext
from pydantic import Field

logger = logging.getLogger(__name__)

# LiveKit API credentials for room management
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")


def create_dynamic_assistant(
    instructions: str,
    transcript_log: list[dict],
    room_name: str,
    session_start_time: float,
    save_call_log_fn: Callable[..., Awaitable[bool]],
    send_to_queue_fn: Callable[[str], Awaitable[None]],
    cleanup_done: dict[str, bool],
) -> type[Agent]:
    """
    Factory function to create a DynamicAssistant class with transcript logging.

    Args:
        instructions: System instructions for the agent
        transcript_log: Shared list to append agent messages to
        room_name: LiveKit room name for cleanup
        session_start_time: Session start timestamp for duration calculation
        save_call_log_fn: Async function to save call logs
        send_to_queue_fn: Async function to send to analysis queue
        cleanup_done: Shared dict to track if cleanup was handled

    Returns:
        A DynamicAssistant class configured with the given instructions
    """

    class DynamicAssistant(Agent):
        def __init__(self) -> None:
            super().__init__(instructions=instructions)
            self._transcript_log = transcript_log
            self._room_name = room_name
            self._session_start_time = session_start_time
            self._save_call_log_fn = save_call_log_fn
            self._send_to_queue_fn = send_to_queue_fn
            self._cleanup_done = cleanup_done

        async def transcription_node(
            self,
            text: AsyncIterable[str],
            model_settings: ModelSettings,
        ) -> AsyncIterable[str]:
            """
            Override transcription_node to capture agent output for transcript logging.
            Collects streamed text and logs the complete response.
            """
            collected_text = ""
            async for delta in text:
                collected_text += delta
                yield delta

            if collected_text.strip():
                self._transcript_log.append({
                    "role": "agent",
                    "content": collected_text.strip(),
                    "timestamp": time.time(),
                })
                logger.debug(f"Agent transcript: {collected_text[:50]}...")

        @function_tool()
        async def end_call(
            self,
            ctx: RunContext,
            reason: Annotated[
                str,
                Field(
                    description="The reason for ending: 'user_goodbye' or 'user_requested'"
                )
            ] = "user_goodbye",
            already_said_goodbye: Annotated[
                bool,
                Field(
                    description="Set to true if you already said goodbye in your response text. Set to false if you need the system to play a goodbye message."
                )
            ] = False,
        ) -> str:
            """
            End the current call gracefully.

            ONLY call when user EXPLICITLY says goodbye:
            - "goodbye", "bye", "bye bye", "see you", "take care"
            - Explicitly asks to hang up or end the call

            DO NOT call when user says:
            - "no", "nothing else", "that's all" - these are answers, not goodbyes
            - After these, YOU say goodbye and wait for them to say bye back

            IMPORTANT: Set already_said_goodbye=true if you said goodbye in your response.
            If you didn't say goodbye, set already_said_goodbye=false and the system will play one.
            """
            logger.info(f"End call requested: {reason}, already_said_goodbye={already_said_goodbye}")

            # Log the end call event
            self._transcript_log.append({
                "role": "system",
                "content": f"Call ended by agent: {reason}",
                "timestamp": time.time(),
            })

            # 1. Play goodbye message only if LLM didn't already say one
            if not already_said_goodbye:
                goodbyes = [
                    "Thanks for calling, take care.",
                    "Goodbye, have a great day.",
                    "Thanks for reaching out, bye.",
                ]
                goodbye_msg = random.choice(goodbyes)

                try:
                    speech_handle = ctx.session.say(goodbye_msg, allow_interruptions=False)
                    await speech_handle.wait_for_playout()
                    logger.debug(f"Outro played: {goodbye_msg}")
                except Exception as e:
                    logger.warning(f"Goodbye playout failed: {e}")
                    await asyncio.sleep(2.0)  # Fallback delay
            else:
                # LLM already said goodbye, just wait for it to finish
                await asyncio.sleep(1)
                logger.debug("Waiting for LLM goodbye to finish")

            # 2. Small natural pause
            await asyncio.sleep(0.3)

            # 3. Save call log (sync - important for data integrity)
            duration = int(time.time() - self._session_start_time)
            try:
                success = await self._save_call_log_fn(
                    room_name=self._room_name,
                    transcript=self._transcript_log,
                    duration_seconds=duration,
                    status="completed",
                )
                if success:
                    logger.info(f"Call log saved: {duration}s, {len(self._transcript_log)} messages")
                    self._cleanup_done["value"] = True  # Mark cleanup as done
                else:
                    logger.warning(f"Failed to save call log: {self._room_name}")
            except Exception as e:
                logger.error(f"Save call log error: {e}")

            # 4. Send to SQS as background task (don't block disconnect)
            async def send_to_queue_background():
                try:
                    await self._send_to_queue_fn(self._room_name)
                    logger.debug(f"Sent to analysis queue: {self._room_name}")
                except Exception as e:
                    logger.error(f"SQS send error: {e}")

            asyncio.create_task(send_to_queue_background())

            # 5. Delete room immediately to disconnect user
            try:
                async with api.LiveKitAPI(
                    LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
                ) as lk_api:
                    await lk_api.room.delete_room(api.DeleteRoomRequest(room=self._room_name))
                    logger.info(f"Room deleted: {self._room_name}")
            except Exception as e:
                logger.debug(f"Room deletion skipped: {e}")

            return f"Call ended: {reason}"

    return DynamicAssistant


def create_user_transcript_handler(transcript_log: list[dict]):
    """
    Create an event handler for user speech transcriptions.

    Args:
        transcript_log: Shared list to append user messages to

    Returns:
        Event handler function for user_input_transcribed events
    """

    def on_user_transcribed(event):
        """Capture user speech transcriptions."""
        if event.is_final:
            transcript_log.append({
                "role": "user",
                "content": event.transcript,
                "timestamp": time.time(),
                "language": getattr(event, "language", None),
            })
            logger.debug(f"User transcript: {event.transcript[:50]}...")

    return on_user_transcribed
