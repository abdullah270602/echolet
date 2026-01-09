"""
LLM Transcript Analyzer

Uses OpenRouter (Gemini) to analyze call transcripts and extract:
- Summary: What happened in the call
- Category: Type of call (Appointment, Inquiry, Complaint, etc.)
- Urgency: Priority level (High, Medium, Low)
- Sentiment: Caller mood (Positive, Neutral, Frustrated, Angry)
- Action Required: Whether human follow-up is needed
- Action Items: Specific tasks for follow-up
"""

import json
import logging
from typing import Any

import httpx

from config import OPENROUTER_API_KEY, LLM_BASE_URL, LLM_MODEL
from prompt import ANALYSIS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def format_transcript(transcript: list[dict[str, Any]]) -> str:
    """Format transcript messages for the LLM prompt."""
    lines = []
    for msg in transcript:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        lines.append(f"[{role}]: {content}")
    return "\n".join(lines)


def get_default_analysis() -> dict[str, Any]:
    """Return default analysis when processing fails."""
    return {
        "summary": "Analysis pending.",
        "category": "Other",
        "urgency": "Medium",
        "sentiment": "Neutral",
        "action_required": False,
        "action_items": [],
    }


# Valid values for validation
VALID_CATEGORIES = {"Appointment", "Inquiry", "Complaint", "Spam", "Urgent Service", "Other"}
VALID_URGENCIES = {"High", "Medium", "Low"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Frustrated", "Angry"}


async def analyze_transcript(transcript: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze a call transcript using the LLM.

    Args:
        transcript: List of message dicts with role/content

    Returns:
        Dict with summary, category, urgency, sentiment, action_required, action_items
    """
    if not transcript:
        result = get_default_analysis()
        result["summary"] = "Empty call - no conversation recorded."
        return result

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not configured")
        result = get_default_analysis()
        result["summary"] = "Analysis unavailable - API key not configured."
        return result

    formatted_transcript = format_transcript(transcript)
    full_prompt = ANALYSIS_SYSTEM_PROMPT + formatted_transcript

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

            result = json.loads(content.strip())

            # Validate and sanitize each field
            category = result.get("category", "Other")
            urgency = result.get("urgency", "Medium")
            sentiment = result.get("sentiment", "Neutral")

            return {
                "summary": str(result.get("summary", "No summary available."))[:1000],
                "category": category if category in VALID_CATEGORIES else "Other",
                "urgency": urgency if urgency in VALID_URGENCIES else "Medium",
                "sentiment": sentiment if sentiment in VALID_SENTIMENTS else "Neutral",
                "action_required": bool(result.get("action_required", False)),
                "action_items": [str(item) for item in result.get("action_items", [])][:10],
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")

    # Fallback response
    result = get_default_analysis()
    result["summary"] = "Analysis failed - please review transcript manually."
    return result
