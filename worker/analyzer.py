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
from prompt import build_analysis_prompt, get_enabled_field_keys

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


async def analyze_transcript(
    transcript: list[dict[str, Any]],
    output_config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Analyze a call transcript using the LLM.

    Args:
        transcript: List of message dicts with role/content
        output_config: Optional output configuration from agent_configs.config.output
                      Controls which fields are extracted

    Returns:
        Dict with analysis fields based on output config (defaults to all fields)
    """
    enabled_keys = get_enabled_field_keys(output_config)

    if not transcript:
        result = get_default_analysis(output_config)
        result["summary"] = "Empty call - no conversation recorded."
        return result

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not configured")
        result = get_default_analysis(output_config)
        result["summary"] = "Analysis unavailable - API key not configured."
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

            # Build result with only enabled fields, validated
            result = {}

            # Summary is always included
            result["summary"] = str(llm_result.get("summary", "No summary available."))[:1000]

            # Validate and include only enabled fields
            if "intent" in enabled_keys:
                category = llm_result.get("category", "Other")
                result["category"] = category if category in VALID_CATEGORIES else "Other"

            if "priority" in enabled_keys:
                urgency = llm_result.get("urgency", "Medium")
                result["urgency"] = urgency if urgency in VALID_URGENCIES else "Medium"

            if "sentiment" in enabled_keys:
                sentiment = llm_result.get("sentiment", "Neutral")
                result["sentiment"] = sentiment if sentiment in VALID_SENTIMENTS else "Neutral"

            if "follow_up_required" in enabled_keys:
                result["action_required"] = bool(llm_result.get("action_required", False))

            if "action_items" in enabled_keys:
                result["action_items"] = [str(item) for item in llm_result.get("action_items", [])][:10]

            return result

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")

    # Fallback response
    result = get_default_analysis(output_config)
    result["summary"] = "Analysis failed - please review transcript manually."
    return result
