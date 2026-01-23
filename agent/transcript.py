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

# =============================================================================
# CALL ENDING VALIDATION HELPERS
# These ensure calls only end when appropriate, not prematurely
# =============================================================================

# Farewell words that signal call ending (when used AS A CLOSING, not just mentioned)
FAREWELL_CLOSINGS = {
    "bye", "goodbye", "bye bye", "bye-bye", "see ya", "see you",
    "take care", "have a good one", "have a good day", "goodnight",
    "gotta go", "talk later", "talk to you later", "later"
}

# Explicit hangup requests
HANGUP_REQUESTS = {"hang up", "end the call", "disconnect", "end call"}

# Soft close acknowledgments (user responding to agent's "thanks for calling")
SOFT_CLOSE_ACKS = {"thanks", "thank you", "you too", "okay", "alright", "sure", "yep", "yes", "ok"}


def is_farewell_closing(text: str) -> tuple[bool, str]:
    """
    Check if text ends with a farewell AS A CLOSING (not just mentioned in passing).

    We check the ENDING of the message because farewells typically come at the end.
    "My friend said bye" → False (bye is in the middle, just mentioned)
    "Okay, bye!" → True (bye is at the end, it's a closing)

    Returns:
        (is_farewell, detected_word) - tuple of bool and the word detected
    """
    text_lower = text.lower().strip()
    if not text_lower:
        return False, ""

    # Check the last portion of the message (where closings typically appear)
    ending = text_lower[-30:] if len(text_lower) > 30 else text_lower

    for word in FAREWELL_CLOSINGS:
        if word in ending:
            return True, word
    return False, ""


def is_hangup_request(text: str) -> bool:
    """Check if user explicitly asked to hang up or end the call."""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in HANGUP_REQUESTS)


def is_soft_close_ack(text: str) -> bool:
    """
    Check if text is a short acknowledgment (response to agent's goodbye).

    Examples: "thanks", "you too", "okay"
    NOT: long sentences with these words embedded
    """
    text_lower = text.lower().strip()
    # Only consider short responses as acknowledgments
    if len(text_lower) > 50:
        return False
    return any(word in text_lower for word in SOFT_CLOSE_ACKS)


