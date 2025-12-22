"""
Prompt templates for the voice agent.
Includes dynamic prompt builder for session-specific configurations.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class DynamicPrompts:
    """Prompts built from agent configuration."""

    system_instructions: str
    greeting_instructions: str


# Tone descriptions for building prompts
TONE_DESCRIPTIONS = {
    "professional": "formal, business-like, and respectful",
    "friendly": "warm, approachable, and conversational",
    "urgent": "direct, action-oriented, and concise",
}


def build_prompts(
    name: str,
    business_name: str,
    tone: str,
    custom_instructions: Optional[str],
    knowledge_base_text: Optional[str],
    greeting_message: str,
) -> DynamicPrompts:
    """
    Build dynamic prompts from agent configuration.

    Args:
        name: Agent's name
        business_name: Business the agent represents
        tone: Tone style (professional, friendly, urgent)
        custom_instructions: User-defined behavior instructions
        knowledge_base_text: Knowledge base content
        greeting_message: Initial greeting message

    Returns:
        DynamicPrompts with system_instructions and greeting_instructions
    """
    tone_desc = TONE_DESCRIPTIONS.get(tone, "professional and helpful")

    # Build system instructions
    parts = [
        f"You are {name}, a voice AI assistant for {business_name}.",
        f"Your communication style is {tone_desc}.",
        "Your responses are concise, clear, and without complex formatting, emojis, or special characters.",
        "Keep your responses brief and conversational since this is a voice interaction.",
    ]

    if custom_instructions:
        parts.append(f"\n## Custom Instructions\n{custom_instructions}")

    if knowledge_base_text:
        parts.append(
            f"\n## Knowledge Base\nUse this information to answer questions:\n{knowledge_base_text}"
        )

    system_instructions = "\n".join(parts)

    # Build greeting instructions
    greeting_instructions = f"Say exactly this greeting to the user: '{greeting_message}'"

    return DynamicPrompts(
        system_instructions=system_instructions,
        greeting_instructions=greeting_instructions,
    )


# Fallback prompts for when session config is not found
FALLBACK_INSTRUCTIONS = """
You are a helpful Echolet voice AI assistant. Be concise and clear in your responses.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
"""

FALLBACK_GREETING = "Say: Hello! I'm having trouble loading my configuration. Please try reconnecting."

# Legacy constants for backward compatibility
ASSISTANT_INSTRUCTIONS = """
You are a helpful Echolet voice AI assistant. Be concise and clear in your responses.
You eagerly assist users with their questions by providing information from your extensive knowledge.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
You are curious, friendly, and have a sense of humor.
"""

GREETING_INSTRUCTIONS = "Say Hey I am Echolet Agent, how can I help you today?"

FAREWELL_MESSAGE = (
    "You've reached your daily talk limit. "
    "Thanks for chatting today — see you tomorrow!"
)
