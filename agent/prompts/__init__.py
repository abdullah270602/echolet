"""
Agent prompts module.

This module provides prompt building functionality with clean separation between:
- System prompts (technical behavior - voice rules, guardrails, call ending)
- User content (business-specific - name, knowledge base, custom instructions)

Usage:
    from prompts import build_prompts, DynamicPrompts

    prompts = build_prompts(
        name="Sarah",
        business_name="Acme Corp",
        tone="professional",
        custom_instructions="Always offer callbacks",
        knowledge_base_text="Our hours are 9-5...",
        greeting_message="Hi! Thanks for calling Acme Corp!",
    )

    # prompts.system_instructions contains the full prompt
    # prompts.greeting_instructions contains the greeting directive
"""

from .builder import (
    DynamicPrompts,
    build_prompts,
    TONE_DESCRIPTIONS,
    FALLBACK_INSTRUCTIONS,
    FALLBACK_GREETING,
    ASSISTANT_INSTRUCTIONS,
    GREETING_INSTRUCTIONS,
    FAREWELL_MESSAGE,
)

from .system import (
    SYSTEM_PROMPT,
    FALLBACK_SYSTEM_PROMPT,
    VOICE_RULES,
    BASE_GUARDRAILS,
    TASK_DEFINITION,
    CALL_ENDING_RULES,
)

__all__ = [
    # Main builder
    "build_prompts",
    "DynamicPrompts",
    "TONE_DESCRIPTIONS",
    # Fallbacks
    "FALLBACK_INSTRUCTIONS",
    "FALLBACK_GREETING",
    # Legacy compatibility
    "ASSISTANT_INSTRUCTIONS",
    "GREETING_INSTRUCTIONS",
    "FAREWELL_MESSAGE",
    # System prompts (for advanced use/testing)
    "SYSTEM_PROMPT",
    "FALLBACK_SYSTEM_PROMPT",
    "VOICE_RULES",
    "BASE_GUARDRAILS",
    "TASK_DEFINITION",
    "CALL_ENDING_RULES",
]
