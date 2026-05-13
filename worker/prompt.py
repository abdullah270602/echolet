"""
Dynamic Prompt Builder for Call Analysis

Builds analysis prompts based on enabled output fields from agent config.
"""

from typing import Any


# Field definitions with their prompt descriptions and validation
FIELD_DEFINITIONS = {
    "call_summary": {
        "json_key": "summary",
        "description": '"summary": "String. 1 sentence starting with the caller\'s name (or \'Caller\'). Focus on the *core request*."',
        "required": True,  # Always required
    },
    "priority": {
        "json_key": "urgency",
        "description": '"urgency": "String. One of: [\'High\', \'Medium\', \'Low\']"',
        "definitions": """**Urgency:**
   - "High": Emergency, money on the table, angry customer, or immediate service needed (e.g., "Pipe burst").
   - "Medium": Specific questions, appointment requests, or callbacks requested.
   - "Low": General info, spam, or wrong number.""",
    },
    "sentiment": {
        "json_key": "sentiment",
        "description": '"sentiment": "String. One of: [\'Positive\', \'Neutral\', \'Frustrated\', \'Angry\']"',
        "definitions": """**Sentiment:**
   - Distinguish between "Frustrated" (annoyed by bot/process) and "Angry" (mad at business).""",
    },
    "intent": {
        "json_key": "category",
        "description": '"category": "String. One of: [\'Appointment\', \'Inquiry\', \'Complaint\', \'Spam\', \'Urgent Service\', \'Other\']"',
    },
    "follow_up_required": {
        "json_key": "action_required",
        "description": '"action_required": "Boolean. True if a human must follow up."',
    },
    "action_items": {
        "json_key": "action_items",
        "description": '"action_items": ["String", "String"]',
        "definitions": """**Action Items:**
   - Only list tasks for the *Business Owner* (e.g., "Call back to confirm price").
   - Do NOT list tasks the AI already completed (e.g., "AI answered the question").""",
    },
}


def build_analysis_prompt(output_config: dict[str, Any] = None) -> str:
    """
    Build the analysis prompt based on enabled output fields.

    Args:
        output_config: The output configuration from agent_configs.config.output
                      Contains 'ticket_fields' list with enabled/disabled fields

    Returns:
        Complete analysis prompt string
    """
    if output_config is None:
        output_config = {}

    ticket_fields = output_config.get("ticket_fields", [])

    # Determine which fields are enabled
    enabled_fields = set()
    for field in ticket_fields:
        if field.get("enabled", True):
            enabled_fields.add(field.get("id"))

    # If no fields configured, use defaults (all enabled)
    if not enabled_fields:
        enabled_fields = {"call_summary", "priority", "sentiment", "intent", "follow_up_required", "action_items"}

    # Always include summary
    enabled_fields.add("call_summary")

    # Build JSON structure section
    json_fields = []
    definitions = []

    for field_id, field_def in FIELD_DEFINITIONS.items():
        if field_id in enabled_fields:
            json_fields.append(f"  {field_def['description']}")
            if "definitions" in field_def:
                definitions.append(field_def["definitions"])

    json_structure = "{\n" + ",\n".join(json_fields) + "\n}"

    # Build definitions section
    definitions_text = ""
    if definitions:
        definitions_text = "\n\n### DEFINITIONS\n" + "\n\n".join(f"{i+1}. {d}" for i, d in enumerate(definitions))

    prompt = f"""
You are an expert Call Analyst for "Echolet," an AI receptionist service.
Your job is to analyze transcripts of phone calls between an AI agent and a human caller.

You must extract structured data to help the business owner quickly triage the call.

### OUTPUT FORMAT
Return valid JSON only. Do not use Markdown code blocks (```json). Do not add conversational text.
Structure:
{json_structure}{definitions_text}

### INPUT TRANSCRIPT
"""

    return prompt


def get_enabled_field_keys(output_config: dict[str, Any] = None) -> dict[str, str]:
    """
    Get mapping of enabled field IDs to their JSON keys.

    Args:
        output_config: The output configuration

    Returns:
        Dict mapping field_id to json_key (e.g., {"priority": "urgency"})
    """
    if output_config is None:
        output_config = {}

    ticket_fields = output_config.get("ticket_fields", [])

    enabled_fields = set()
    for field in ticket_fields:
        if field.get("enabled", True):
            enabled_fields.add(field.get("id"))

    # Default: all enabled
    if not enabled_fields:
        enabled_fields = {"call_summary", "priority", "sentiment", "intent", "follow_up_required", "action_items"}

    # Always include summary
    enabled_fields.add("call_summary")

    return {
        field_id: FIELD_DEFINITIONS[field_id]["json_key"]
        for field_id in enabled_fields
        if field_id in FIELD_DEFINITIONS
    }


# Legacy constant for backward compatibility
ANALYSIS_SYSTEM_PROMPT = build_analysis_prompt()