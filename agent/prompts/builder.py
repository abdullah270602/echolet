"""
Prompt builder - Combines system prompts with user configuration.

This module is responsible for merging:
- System prompts (voice rules, guardrails, ending logic) - from system.py
- User configuration (identity, services, knowledge, guardrails, etc.) - from database

Users configure their business-specific content.
System handles all technical behavior automatically.
"""

from dataclasses import dataclass
from typing import Optional, Any

from .system import SYSTEM_PROMPT, FALLBACK_SYSTEM_PROMPT
from database import SessionConfig


# Speaking style descriptions - maps style keys to natural language descriptions
SPEAKING_STYLE_DESCRIPTIONS = {
    "calm_professional": "calm, measured, and business-like",
    "friendly_casual": "warm, approachable, and conversational",
    "energetic": "upbeat, enthusiastic, and dynamic",
    "empathetic": "caring, understanding, and supportive",
}


@dataclass
class DynamicPrompts:
    """Prompts built from agent configuration."""

    system_instructions: str
    greeting_instructions: str


def build_prompts_from_config(config: SessionConfig, saved: bool = True) -> DynamicPrompts:
    """
    Build complete agent prompts from SessionConfig.

    Args:
        config: SessionConfig loaded from database with full JSONB config

    Returns:
        DynamicPrompts with system_instructions and greeting_instructions
    """
    sections = []

    # 1. Role section
    sections.append(_build_role_section(config))

    # 2. Services section (if any)
    if config.services:
        sections.append(_build_services_section(config.services))

    # 3. Knowledge base section
    knowledge_text = _build_knowledge_text(config.knowledge_base)
    if knowledge_text:
        sections.append(f"""
<business_context>
{knowledge_text}
</business_context>
""")

    # 4. Speaking style section
    speaking_style = config.voice.get("speaking_style", "calm_professional")
    style_desc = SPEAKING_STYLE_DESCRIPTIONS.get(speaking_style, "professional and helpful")
    sections.append(f"""
<conversation_style>
Your tone is {style_desc}.
If the user is angry, lower your energy and slow down.
If the user is happy, match their energy.
Keep responses brief and natural - this is a phone call, not an essay.
</conversation_style>
""")

    # 5. Guardrails section (if any)
    if config.guardrails:
        guardrails_section = _build_guardrails_section(config.guardrails, saved)
        if guardrails_section:
            sections.append(guardrails_section)

    # 6. Business hours awareness (if enabled)
    business_hours = config.conversation.get("business_hours", {})
    if business_hours.get("enabled"):
        sections.append(_build_business_hours_section(business_hours))

    # 7. Custom instructions (user-defined additional rules)
    if config.custom_instructions:
        sections.append(f"""
<additional_instructions>
{config.custom_instructions}
</additional_instructions>
""")

    # 8. System prompt (voice rules, ending behavior, etc.)
    sections.append(SYSTEM_PROMPT)

    # Combine all sections
    full_instructions = "\n".join(sections).strip()

    return DynamicPrompts(
        system_instructions=full_instructions,
        greeting_instructions=f"Say exactly this greeting: '{_greeting(config, saved)}'",
    )


RECORDING_NOTICE = "Just so you know, this call is transcribed and saved so we can follow up."


def _greeting(config: SessionConfig, saved: bool) -> str:
    """The opening line, with the recording notice when the business turned it on."""
    compliance = config.guardrails.get("compliance", {})
    if saved and compliance.get("call_recording_disclaimer"):
        return f"{config.greeting_message} {RECORDING_NOTICE}"
    return config.greeting_message


def _build_role_section(config: SessionConfig) -> str:
    """Build the role/identity section of the prompt."""
    return f"""
<role>
You are {config.name}, a warm, helpful receptionist for {config.business_name}.
You are currently on a PHONE CALL. This is VOICE, not text.
</role>
"""


def _build_services_section(services: list[dict[str, Any]]) -> str:
    """Build the services section of the prompt."""
    services_lines = []
    for service in services:
        name = service.get("name", "Unknown Service")
        price = service.get("price", "Contact for price")
        duration = service.get("duration_minutes")
        duration_str = f", {duration} minutes" if duration else ""
        services_lines.append(f"- {name}: {price}{duration_str}")

    return f"""
<services>
These are the ONLY services offered. If a caller asks about anything else (crowns,
braces, implants...), don't say it's offered; say you're not sure and offer a follow-up.
Services you can book or discuss:
{chr(10).join(services_lines)}

When discussing services:
- Be helpful about pricing and duration
- Offer to schedule appointments if asked
- Don't make up prices or durations not listed here
</services>
"""


