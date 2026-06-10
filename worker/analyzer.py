"""
LLM Transcript Analyzer

Uses OpenRouter (Gemini) to analyze call transcripts and extract
configurable fields based on the agent's output configuration:
- Summary: What happened in the call
- Category: Type of call (Appointment, Inquiry, Complaint, etc.)
- Urgency: Priority level (High, Medium, Low)
- Sentiment: Caller mood (Positive, Neutral, Frustrated, Angry)
- Action Required: Whether human follow-up is needed
- Action Items: Specific tasks for follow-up
"""

import json
import logging
from typing import Any, Optional

import httpx

from config import OPENROUTER_API_KEY, LLM_BASE_URL, LLM_MODEL
from datetime import datetime

from prompt import (
    LEGACY_KEYS,
    build_analysis_prompt,
    get_enabled_field_keys,
    get_ticket_fields,
)

logger = logging.getLogger(__name__)


def format_transcript(transcript: list[dict[str, Any]]) -> str:
    """Format transcript messages for the LLM prompt."""
    lines = []
    for msg in transcript:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        lines.append(f"[{role}]: {content}")
    return "\n".join(lines)


def get_default_analysis(output_config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Return default analysis when processing fails."""
    enabled_keys = get_enabled_field_keys(output_config)

    defaults = {
        "summary": "Analysis pending.",
        "category": "Other",
        "urgency": "Medium",
        "sentiment": "Neutral",
        "action_required": False,
        "action_items": [],
    }

    # Only return fields that are enabled
    result = {}
    for field_id, json_key in enabled_keys.items():
        if json_key in defaults:
            result[json_key] = defaults[json_key]

    # Always include summary
    if "summary" not in result:
        result["summary"] = defaults["summary"]

    return result


# Valid values for validation
VALID_CATEGORIES = {"Appointment", "Inquiry", "Complaint", "Spam", "Urgent Service", "Other"}
VALID_URGENCIES = {"High", "Medium", "Low"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Frustrated", "Angry"}


def _match_option(value: Any, options: list[str]) -> Optional[str]:
    """Case-insensitive match against configured options; None if not in the set."""
    if isinstance(value, str):
        for opt in options:
            if value.strip().lower() == str(opt).lower():
                return opt
    return None


def coerce_value(field: dict[str, Any], value: Any) -> Any:
    """Coerce an LLM value to the field's configured type; None if it doesn't fit."""
    if value is None:
        return None
    t = field.get("type", "string")
    if t == "select":
        return _match_option(value, field.get("options") or [])
    if t in ("string", "text"):
        ok = isinstance(value, (str, int, float)) and not isinstance(value, bool)
        return str(value)[:1000] if ok else None
    if t == "number":
        if isinstance(value, bool):
            return None
        try:
            return value if isinstance(value, (int, float)) else float(value)
        except (TypeError, ValueError):
            return None
    if t == "boolean":
        if isinstance(value, bool):
            return value
        return {"true": True, "false": False}.get(str(value).strip().lower())
    if t == "array":
        return [str(i) for i in value][:10] if isinstance(value, list) else None
    if t == "datetime":
        try:
            datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return str(value)
        except ValueError:
            return None
    return None


def build_result(
    llm_result: dict[str, Any],
    output_config: Optional[dict[str, Any]],
    call_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Validate an LLM reply against the configured fields.

    Returns the legacy column keys (summary, category, urgency, sentiment,
    action_required, action_items; select options title-cased so the dashboard
    renders them, falling back to defaults when the LLM value is invalid), plus:
      "fields": {field_id: validated value} for every enabled field
      "tags": subset of custom_tags
    ponytail: call_sessions has no JSON column for "fields"/"tags", so they are
    returned but not persisted until one is added.
    """
    call_data = call_data or {}
    defaults = get_default_analysis(output_config)
    result: dict[str, Any] = {}
    fields: dict[str, Any] = {}

    for f in get_ticket_fields(output_config):
        fid = f["id"]
        if fid == "timestamp":
            fields[fid] = call_data.get("timestamp")
        elif fid == "call_duration":
            fields[fid] = call_data.get("duration_seconds")
        else:
            # Accept the legacy key too (older prompts/LLM habits).
            raw = llm_result.get(fid, llm_result.get(LEGACY_KEYS.get(fid, fid)))
            fields[fid] = coerce_value(f, raw)

        legacy = LEGACY_KEYS.get(fid)
        if legacy:
            v = fields[fid]
            if fid == "call_summary":
                result[legacy] = v or "No summary available."
            elif f.get("type") == "select":
                result[legacy] = v.title() if v else defaults.get(legacy)
            elif fid == "follow_up_required":
                result[legacy] = bool(v)
            else:
                result[legacy] = v if v is not None else defaults.get(legacy)

    allowed = (output_config or {}).get("custom_tags") or []
    raw_tags = llm_result.get("tags")
    tags = [t for t in raw_tags if t in allowed] if isinstance(raw_tags, list) else []
    result["fields"] = fields
    result["tags"] = list(dict.fromkeys(tags))
    return result


async def analyze_transcript(
    transcript: list[dict[str, Any]],
    output_config: Optional[dict[str, Any]] = None,
    call_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Analyze a call transcript using the LLM.

    Args:
        transcript: List of message dicts with role/content
        output_config: Optional output configuration from agent_configs.config.output
                      Controls which fields are extracted
        call_data: Optional {"timestamp", "duration_seconds"} from the call record;
                   fills the timestamp / call_duration fields (never taken from the LLM)

    Returns:
        Dict with analysis fields based on output config (defaults to all fields)
    """
    if not transcript:
        result = get_default_analysis(output_config)
        result["summary"] = "Empty call - no conversation recorded."
        return result

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not configured")
        result = get_default_analysis(output_config)
        result["summary"] = "Analysis unavailable - API key not configured."
        result["failed"] = True
        return result

    # Build dynamic prompt based on enabled fields
    analysis_prompt = build_analysis_prompt(output_config)
    formatted_transcript = format_transcript(transcript)
    full_prompt = analysis_prompt + formatted_transcript

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.3,
                },
            )

            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]

            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            llm_result = json.loads(content.strip())
            if not isinstance(llm_result, dict):
                raise json.JSONDecodeError("expected a JSON object", content, 0)
            return build_result(llm_result, output_config, call_data)

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")

    # Fallback response
    result = get_default_analysis(output_config)
    result["summary"] = "Analysis failed - please review transcript manually."
    result["failed"] = True  # a placeholder, not a result: the worker must not persist it
    return result
