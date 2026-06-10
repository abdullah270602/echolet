"""
Dynamic Prompt Builder for Call Analysis

Builds the analysis prompt from the agent's configured ticket fields
(agent_configs.config.output): label, type, options, required, plus custom_tags.
"""

from typing import Any

# Mirror of backend/app/schemas/agent.py DEFAULT_TICKET_FIELDS (the worker cannot
# import the backend). Used when an agent has no ticket fields configured.
DEFAULT_TICKET_FIELDS: list[dict[str, Any]] = [
    {"id": "customer_name", "label": "Customer Name", "type": "string", "required": True},
    {"id": "phone_number", "label": "Phone Number", "type": "string", "required": True},
    {"id": "call_summary", "label": "Call Summary", "type": "text", "required": True},
    {"id": "timestamp", "label": "Timestamp", "type": "datetime", "required": True},
    {"id": "priority", "label": "Priority", "type": "select", "options": ["low", "medium", "high", "urgent"]},
    {"id": "sentiment", "label": "Sentiment", "type": "select", "options": ["positive", "neutral", "negative"]},
    {"id": "intent", "label": "Intent", "type": "select",
     "options": ["appointment", "inquiry", "complaint", "support", "other"]},
    {"id": "action_items", "label": "Action Items", "type": "array"},
    {"id": "follow_up_required", "label": "Follow-up Required", "type": "boolean"},
    {"id": "call_duration", "label": "Call Duration", "type": "number"},
]

# Ticket field id -> legacy call_sessions column / worker key.
LEGACY_KEYS = {
    "call_summary": "summary",
    "priority": "urgency",
    "sentiment": "sentiment",
    "intent": "category",
    "follow_up_required": "action_required",
    "action_items": "action_items",
}

# Fields filled from the call record, never asked of the LLM.
CALL_DATA_FIELDS = {"timestamp", "call_duration"}

# Extra guidance for well-known field ids.
HINTS = {
    "customer_name": "The caller's name if they gave it, else null.",
    "phone_number": "Only a phone number the caller explicitly said in the transcript. Never invent or infer one; null if not said.",
    "call_summary": "1 sentence starting with the caller's name (or 'Caller'); focus on the core request.",
    "priority": "Emergency, money on the table, angry customer or immediate service needed means higher priority; general info, spam or wrong number means lower.",
    "sentiment": "The caller's mood toward the business.",
    "action_items": "Only tasks for the business owner; not things the AI already did.",
    "follow_up_required": "True if a human must follow up.",
}


def get_ticket_fields(output_config: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Enabled fields from config (defaults if none configured). call_summary is always present."""
    configured = (output_config or {}).get("ticket_fields") or []
    fields = [f for f in configured if f.get("id")] or DEFAULT_TICKET_FIELDS
    fields = [f for f in fields if f.get("enabled", True)]
    if not any(f["id"] == "call_summary" for f in fields):
        fields.insert(0, {"id": "call_summary", "label": "Call Summary", "type": "text", "required": True})
    return fields


def describe_field(field: dict[str, Any]) -> str:
    """One JSON-structure line for a field, built from its label/type/options/required."""
    t = field.get("type", "string")
    if t == "select":
        kind = f"One of {field.get('options') or []}, or null"
    elif t == "number":
        kind = "Number, or null"
    elif t == "boolean":
        kind = "Boolean"
    elif t == "array":
        kind = "Array of strings"
    elif t == "datetime":
        kind = "ISO 8601 datetime, or null"
    else:
        kind = "String, or null"
    req = "Required" if field.get("required") else "Optional"
    hint = HINTS.get(field["id"])
    return f'  "{field["id"]}": "{field.get("label", field["id"])} ({req}). {kind}.{" " + hint if hint else ""}"'


def llm_fields(output_config: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [f for f in get_ticket_fields(output_config) if f["id"] not in CALL_DATA_FIELDS]


def build_analysis_prompt(output_config: dict[str, Any] | None = None) -> str:
    """Build the analysis prompt from the configured ticket fields and tags."""
    lines = [describe_field(f) for f in llm_fields(output_config)]
    tags = (output_config or {}).get("custom_tags") or []
    if tags:
        lines.append(f'  "tags": "Array of strings. Only tags from this list that clearly apply: {tags}. Use [] if none."')
    json_structure = "{\n" + ",\n".join(lines) + "\n}"

    return f"""
You are an expert Call Analyst for "Echolet," an AI receptionist service.
Your job is to analyze transcripts of phone calls between an AI agent and a human caller.

You must extract structured data to help the business owner quickly triage the call.

### OUTPUT FORMAT
Return valid JSON only. Do not use Markdown code blocks (```json). Do not add conversational text.
Use null for anything not determinable from the transcript; never invent values.
Select fields must use exactly one of the listed options.
Structure:
{json_structure}

### INPUT TRANSCRIPT
"""


def get_enabled_field_keys(output_config: dict[str, Any] | None = None) -> dict[str, str]:
    """Map enabled legacy-column field ids to their column keys (e.g. {"priority": "urgency"})."""
    return {f["id"]: LEGACY_KEYS[f["id"]] for f in get_ticket_fields(output_config) if f["id"] in LEGACY_KEYS}


# Legacy constant for backward compatibility
ANALYSIS_SYSTEM_PROMPT = build_analysis_prompt()
