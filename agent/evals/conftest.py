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
    prompts = build_prompts_from_config(session_config)
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
