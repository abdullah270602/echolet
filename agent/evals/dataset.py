"""
Eval dataset: loading, validation and stats. Plain Python, no LiveKit import, so the
unit test suite can validate every batch for free.

Each line of cases/batch-NNN.jsonl is one synthetic test case (invented callers, never
real call data):

{
  "id": "knowledge-price-cleaning-01",        unique, kebab-case
  "category": "knowledge",                     one of CATEGORIES
  "turns": ["Hi, how much is a cleaning?"],    caller lines, in order (1 to 4)
  "judge": "States that a check-up and cleaning costs $120.",   intent for the LLM judge,
                                               applied to the agent's last reply
  "must_include_any": ["120"],                 optional: last reply contains one of these
  "must_not_include": ["$"],                   optional: last reply contains none of these
  "end_call": false,                           optional: true = must hang up on the last turn,
                                               false = must not hang up on any turn
  "source": "synthetic",                       "synthetic" (generated) or "hand" (hand-written)
  "batch": 1
}

Checks against text are case-insensitive. Every reply is also checked to be speakable
(no markdown, not too long).
"""

import json
import re
from collections import Counter
from pathlib import Path

CASES_DIR = Path(__file__).parent / "cases"

CATEGORIES = {
    "knowledge": "Answers from the clinic's facts: prices, durations, hours, location, policies",
    "unknown": "Questions the knowledge base doesn't cover: must not invent an answer",
    "booking": "Booking requests: collects name, service and time; never confirms a slot itself",
    "medical-safety": "No diagnosis, medication or dosage advice",
    "emergency": "Dental emergencies get a same-day visit; serious injuries also emergency services",
    "injection": "Prompt injection, role-play and attempts to extract instructions",
    "off-topic": "Unrelated requests: politely redirects to the clinic",
    "privacy": "Requests for other patients' or staff's personal information",
    "hang-up": "When the agent must or must not end the call",
    "difficult-caller": "Angry, confused, rude or rambling callers",
    "identity": "Questions about who or what the agent is",
    "style": "Replies must be short, spoken-language, no lists or markdown",
}

REQUIRED = {"id", "category", "turns", "judge", "source", "batch"}
OPTIONAL = {"must_include_any", "must_not_include", "end_call"}
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load(paths=None) -> list[dict]:
    """All cases from cases/*.jsonl (or the given files), in file order."""
    cases = []
    for path in paths or sorted(CASES_DIR.glob("batch-*.jsonl")):
        for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                case = json.loads(line)
                case["_where"] = f"{Path(path).name}:{n}"
                cases.append(case)
    return cases


def validate(cases: list[dict]) -> list[str]:
    """Problems found, as human-readable strings. Empty means the dataset is valid."""
    problems = []
    seen_ids, seen_turns = {}, {}
    for c in cases:
        where = c.get("_where", c.get("id", "?"))
        keys = set(c) - {"_where"}
        if missing := REQUIRED - keys:
            problems.append(f"{where}: missing {sorted(missing)}")
            continue
        if extra := keys - REQUIRED - OPTIONAL:
            problems.append(f"{where}: unknown fields {sorted(extra)}")
        if not ID.match(str(c["id"])):
            problems.append(f"{where}: id {c['id']!r} is not kebab-case")
        if c["category"] not in CATEGORIES:
            problems.append(f"{where}: unknown category {c['category']!r}")
        turns = c["turns"]
        if not (isinstance(turns, list) and 1 <= len(turns) <= 4 and all(isinstance(t, str) and t.strip() for t in turns)):
            problems.append(f"{where}: turns must be 1-4 non-empty strings")
            continue
        if not (isinstance(c["judge"], str) and len(c["judge"].split()) >= 4):
            problems.append(f"{where}: judge intent is too short")
        for field in ("must_include_any", "must_not_include"):
            if field in c and not (isinstance(c[field], list) and c[field] and all(isinstance(x, str) and x for x in c[field])):
                problems.append(f"{where}: {field} must be a non-empty list of strings")
        if "end_call" in c and not isinstance(c["end_call"], bool):
            problems.append(f"{where}: end_call must be true or false")
        if c["id"] in seen_ids:
            problems.append(f"{where}: duplicate id (also {seen_ids[c['id']]})")
        seen_ids[c["id"]] = where
        key = " | ".join(_norm(t) for t in turns)
        if key in seen_turns:
            problems.append(f"{where}: same caller lines as {seen_turns[key]}")
        seen_turns[key] = where
    return problems


def stats(cases: list[dict]) -> str:
    """Markdown table of case counts per batch and category."""
    batches = sorted({c["batch"] for c in cases})
    cats = sorted({c["category"] for c in cases})
    by = Counter((c["batch"], c["category"]) for c in cases)
    head = "| Category | " + " | ".join(f"Batch {b}" for b in batches) + " | Total |"
    rows = [head, "|---|" + "---|" * (len(batches) + 1)]
    for cat in cats:
        counts = [by[(b, cat)] for b in batches]
        rows.append(f"| {cat} | " + " | ".join(map(str, counts)) + f" | {sum(counts)} |")
    totals = [sum(by[(b, c)] for c in cats) for b in batches]
    rows.append("| **Total** | " + " | ".join(f"**{t}**" for t in totals) + f" | **{sum(totals)}** |")
    return "\n".join(rows)


if __name__ == "__main__":
    import sys

    cases = load()
    issues = validate(cases)
    print(stats(cases) if cases else "No cases yet.")
    print(f"\n{len(cases)} cases, {len(issues)} problems")
    for p in issues:
        print(" -", p)
    sys.exit(1 if issues else 0)
