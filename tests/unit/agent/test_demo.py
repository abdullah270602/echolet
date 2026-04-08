"""Voice agent: trusting demo-call metadata from the signed LiveKit token."""

import importlib.util
import json
import os

import pytest

# Load agent/demo.py by path: backend, agent and worker all have modules with the
# same names (config, database), so a plain import could pick the wrong service.
_spec = importlib.util.spec_from_file_location(
    "agent_demo", os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent", "demo.py")
)
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)


def _meta(**overrides):
    data = {"demo": True, "max_seconds": 120, "config": {"agent": {"name": "Emma"}}}
    data.update(overrides)
    return json.dumps(data)


def test_room_prefix():
    assert demo.is_demo_room("demo-1234")
    assert not demo.is_demo_room("5f0c-uuid-room")


def test_valid_metadata():
    config, cap = demo.parse_demo_metadata(_meta())
    assert config == {"agent": {"name": "Emma"}}
    assert cap == 120


def test_cap_is_clamped_to_ceiling():
    _, cap = demo.parse_demo_metadata(_meta(max_seconds=99999))
    assert cap == demo.DEMO_MAX_SECONDS_CEILING


@pytest.mark.parametrize("metadata", [
    "",
    "not json",
    "[]",
    _meta(demo=False),
    _meta(max_seconds=0),
    _meta(max_seconds="abc"),
    _meta(config="nope"),
    json.dumps({"demo": True, "max_seconds": 60}),
])
def test_invalid_metadata_is_rejected(metadata):
    assert demo.parse_demo_metadata(metadata) is None


@pytest.mark.asyncio
async def test_demo_persistence_is_noop():
    assert await demo.skip_save_call_log(room_name="demo-1", transcript=[]) is True
    assert await demo.skip_analysis_queue("demo-1") is None
