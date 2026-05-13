"""
Agent prompts module.

This module provides prompt building functionality with clean separation between:
- System prompts (technical behavior - voice rules, guardrails, call ending)
- User content (business-specific - name, knowledge base, custom instructions)

Usage:
    from prompts import build_prompts_from_config, DynamicPrompts
    from database import SessionConfig

    # New recommended approach using SessionConfig
    prompts = build_prompts_from_config(session_config)

    # prompts.system_instructions contains the full prompt
    # prompts.greeting_instructions contains the greeting directive

Legacy Usage (for backward compatibility):
    from prompts import build_prompts, DynamicPrompts

    prompts = build_prompts(
        name="Sarah",
        business_name="Acme Corp",
        tone="professional",
        ...
    )
"""

from .builder import (
    DynamicPrompts,
    build_prompts_from_config,
    build_prompts,  # Legacy
    SPEAKING_STYLE_DESCRIPTIONS,
    FALLBACK_INSTRUCTIONS,
    FALLBACK_GREETING,
    ASSISTANT_INSTRUCTIONS,
    GREETING_INSTRUCTIONS,
    FAREWELL_MESSAGE,
)

from .system import (
    SYSTEM_PROMPT,
    FALLBACK_SYSTEM_PROMPT,
    VOICE_STYLE,
    CORE_BEHAVIOR,
    GUARDRAILS,
    CALL_ENDING,
)

__all__ = [
    # Main builder (new)
    "build_prompts_from_config",
    "DynamicPrompts",
    "SPEAKING_STYLE_DESCRIPTIONS",
    # Legacy builder
    "build_prompts",
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
    "VOICE_STYLE",
    "CORE_BEHAVIOR",
    "GUARDRAILS",
    "CALL_ENDING",
]
