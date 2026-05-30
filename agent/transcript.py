"""
Transcript capture module for the voice agent.
Handles capturing and logging agent/user speech.
"""

import asyncio
import logging
import os
import time
from typing import AsyncIterable, Annotated, Callable, Awaitable

from livekit import api
from livekit.agents import Agent, ModelSettings, function_tool
from livekit.agents.voice import RunContext
from pydantic import Field

from call_ending import caller_said_goodbye

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
    before_hangup: Callable[[], Awaitable[None]] | None = None,
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
            self._before_hangup = before_hangup
            # Log available tools for debugging
            logger.info(f"DynamicAssistant initialized with tools: {self.tools}")

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
            already_said_goodbye: Annotated[
                bool,
                Field(
                    description="Set true if you said goodbye in your response. Set false if you need me to say goodbye for you."
                )
            ] = True,
        ) -> str:
            """
            End the current call. USE SPARINGLY - only when user explicitly says goodbye.

            ONLY call when user said: "bye", "goodbye", "take care", "that's all", "nothing else", "hang up"

            DO NOT call when user:
            - Asked a question (even "how to buy?")
            - Answered YOUR question (even "most advanced one")
            - Said "no", "I won't buy", "leave it", "okay", "thanks"

            When in doubt, ask "Anything else?" instead of ending.
            """
            logger.info(f"end_call called, already_said_goodbye={already_said_goodbye}")

            # Safety checks: never hang up on a caller who is still talking business.
            user_messages = [m for m in self._transcript_log if m.get("role") == "user"]
            if len(user_messages) < 2:
                logger.warning(f"end_call too early: only {len(user_messages)} user message(s)")
                return "Conversation too short. Ask if there's anything else you can help with first."
            if not caller_said_goodbye(user_messages[-1].get("content", "")):
                logger.warning("end_call refused: caller's last turn was not a goodbye")
                return (
                    "Call NOT ended: the caller has not said goodbye. Do not say goodbye. "
                    "Answer what they just said and keep helping."
                )

            # Log the end
            self._transcript_log.append({
                "role": "system",
                "content": "Call ended by agent",
                "timestamp": time.time(),
            })

            # Wait for the LLM's goodbye message to finish playing
            # ctx.wait_for_playout() waits for speech generated BEFORE this tool call
            try:
                await ctx.wait_for_playout()
                logger.debug("Playout complete, proceeding to end call")
            except Exception as e:
                logger.warning(f"wait_for_playout failed: {e}")
                # Fallback: give some time for speech to play
                await asyncio.sleep(3.0)

            # If LLM didn't say goodbye, say one now
            if not already_said_goodbye:
                try:
                    speech_handle = ctx.session.say(
                        "Thanks for calling, take care!",
                        allow_interruptions=False
                    )
                    await speech_handle.wait_for_playout()
                    logger.debug("Fallback goodbye played")
                except Exception as e:
                    logger.warning(f"Fallback goodbye failed: {e}")

            # Save call log
            duration = int(time.time() - self._session_start_time)
            try:
                success = await self._save_call_log_fn(
                    room_name=self._room_name,
                    transcript=self._transcript_log,
                    duration_seconds=duration,
                    status="completed",
                )
                if success:
                    self._cleanup_done["value"] = True
                    logger.info(f"Call log saved: {duration}s")
                else:
                    logger.warning(f"Failed to save call log: {self._room_name}")
            except Exception as e:
                logger.error(f"Save call log error: {e}")

            # Send to SQS (background)
            asyncio.create_task(self._send_to_queue_fn(self._room_name))

            # Last chance to talk to the caller's browser (demo calls push their ticket).
            if self._before_hangup:
                try:
                    await asyncio.wait_for(self._before_hangup(), timeout=12)
                except Exception as e:
                    logger.warning(f"before_hangup failed: {e}")

            # Delete room
            try:
                async with api.LiveKitAPI(
                    LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
                ) as lk_api:
                    await lk_api.room.delete_room(api.DeleteRoomRequest(room=self._room_name))
                    logger.info(f"Room deleted: {self._room_name}")
            except Exception as e:
                logger.debug(f"Room deletion skipped: {e}")

            return "Call ended successfully"

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
