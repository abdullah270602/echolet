"""The agent never tells a caller something untrue about recording, and compliance switches work."""

import importlib
import os
import sys
import types

import pytest

AGENT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent")


@pytest.fixture(scope="module")
def builder():
    # builder.py does `from database import SessionConfig`; backend and worker also have a
    # `database` module, so stub it while importing the agent's prompts package.
    saved = {k: sys.modules.get(k) for k in ("database", "prompts", "prompts.builder", "prompts.system")}
    sys.modules["database"] = types.SimpleNamespace(SessionConfig=object)
    for k in ("prompts", "prompts.builder", "prompts.system"):
        sys.modules.pop(k, None)
    sys.path.insert(0, AGENT)
    try:
        yield importlib.import_module("prompts.builder")
    finally:
        sys.path.remove(AGENT)
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def _config(disclaimer):
    return types.SimpleNamespace(
        greeting_message="Hi, this is Emma.",
        guardrails={"compliance": {"call_recording_disclaimer": disclaimer}},
    )


def test_saved_calls_admit_recording_when_asked(builder):
    text = builder._build_guardrails_section({"compliance": {}}, saved=True)
    assert "transcribed and saved" in text
    assert "Never claim the call isn't recorded" in text


def test_disclaimer_switch_puts_notice_in_greeting_once(builder):
    assert builder._greeting(_config(True), saved=True) == f"Hi, this is Emma. {builder.RECORDING_NOTICE}"
    assert builder._greeting(_config(False), saved=True) == "Hi, this is Emma."


def test_demo_calls_never_claim_to_be_saved(builder):
    text = builder._build_guardrails_section({"compliance": {"call_recording_disclaimer": True}}, saved=False)
    assert "nothing from it is saved" in text
    assert "transcribed and saved" not in text
    assert builder._greeting(_config(True), saved=False) == "Hi, this is Emma."


def test_hipaa_or_gdpr_adds_privacy_rule(builder):
    section = builder._build_guardrails_section
    assert "Privacy:" not in section({"compliance": {}})
    assert "Privacy:" in section({"compliance": {"hipaa_mode": True}})
    assert "Privacy:" in section({"compliance": {"gdpr_mode": True}})
