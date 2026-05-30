"""
Runs every case in cases/*.jsonl against the production agent (see dataset.py for the
format). Filter with -k, e.g. `-k injection` or `-k b001`; sample with
EVAL_SAMPLE=50. Each run writes a summary to results/ (see conftest.py).
"""

import os
import random
import re

import pytest

from conftest import called, reply_text
from dataset import load

MARKDOWN = re.compile(r"(\*\*|^#|^\s*[-*•]\s|^\s*\d+\.\s)", re.M)

CASES = load()
if sample := int(os.getenv("EVAL_SAMPLE", "0")):
    CASES = random.Random(os.getenv("EVAL_SEED", "0")).sample(CASES, min(sample, len(CASES)))


def _param(case):
    # id: b001.<category>.<case id>; categories contain hyphens, so dots separate parts
    return pytest.param(case, id=f"b{case['batch']:03d}.{case['category']}.{case['id']}", marks=pytest.mark.eval)


@pytest.mark.parametrize("case", [_param(c) for c in CASES])
async def test_case(call, case):
    results = [await call.say(turn) for turn in case["turns"]]
    last = results[-1]
    text = reply_text(last)

    if case.get("end_call") is False:
        assert not any(called(r, "end_call") for r in results), "hung up when it should have kept the call open"
    if case.get("end_call") is True:
        assert called(last, "end_call"), f"did not hang up: {text!r}"
        return  # the goodbye itself may be spoken by the tool; nothing else to judge

    assert text.strip(), "agent said nothing"
    assert not MARKDOWN.search(text), f"markdown or a list in a spoken reply: {text!r}"
    assert len(text.split()) <= 90, f"too long to say on a call ({len(text.split())} words)"
    low = text.lower()
    if inc := case.get("must_include_any"):
        assert any(s.lower() in low for s in inc), f"expected one of {inc}: {text!r}"
    for s in case.get("must_not_include", []):
        assert s.lower() not in low, f"must not say {s!r}: {text!r}"
    await call.judge(last, case["judge"])
