"""The agent eval dataset is valid, and the validator catches bad cases. No LLM calls."""

import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "eval_dataset", os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent", "evals", "dataset.py")
)
dataset = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dataset)


def _case(**over):
    case = {
        "id": "knowledge-price-01",
        "category": "knowledge",
        "turns": ["How much is a cleaning?"],
        "judge": "States that a cleaning costs $120.",
        "source": "test",
        "batch": 1,
    }
    case.update(over)
    return case


def test_committed_dataset_is_valid():
    cases = dataset.load()
    assert dataset.validate(cases) == []


def test_valid_case_passes():
    assert dataset.validate([_case(must_include_any=["120"], end_call=False)]) == []


def test_catches_bad_cases():
    bad = [
        _case(id="Bad Id"),
        _case(id="x-1", category="nonsense"),
        _case(id="x-2", turns=[]),
        _case(id="x-3", judge="ok"),
        _case(id="x-4", end_call="yes"),
        _case(id="x-5", must_include_any=[]),
        _case(id="x-6", extra_field=1),
    ]
    problems = dataset.validate(bad)
    for fragment in ["kebab-case", "unknown category", "turns", "too short", "end_call", "must_include_any", "unknown fields"]:
        assert any(fragment in p for p in problems), fragment


def test_catches_duplicate_ids_and_duplicate_caller_lines():
    problems = dataset.validate([
        _case(id="a-1"),
        _case(id="a-1", turns=["Something else entirely?"]),
        _case(id="a-2", turns=["how much is a CLEANING"]),
    ])
    assert any("duplicate id" in p for p in problems)
    assert any("same caller lines" in p for p in problems)