def _build_knowledge_text(knowledge_base: dict[str, Any]) -> str:
    """Build knowledge text from all sources."""
    sources = knowledge_base.get("sources", [])
    if not sources:
        return ""

    text_parts = []
    for source in sources:
        source_type = source.get("type")
        name = source.get("name", "")

        if source_type == "text" and source.get("content"):
            text_parts.append(f"[{name}]\n{source['content']}")
        elif source_type == "website" and source.get("url"):
            text_parts.append(f"[{name}]\nRefer to: {source['url']}")

    return "\n\n".join(text_parts) if text_parts else ""


def _build_guardrails_section(guardrails: dict[str, Any], saved: bool = True) -> str:
    """Build the guardrails section, including the compliance switches.

    `saved` is whether this call is stored (false for landing-page demo calls), so the
    agent never tells a caller something untrue about recording.
    """
    allowed_topics = guardrails.get("allowed_topics", [])
    disallowed_topics = guardrails.get("disallowed_topics", [])
    compliance = guardrails.get("compliance", {})

    lines = ["<guardrails>"]

    if allowed_topics:
        lines.append(f"Topics you CAN discuss: {', '.join(allowed_topics)}")

    if disallowed_topics:
        lines.append(f"Topics to AVOID: {', '.join(disallowed_topics)}")
        lines.append("")
        lines.append("If asked about avoided topics:")
        lines.append("- First, try to naturally redirect the conversation to something you can help with")
        lines.append("- If they persist, politely say you're not able to discuss that topic")
        lines.append("- Offer to help with something else or connect them with someone who can help")

    lines.append("")
    if saved:
        lines.append(
            "Recording: this call is transcribed and saved so the business can follow up. "
            "If asked, say so plainly. Never claim the call isn't recorded."
        )
    else:
        lines.append(
            "Recording: this is a demo call and nothing from it is saved. If asked, say so plainly."
        )
    if compliance.get("hipaa_mode") or compliance.get("gdpr_mode"):
        lines.append(
            "Privacy: collect only what's needed to help (name, contact, reason for calling). "
            "Never confirm whether someone is a patient or share anyone else's details."
        )

    lines.append("</guardrails>")
    return "\n".join(lines)


def _build_business_hours_section(business_hours: dict[str, Any]) -> str:
    """Build the business hours awareness section."""
    timezone = business_hours.get("timezone", "your local time")
    schedule = business_hours.get("schedule", [])
    after_hours = business_hours.get("after_hours_behavior", "offer_callback")

    # Build schedule summary
    open_days = []
    for day_info in schedule:
        day = day_info.get("day", "")
        open_time = day_info.get("open")
        close_time = day_info.get("close")
        if open_time and close_time:
            open_days.append(f"{day}: {open_time} - {close_time}")

    schedule_text = "\n".join(open_days) if open_days else "Check with the business for hours"

    after_hours_text = ""
    if after_hours == "offer_callback":
        after_hours_text = "If someone calls outside business hours, offer to have someone call them back during business hours."
    elif after_hours == "voicemail":
        after_hours_text = "If someone calls outside business hours, offer to take a message."

    return f"""
<business_hours>
Business hours ({timezone}):
{schedule_text}

{after_hours_text}
</business_hours>
"""


# Legacy function for backward compatibility
def build_prompts(
    name: str,
    business_name: str,
    tone: str,
    custom_instructions: Optional[str],
    knowledge_base_text: Optional[str],
    greeting_message: str,
) -> DynamicPrompts:
    """
    Legacy function - builds prompts from individual parameters.

    Prefer using build_prompts_from_config() with SessionConfig.
    """
    # Map old tone to new speaking style
    tone_to_style = {
        "professional": "calm_professional",
        "friendly": "friendly_casual",
        "urgent": "energetic",
    }
    style = tone_to_style.get(tone, "calm_professional")
    style_desc = SPEAKING_STYLE_DESCRIPTIONS.get(style, "professional and helpful")

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
Your tone is {style_desc}.
If the user is angry, lower your energy and slow down.
If the user is happy, match their energy.
Keep responses brief and natural - this is a phone call, not an essay.
</conversation_style>
"""

    custom_section = ""
    if custom_instructions:
        custom_section = f"""
<additional_instructions>
{custom_instructions}
</additional_instructions>
"""

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
