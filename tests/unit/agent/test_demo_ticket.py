"""Demo ticket: prompt building and tolerant parsing of the model reply."""

import importlib.util
import json
import os

_spec = importlib.util.spec_from_file_location(
    "agent_demo_ticket",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent", "demo_ticket.py"),
)
dt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dt)

CFG = {"agent": {"name": "Emma", "business_name": "Brightside Dental"}}
GOOD = {"caller": "Dana", "phone": "555 0142", "about": "Cleaning", "wants": "Thursday pm",
        "mood": "Positive", "todo": ["Text a slot"], "summary": "Dana wants a cleaning."}


def test_messages_include_transcript_and_null_rule():
    msgs = dt.build_ticket_messages(
        [{"role": "agent", "content": "Hi"}, {"role": "user", "content": "I need a cleaning"}], CFG
    )
    assert "Emma: Hi" in msgs[1]["content"]
    assert "Caller: I need a cleaning" in msgs[1]["content"]
    assert "null" in msgs[0]["content"] and "Never invent" in msgs[0]["content"]
    assert "Brightside Dental" in msgs[0]["content"]


def test_parse_clean_and_fenced():
    assert dt.parse_ticket(json.dumps(GOOD)) == GOOD
    assert dt.parse_ticket("Sure!\n```json\n" + json.dumps(GOOD) + "\n```") == GOOD


def test_parse_garbage_falls_back():
    for bad in ["", "no json here", "{broken", "[1,2]", None]:
        t = dt.parse_ticket(bad)
        assert t["caller"] is None and t["todo"] == []


def test_trims_and_coerces():
    t = dt.parse_ticket(json.dumps({**GOOD, "about": "x" * 500, "phone": 5550142, "caller": ["Dana"],
                                    "mood": "null", "todo": ["a", 3, "", "b", "c", "d"]}))
    assert len(t["about"]) == 120
    assert t["phone"] == "5550142"
    assert t["caller"] is None and t["mood"] is None
    assert t["todo"] == ["a", "b", "c"]


def test_todo_string_becomes_list():
    assert dt.parse_ticket(json.dumps({**GOOD, "todo": "Call back"}))["todo"] == ["Call back"]
