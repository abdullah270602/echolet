"""
Ticket for the landing-page demo call.

Turns the demo transcript into the same kind of "While you were out" slip the real
analysis worker produces. Kept free of agent config imports so it can be tested alone.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Field -> max length. Trims anything the model rambles on about.
_TEXT_FIELDS = {"caller": 60, "phone": 30, "about": 120, "wants": 80, "mood": 20, "summary": 200}
_TODO_MAX_ITEMS, _TODO_MAX_LEN = 3, 100

EMPTY_TICKET: dict[str, Any] = {**{k: None for k in _TEXT_FIELDS}, "todo": []}


def build_ticket_messages(transcript: list[dict], config: dict) -> list[dict]:
    """Chat messages asking for a strict-JSON ticket for this call."""
    agent = config.get("agent", {}) if isinstance(config, dict) else {}
    business = agent.get("business_name") or agent.get("company") or "the business"
    name = agent.get("name") or "the receptionist"
    lines = "\n".join(
        f"{'Caller' if m.get('role') == 'user' else name}: {m.get('content', '')}"
        for m in transcript
        if m.get("content")
    )
    system = (
        f"You write the message slip a receptionist leaves after a call to {business}. "
        "Reply with ONLY a JSON object, no code fences, with these keys: "
        '"caller" (caller\'s name or null), "phone" (phone number or null), '
        '"about" (the service or reason for calling), '
        '"wants" (the day/time they asked for or null), '
        '"mood" (one word), '
        '"todo" (list of 1 to 3 short action items for the front desk), '
        '"summary" (one sentence). '
        "Use only what the caller actually said. If the caller did not say something, "
        "use null. Never invent names, numbers, times or services."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Call transcript:\n{lines}"},
    ]


def _clean(value: Any, limit: int) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    if not value or value.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    return value[:limit]


def parse_ticket(text: str) -> dict[str, Any]:
    """Parse the model reply into a safe ticket. Garbage gives the empty ticket."""
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return dict(EMPTY_TICKET, todo=[])
    ticket: dict[str, Any] = {k: _clean(data.get(k), n) for k, n in _TEXT_FIELDS.items()}
    todo = data.get("todo")
    if isinstance(todo, str):
        todo = [todo]
    items = (_clean(t, _TODO_MAX_LEN) for t in todo if isinstance(t, str)) if isinstance(todo, list) else ()
    ticket["todo"] = [t for t in items if t][:_TODO_MAX_ITEMS]
    return ticket


async def generate_ticket(transcript: list[dict], config: dict) -> dict[str, Any]:
    """Ask the LLM for the ticket. Raises on API errors; the caller handles them."""
    from openai import AsyncOpenAI

    from config import LLM_BASE_URL, LLM_MODEL, OPENROUTER_API_KEY

    client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=LLM_BASE_URL, timeout=10)
    resp = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=build_ticket_messages(transcript, config),
        max_tokens=400,
        temperature=0,
    )
    return parse_ticket(resp.choices[0].message.content or "")
