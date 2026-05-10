"""The agent evals run against a JSON copy of the starter agent; keep it in sync."""

import json
from pathlib import Path

from app.agent_templates.default import DEFAULT_AGENT_CONFIG

FIXTURE = Path(__file__).resolve().parents[3] / "agent" / "evals" / "clinic_config.json"


def test_eval_fixture_matches_starter_agent():
    assert json.loads(FIXTURE.read_text()) == DEFAULT_AGENT_CONFIG.model_dump(mode="json"), (
        "agent/evals/clinic_config.json is stale; regenerate it from "
        "backend/app/agent_templates/default.py"
    )
