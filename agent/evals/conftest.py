"""
Behavioural evals for the voice agent.

Each eval runs the production agent (real prompt builder, real end_call tool, real
LLM via OpenRouter) in LiveKit's text mode, then checks the reply with hard rules
and, where wording varies, an LLM judge. They cost real tokens, so they are not
part of the unit suite: run with `cd agent && uv run pytest evals`.
"""

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from livekit.agents import AgentSession  # noqa: E402
from livekit.plugins import openai  # noqa: E402

from config import LLM_BASE_URL, LLM_MODEL  # noqa: E402
from database import SessionConfig  # noqa: E402
from demo import skip_analysis_queue, skip_save_call_log  # noqa: E402
from prompts import build_prompts_from_config  # noqa: E402
# end_call deletes the LiveKit room; there is no room in text mode, so make sure
# that call can't reach a real LiveKit project (it fails fast and is logged).
os.environ["LIVEKIT_URL"] = ""
# (Set after config.py, whose load_dotenv(override=True) would restore it.)
from transcript import create_dynamic_assistant  # noqa: E402

# Same persona as the landing-page demo and new users' starter agent.
# tests/unit/backend/test_eval_fixture.py fails if this drifts from the backend template.
CLINIC_CONFIG = json.loads((Path(__file__).parent / "clinic_config.json").read_text())

JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", LLM_MODEL)

if not os.getenv("OPENROUTER_API_KEY"):
    pytest.skip("OPENROUTER_API_KEY not set; evals call a real LLM", allow_module_level=True)


def _llm(model: str) -> openai.LLM:
    return openai.LLM(api_key=os.environ["OPENROUTER_API_KEY"], base_url=LLM_BASE_URL, model=model)


class Call:
    """One simulated call. `say()` is a caller turn; returns LiveKit's RunResult."""

    def __init__(self, session: AgentSession, transcript: list[dict], judge_llm: openai.LLM):
        self.session = session
        self.transcript = transcript
        self.judge_llm = judge_llm

    async def say(self, text: str):
        # In audio mode the STT handler records caller turns; end_call's
        # "conversation too short" guard reads them, so record them here too.
        self.transcript.append({"role": "user", "content": text, "timestamp": time.time()})
        return await self.session.run(user_input=text)

    async def judge(self, result, intent: str) -> str:
        """Assert the agent's final reply this turn meets `intent`; returns all reply text.

        A turn can contain several assistant messages (e.g. around a tool call); the
        last one is what the caller is left with, so that is what gets judged.
        """
        last = max(
            (i for i, e in enumerate(result.events) if e.type == "message" and e.item.role == "assistant"),
            default=None,
        )
        assert last is not None, "agent did not reply"
        await result.expect[last].is_message(role="assistant").judge(self.judge_llm, intent=intent)
        return reply_text(result)


def reply_text(result) -> str:
    return " ".join(
        e.item.text_content or ""
        for e in result.events
        if e.type == "message" and e.item.role == "assistant"
    )


def called(result, tool: str) -> bool:
    return any(e.type == "function_call" and e.item.name == tool for e in result.events)


@pytest.fixture
async def call():
    session_config = SessionConfig(session_id=0, agent_id=0, user_id="", config=CLINIC_CONFIG)
    # Evaluate the agent as it runs for a real business (calls are saved).
    prompts = build_prompts_from_config(session_config, saved=True)
    transcript: list[dict] = []
    Assistant = create_dynamic_assistant(
        instructions=prompts.system_instructions,
        transcript_log=transcript,
        room_name="eval",
        session_start_time=time.time(),
        save_call_log_fn=skip_save_call_log,
        send_to_queue_fn=skip_analysis_queue,
        cleanup_done={"value": False},
    )
    async with _llm(LLM_MODEL) as agent_llm, _llm(JUDGE_MODEL) as judge_llm, AgentSession(llm=agent_llm) as session:
        await session.start(Assistant())
        yield Call(session, transcript, judge_llm)


# --- Run tracking -------------------------------------------------------------
# Each run of the dataset writes results/<UTC timestamp>.json: pass rate overall and
# per category, the failing case ids with the reason, and the model under test.

import datetime as _dt
import subprocess as _sp
from collections import defaultdict as _dd

_outcomes: dict[str, tuple[str, str]] = {}


def pytest_runtest_logreport(report):
    if "test_dataset.py" in report.nodeid and (report.when == "call" or report.outcome != "passed"):
        msg = ""
        if report.failed:
            crash = getattr(report.longrepr, "reprcrash", None)  # the assertion itself, not context
            msg = (crash.message if crash else str(report.longrepr).splitlines()[-1])[:400]
        _outcomes[report.nodeid] = (report.outcome, msg)


def pytest_sessionfinish(session):
    if hasattr(session.config, "workerinput") or not _outcomes:
        return  # xdist workers report to the controller; nothing ran from the dataset
    by_cat = _dd(lambda: [0, 0])
    failures = []
    for nodeid, (outcome, msg) in sorted(_outcomes.items()):
        case_id = nodeid.split("[", 1)[-1].rstrip("]")
        cat = case_id.split(".")[1]
        by_cat[cat][1] += 1
        if outcome == "passed":
            by_cat[cat][0] += 1
        else:
            failures.append({"case": case_id, "reason": msg})
    passed = sum(p for p, _ in by_cat.values())
    total = sum(t for _, t in by_cat.values())
    try:
        commit = _sp.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(__file__).parent / "results" / f"{stamp}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "run_at": stamp,
        "commit": commit,
        "model": LLM_MODEL,
        "judge": JUDGE_MODEL,
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 3) if total else None,
        "by_category": {k: {"passed": p, "total": t} for k, (p, t) in sorted(by_cat.items())},
        "failures": failures,
    }, indent=2) + "\n", encoding="utf-8")


# --- Demo mode: the landing-page agent with the demo calendar --------------------

@pytest.fixture
async def demo_call():
    """(Call, DemoCalendar) for the public demo: calendar tools, nothing saved."""
    from demo_calendar import CALENDAR_PROMPT, DemoCalendar, calendar_tools

    session_config = SessionConfig(session_id=0, agent_id=0, user_id="", config=CLINIC_CONFIG)
    prompts = build_prompts_from_config(session_config, saved=False)
    cal = DemoCalendar(CLINIC_CONFIG)
    transcript: list[dict] = []
    Assistant = create_dynamic_assistant(
        instructions=prompts.system_instructions + CALENDAR_PROMPT,
        transcript_log=transcript,
        room_name="eval-demo",
        session_start_time=time.time(),
        save_call_log_fn=skip_save_call_log,
        send_to_queue_fn=skip_analysis_queue,
        cleanup_done={"value": False},
        tools=calendar_tools(cal),
    )
    async with _llm(LLM_MODEL) as agent_llm, _llm(JUDGE_MODEL) as judge_llm, AgentSession(llm=agent_llm) as session:
        await session.start(Assistant())
        yield Call(session, transcript, judge_llm), cal
