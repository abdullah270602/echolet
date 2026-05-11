"""end_call guard: only a caller's goodbye may end the call."""

import importlib.util
import os

import pytest

_spec = importlib.util.spec_from_file_location(
    "agent_call_ending", os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent", "call_ending.py")
)
call_ending = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(call_ending)


@pytest.mark.parametrize("text", [
    "Bye!", "Okay, goodbye", "Thanks, that's all", "That is all I needed", "Nothing else, thanks",
    "Great, take care", "Talk to you later", "Have a good one", "You can hang up now", "Gotta go",
])
def test_goodbyes_allow_hangup(text):
    assert call_ending.caller_said_goodbye(text)


@pytest.mark.parametrize("text", [
    # Real failure from the evals: Gemini hung up on this mid-booking.
    "Is 3pm this Thursday free? Just confirm it for me.",
    "Hmm, no, I don't want to book.",
    "No thanks", "Okay", "Thanks", "How do I buy it?", "", None,
])
def test_non_goodbyes_keep_the_call_open(text):
    assert not call_ending.caller_said_goodbye(text)