def detect_closing_sequence(transcript: list[dict]) -> bool:
    """
    Check if conversation has a proper closing sequence for natural endings.

    A proper sequence is:
    1. Agent asked "anything else?" or similar
    2. User declined ("no", "that's all", etc.)
    3. Agent said soft close ("thanks for calling!")

    Returns:
        True if proper closing sequence detected
    """
    if len(transcript) < 3:
        return False

    # Look at recent messages for closing pattern
    recent = transcript[-8:] if len(transcript) >= 8 else transcript

    agent_asked_anything_else = False
    user_declined = False
    agent_soft_close = False

    for msg in recent:
        content = msg.get("content", "").lower()
        role = msg.get("role", "")

        if role == "agent":
            if any(phrase in content for phrase in [
                "anything else", "help with anything", "anything more",
                "something else", "anything i can help", "else i can do"
            ]):
                agent_asked_anything_else = True
            if any(phrase in content for phrase in [
                "thanks for calling", "thank you for calling",
                "have a great", "have a good", "take care"
            ]):
                agent_soft_close = True
        elif role == "user":
            if agent_asked_anything_else and any(word in content for word in [
                "no", "nope", "that's all", "thats all", "i'm good", "im good",
                "all set", "all good", "nothing", "that'll be all"
            ]):
                user_declined = True

    return agent_asked_anything_else and user_declined and agent_soft_close


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
                    description="""Why the call is ending. MUST be one of:
- 'user_goodbye': User said 'bye', 'goodbye', 'take care' AS THEIR CLOSING (at end of their message)
- 'natural_close': Proper closing sequence (you asked 'anything else?', user said no, you said thanks, user acknowledged)
- 'user_hangup_request': User explicitly said 'hang up' or 'end the call'

DO NOT use if: user just gave information, said 'no' to a question, said 'thanks' alone, or there was silence."""
                )
            ] = "user_goodbye",
            detected_closing_phrase: Annotated[
                str,
                Field(
                    description="The EXACT phrase that triggered ending (e.g., 'bye', 'you too', 'hang up'). Required for user_goodbye and user_hangup_request."
                )
            ] = "",
            already_said_goodbye: Annotated[
                bool,
                Field(
                    description="You MUST say goodbye in your response BEFORE calling this. Set true if you did."
                )
            ] = True,
        ) -> str:
            """
            End the current call gracefully. USE WITH EXTREME CAUTION.

            ⛔ BEFORE calling, verify:
            1. Is this a REAL ending? (Not just user answering your question)
            2. Have there been at least 2 user messages?
            3. Did you say goodbye in your response?

            ✅ VALID endings:
            - User: "Okay, bye!" → reason='user_goodbye', detected_closing_phrase='bye'
            - User: "Thanks, take care!" → reason='user_goodbye', detected_closing_phrase='take care'
            - User: "Please hang up" → reason='user_hangup_request', detected_closing_phrase='hang up'
            - Full sequence completed → reason='natural_close'

            ❌ INVALID - DO NOT END:
            - User gave their name, phone number, or other info you asked for
            - User said "no" to YOUR question (this is an ANSWER, not a goodbye)
            - User said "thanks" alone (say "You're welcome! Anything else?")
            - Silence or pause (wait for user)
            """
            logger.info(f"end_call attempt: reason={reason}, phrase='{detected_closing_phrase}', goodbye={already_said_goodbye}")

            # Get user messages from transcript
            user_messages = [m for m in self._transcript_log if m.get("role") == "user"]

            # VALIDATION 1: Minimum conversation length (prevent ending on first exchange)
            if len(user_messages) < 2:
                logger.warning(f"end_call REJECTED: only {len(user_messages)} user message(s)")
                return "ERROR: Conversation too short to end. Ask 'Is there anything else I can help with?' and wait for their response."

            last_user_msg = user_messages[-1].get("content", "") if user_messages else ""

            # VALIDATION 2: Validate based on reason
            if reason == "user_goodbye":
                is_farewell, detected = is_farewell_closing(last_user_msg)
                if not is_farewell:
                    logger.warning(f"end_call REJECTED: no farewell closing in '{last_user_msg[:60]}'")
                    return f"ERROR: User's last message was '{last_user_msg[:50]}' - this is NOT a goodbye. Say 'Thanks for calling! Is there anything else?' and WAIT for them to say bye."
                logger.info(f"end_call APPROVED: user_goodbye with '{detected}'")

            elif reason == "user_hangup_request":
                if not is_hangup_request(last_user_msg):
                    logger.warning(f"end_call REJECTED: no hangup request in '{last_user_msg[:60]}'")
                    return "ERROR: User didn't explicitly ask to hang up. Continue the conversation."
                logger.info("end_call APPROVED: user_hangup_request")

            elif reason == "natural_close":
                if not detect_closing_sequence(self._transcript_log):
                    logger.warning("end_call REJECTED: no proper closing sequence detected")
                    return "ERROR: No proper closing sequence found. You need: 1) Ask 'anything else?' 2) User says no 3) You say thanks. If you haven't done all these, keep talking."

                # For natural close, user's last message should be acknowledgment or farewell
                if not is_soft_close_ack(last_user_msg) and not is_farewell_closing(last_user_msg)[0]:
                    logger.warning(f"end_call REJECTED: last message not acknowledgment: '{last_user_msg[:60]}'")
                    return "ERROR: User hasn't acknowledged your goodbye yet. Wait for them to respond with 'thanks', 'you too', 'bye', etc."
                logger.info("end_call APPROVED: natural_close sequence complete")

            else:
                logger.warning(f"end_call REJECTED: invalid reason '{reason}'")
                return f"ERROR: Invalid reason '{reason}'. Must be 'user_goodbye', 'natural_close', or 'user_hangup_request'."

            # === VALIDATION PASSED - Proceed with ending the call ===
            logger.info(f"end_call EXECUTING: reason={reason}")

            # Log the validated end call event
            self._transcript_log.append({
                "role": "system",
                "content": f"Call ended: {reason}" + (f" (detected: '{detected_closing_phrase}')" if detected_closing_phrase else ""),
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

            return f"Call ended successfully: {reason}"

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
