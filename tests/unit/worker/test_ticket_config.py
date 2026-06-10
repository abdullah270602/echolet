"""Worker builds its prompt/validation from the agent's configured ticket fields."""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "worker"))

from analyzer import analyze_transcript, build_result  # noqa: E402
from prompt import build_analysis_prompt  # noqa: E402

CONFIG = {
    "ticket_fields": [
        {"id": "customer_name", "label": "Customer Name", "type": "string", "required": True},
        {"id": "call_summary", "label": "Call Summary", "type": "text", "required": True},
        {"id": "priority", "label": "Priority", "type": "select",
         "options": ["low", "medium", "high", "urgent"]},
        {"id": "phone_number", "label": "Phone Number", "type": "string"},
        {"id": "timestamp", "label": "Timestamp", "type": "datetime"},
        {"id": "call_duration", "label": "Call Duration", "type": "number"},
        {"id": "budget", "label": "Budget", "type": "number"},
        {"id": "sentiment", "label": "Sentiment", "type": "select",
         "options": ["positive", "neutral", "negative"], "enabled": False},
    ],
    "custom_tags": ["vip_customer", "emergency"],
}


def test_prompt_includes_labels_options_required_and_tags():
    p = build_analysis_prompt(CONFIG)
    assert '"customer_name": "Customer Name (Required)' in p
    assert '"priority": "Priority (Optional). One of [\'low\', \'medium\', \'high\', \'urgent\']' in p
    assert '"budget": "Budget (Optional). Number' in p
    assert "['vip_customer', 'emergency']" in p
    assert '"sentiment"' not in p  # disabled


def test_prompt_never_asks_llm_for_call_data_fields():
    p = build_analysis_prompt(CONFIG)
    assert '"timestamp"' not in p and '"call_duration"' not in p
    assert "Never invent" in p  # phone number guidance


def test_defaults_prompt_uses_default_ticket_fields():
    p = build_analysis_prompt({})
    for key in ("customer_name", "phone_number", "priority", "sentiment", "intent", "action_items"):
        assert f'"{key}"' in p
    assert "'positive', 'neutral', 'negative'" in p


def test_unknown_select_value_becomes_null():
    r = build_result({"summary": "x", "priority": "critical"}, CONFIG)
    assert r["fields"]["priority"] is None


def test_select_matches_case_insensitively_and_maps_to_legacy_column():
    r = build_result({"summary": "x", "priority": "URGENT"}, CONFIG)
    assert r["fields"]["priority"] == "urgent"
    assert r["urgency"] == "Urgent"


def test_wrong_types_null_or_coerced():
    r = build_result({"summary": "x", "budget": "1500", "customer_name": ["a"]}, CONFIG)
    assert r["fields"]["budget"] == 1500.0
    assert r["fields"]["customer_name"] is None
    assert build_result({"budget": "lots"}, CONFIG)["fields"]["budget"] is None
    assert build_result({"budget": True}, CONFIG)["fields"]["budget"] is None


def test_call_data_fields_come_from_call_not_llm():
    r = build_result(
        {"summary": "x", "timestamp": "1999-01-01T00:00:00", "call_duration": 9999},
        CONFIG,
        {"timestamp": "2026-05-01T10:00:00", "duration_seconds": 42},
    )
    assert r["fields"]["timestamp"] == "2026-05-01T10:00:00"
    assert r["fields"]["call_duration"] == 42
    # without call data they are null, never the LLM's value
    r = build_result({"timestamp": "1999-01-01T00:00:00", "call_duration": 9999}, CONFIG)
    assert r["fields"]["timestamp"] is None and r["fields"]["call_duration"] is None


def test_tags_limited_to_configured_list():
    r = build_result({"tags": ["emergency", "made_up", "emergency"]}, CONFIG)
    assert r["tags"] == ["emergency"]
    assert build_result({"tags": ["emergency"]}, {})["tags"] == []  # no tags configured


def test_disabled_field_absent_but_summary_always_present():
    r = build_result({"sentiment": "positive"}, CONFIG)
    assert "sentiment" not in r["fields"] and "sentiment" not in r
    assert r["summary"]


@pytest.mark.asyncio
async def test_defaults_still_produce_ticket_with_legacy_columns():
    reply = {"summary": "Caller booked.", "customer_name": "Sam", "priority": "high",
             "sentiment": "positive", "intent": "appointment", "action_items": ["Call back"],
             "follow_up_required": True}
    resp = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": json.dumps(reply)}}]}
    with patch("analyzer.OPENROUTER_API_KEY", "k"), patch("httpx.AsyncClient") as http:
        post = AsyncMock(return_value=resp)
        http.return_value.__aenter__.return_value.post = post
        r = await analyze_transcript([{"role": "user", "content": "hi"}], {},
                                     call_data={"timestamp": "t", "duration_seconds": 5})
    assert (r["summary"], r["urgency"], r["sentiment"], r["category"]) == (
        "Caller booked.", "High", "Positive", "Appointment")
    assert r["action_required"] is True and r["action_items"] == ["Call back"]
    assert r["fields"]["customer_name"] == "Sam" and r["fields"]["call_duration"] == 5
    assert "customer_name" in post.call_args.kwargs["json"]["messages"][0]["content"]


def test_hostile_values_cannot_poison_storage():
    import json
    import analyzer

    assert analyzer.coerce_value({"type": "number"}, float("nan")) is None
    assert analyzer.coerce_value({"type": "number"}, "inf") is None
    assert analyzer.coerce_value({"type": "number"}, "12.5") == 12.5
    assert "\x00" not in analyzer.coerce_value({"type": "text"}, "a\x00b")
    assert all("\x00" not in v for v in analyzer.coerce_value({"type": "array"}, ["x\x00", "y"]))
    json.dumps({"n": analyzer.coerce_value({"type": "number"}, 3)}, allow_nan=False)
