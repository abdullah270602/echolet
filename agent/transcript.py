"""
Transcript capture module for the voice agent.
Handles capturing and logging agent/user speech.
"""

import logging
import time
from typing import AsyncIterable

from livekit.agents import Agent, ModelSettings

logger = logging.getLogger(__name__)


def create_dynamic_assistant(
    instructions: str,
    transcript_log: list[dict],
) -> type[Agent]:
    """
    Factory function to create a DynamicAssistant class with transcript logging.

    Args:
        instructions: System instructions for the agent
        transcript_log: Shared list to append agent messages to

    Returns:
        A DynamicAssistant class configured with the given instructions
    """

    class DynamicAssistant(Agent):
        def __init__(self) -> None:
            super().__init__(instructions=instructions)
            self._transcript_log = transcript_log

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
