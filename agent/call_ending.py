"""
Deterministic guard for the end_call tool.

The prompt tells the model to hang up only after an explicit goodbye, but the
behavioural evals (evals/test_receptionist.py) showed Gemini calling end_call
mid-booking. Hanging up on a customer is the worst failure a receptionist can
have, so the tool itself refuses unless the caller's latest words close the call.
"""

import re

# ponytail: English phrase list. A goodbye we don't recognise means the agent stays
# on the line until the caller hangs up, which is the safe direction to fail.
_GOODBYE = re.compile(
    r"\b(bye|goodbye|good night|see (you|ya)|take care|talk (to you )?(soon|later)|"
    r"gotta go|got to go|have a (good|great|nice) (one|day|night|evening|weekend)|"
    r"that'?s all|that is all|that'?s it|nothing else|no,? that'?s (everything|fine)|"
    r"hang up|end (the|this) call)\b",
    re.I,
)


def caller_said_goodbye(text: str) -> bool:
    return bool(_GOODBYE.search(text or ""))
