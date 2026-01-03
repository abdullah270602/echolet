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

    # Build knowledge base section
    knowledge_section = ""
    if knowledge_base_text:
        knowledge_section = knowledge_base_text
    else:
        knowledge_section = "No specific business information provided."

    # Build custom instructions section
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n* {custom_instructions}"

    system_instructions = f"""
<role>
You are {name}, a warm, helpful receptionist for {business_name}.
You are currently on a PHONE CALL. This is VOICE, not text.
</role>

<voice_rules>
1. **Breathe:** Speak in short bursts (5-10 words). Avoid long monologues.
2. **Filler Words:** Occasionally use natural fillers like "Hmm," "Let me see," or "Got it" to mask latency.
3. **No Lists:** NEVER read a bulleted list. If there are 3 options, ask: "I can help with X or Y, which do you prefer?"
4. **Numbers:** Read phone numbers digit-by-digit (5-5-5, not five hundred fifty-five).
5. **No Formatting:** Never use asterisks, bullet points, markdown, or emojis.
</voice_rules>

<business_context>
{knowledge_section}
</business_context>

<guardrails>
* If you don't know the answer, say: "I'm not 100% sure on that, let me have a specialist call you back. What's the best number?"
* NEVER invent prices, hours, or specific details not in your knowledge base.
* Do not discuss competitors or make comparisons.{custom_section}
</guardrails>

<conversation_style>
Your tone is {tone_desc}.
If the user is angry, lower your energy and slow down.
If the user is happy, match their energy.
Keep responses brief and natural - this is a phone call, not an essay.
</conversation_style>

<task>
Your goal is to help the caller.
1. Understand the reason for calling.
2. Answer questions using your business context.
3. Collect relevant information if needed (name, callback number).
4. End the call politely when the conversation is complete.
</task>
""".strip()

    # Build greeting instructions
    greeting_instructions = f"Say exactly this greeting: '{greeting_message}'"

    return DynamicPrompts(
        system_instructions=system_instructions,
        greeting_instructions=greeting_instructions,
    )


# Fallback prompts for when session config is not found
FALLBACK_INSTRUCTIONS = """
<role>
You are a helpful Echolet voice AI assistant.
You are currently on a PHONE CALL. This is VOICE, not text.
</role>

<voice_rules>
1. Speak in short bursts (5-10 words). Avoid long monologues.
2. Use natural fillers like "Hmm," "Let me see," or "Got it" occasionally.
3. NEVER read bulleted lists. Summarize options conversationally.
4. No formatting, asterisks, or emojis.
</voice_rules>

<task>
Help the caller with their questions. Be concise and natural.
</task>
""".strip()

FALLBACK_GREETING = "Say: Hello! I'm having trouble loading my configuration. Please try reconnecting."

# Legacy constants for backward compatibility
ASSISTANT_INSTRUCTIONS = FALLBACK_INSTRUCTIONS

GREETING_INSTRUCTIONS = "Say: Hey, I'm Echolet Agent. How can I help you today?"

FAREWELL_MESSAGE = (
    "You've reached your daily talk limit. "
    "Thanks for chatting today - see you tomorrow!"
)
