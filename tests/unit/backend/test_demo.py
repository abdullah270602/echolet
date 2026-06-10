"""The starter agent template (used for new agents and the landing-page demo)."""

from app.agent_templates.default import DEFAULT_AGENT_CONFIG
from app.schemas.agent import AgentConfigData


def test_default_agent_template_is_a_valid_config():
    assert AgentConfigData.model_validate(DEFAULT_AGENT_CONFIG.model_dump()) == DEFAULT_AGENT_CONFIG
