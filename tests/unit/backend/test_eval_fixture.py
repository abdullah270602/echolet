"""Copies of the starter agent config (evals, Vercel demo function) must match the source."""

import json
from pathlib import Path

from app.agent_templates.default import DEFAULT_AGENT_CONFIG

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = DEFAULT_AGENT_CONFIG.model_dump(mode="json")


def test_eval_fixture_matches_starter_agent():
    fixture = ROOT / "agent" / "evals" / "clinic_config.json"
    assert json.loads(fixture.read_text()) == EXPECTED, (
        f"{fixture} is stale; regenerate it from backend/app/agent_templates/default.py"
    )


def test_vercel_demo_config_matches_starter_agent():
    """The Vercel demo function ships its own copy of the demo persona."""
    src = (ROOT / "frontend" / "api" / "_clinic_config.js").read_text()
    body = src[src.index("export default ") + len("export default "):].rstrip().rstrip(";")
    assert json.loads(body) == EXPECTED, (
        "frontend/api/_clinic_config.js is stale; regenerate it from the backend template"
    )
