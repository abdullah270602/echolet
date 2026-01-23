"""
Prompt builder - Combines system prompts with user configuration.

This module is responsible for merging:
- System prompts (voice rules, guardrails, ending logic) - from system.py
- User configuration (name, business, tone, knowledge base) - from database

Users only configure their business-specific content.
System handles all technical behavior automatically.
"""

from dataclasses import dataclass
from typing import Optional

from .system import SYSTEM_PROMPT, FALLBACK_SYSTEM_PROMPT


# Tone descriptions - maps tone keys to natural language descriptions
TONE_DESCRIPTIONS = {
    "professional": "formal, business-like, and respectful",
    "friendly": "warm, approachable, and conversational",
    "urgent": "direct, action-oriented, and concise",
}


@dataclass
class DynamicPrompts:
    """Prompts built from agent configuration."""

    system_instructions: str
    greeting_instructions: str


def build_prompts(
    name: str,
    business_name: str,
    tone: str,
    custom_instructions: Optional[str],
    knowledge_base_text: Optional[str],
    greeting_message: str,
) -> DynamicPrompts:
    """
    Build complete agent prompts by merging system prompts with user configuration.

    System prompts (automatically included):
    - Voice rules (short sentences, no lists, etc.)
    - Base guardrails (don't invent info, etc.)
    - Task definition (help caller, ask anything else)
    - Call ending logic (when/how to end calls)

    User configuration (passed as arguments):
    - name: Agent's display name
    - business_name: Business the agent represents
    - tone: Conversation style (professional, friendly, urgent)
    - custom_instructions: Additional behavior rules
    - knowledge_base_text: Business-specific information
    - greeting_message: Initial greeting to say

    Returns:
        DynamicPrompts with system_instructions and greeting_instructions
    """
    tone_desc = TONE_DESCRIPTIONS.get(tone, "professional and helpful")

    # === USER-CONFIGURABLE SECTIONS ===

    role_section = f"""
<role>
You are {name}, a warm, helpful receptionist for {business_name}.
You are currently on a PHONE CALL. This is VOICE, not text.
</role>
"""

    knowledge_section = f"""
<business_context>
{knowledge_base_text or "No specific business information provided."}
</business_context>
"""

    style_section = f"""
<conversation_style>
Your tone is {tone_desc}.
If the user is angry, lower your energy and slow down.
If the user is happy, match their energy.
Keep responses brief and natural - this is a phone call, not an essay.
</conversation_style>
"""

    # Optional custom instructions (user's additional rules)
    custom_section = ""
    if custom_instructions:
        custom_section = f"""
<additional_instructions>
{custom_instructions}
</additional_instructions>
"""

    # === COMBINE: User context first, then system rules ===
    # Order matters for LLM attention - user context provides the "who/what"
    # System rules provide the "how" (behavior constraints)

    full_instructions = f"""
{role_section}
{knowledge_section}
{style_section}
{custom_section}
{SYSTEM_PROMPT}
""".strip()

    return DynamicPrompts(
        system_instructions=full_instructions,
        greeting_instructions=f"Say exactly this greeting: '{greeting_message}'",
    )


# === FALLBACK PROMPTS ===
# Used when session configuration cannot be loaded

FALLBACK_INSTRUCTIONS = f"""
<role>
You are a helpful Echolet voice AI assistant.
You are currently on a PHONE CALL. This is VOICE, not text.
</role>

{FALLBACK_SYSTEM_PROMPT}
""".strip()

FALLBACK_GREETING = (
    "Say: Hello! I'm having trouble loading my configuration. Please try reconnecting."
)

# Legacy constants for backward compatibility
ASSISTANT_INSTRUCTIONS = FALLBACK_INSTRUCTIONS

GREETING_INSTRUCTIONS = "Say: Hey, I'm Echolet Agent. How can I help you today?"

FAREWELL_MESSAGE = (
    "You've reached your daily talk limit. "
    "Thanks for chatting today - see you tomorrow!"
)
