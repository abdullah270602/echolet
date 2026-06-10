"""
Call-flow pipeline tests (agent SQS -> worker -> analyzer).

boto3/SQS, the LLM HTTP call and the DB are mocked; this is not a true end-to-end run.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "worker"))


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user_id() -> uuid.UUID:
    """Test user UUID."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def clerk_id() -> str:
    """Test Clerk ID."""
    return "user_test123abc"


@pytest.fixture
def agent_id() -> int:
    """Test agent ID."""
    return 1


@pytest.fixture
def room_name() -> str:
    """Test room name (UUID)."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_transcript() -> list[dict]:
    """Complete conversation transcript."""
    base_time = 1700000000.0
    return [
        {"role": "agent", "content": "Hello! How can I help you today?", "timestamp": base_time},
        {"role": "user", "content": "I'd like to book an appointment.", "timestamp": base_time + 5},
        {"role": "agent", "content": "Sure! What day works best for you?", "timestamp": base_time + 10},
        {"role": "user", "content": "Tomorrow at 2pm please.", "timestamp": base_time + 15},
        {"role": "agent", "content": "I've noted that down. Is there anything else I can help with?", "timestamp": base_time + 20},
        {"role": "user", "content": "No, that's all. Thank you!", "timestamp": base_time + 25},
        {"role": "agent", "content": "You're welcome! Have a great day. Goodbye!", "timestamp": base_time + 30},
        {"role": "user", "content": "Bye!", "timestamp": base_time + 35},
    ]


@pytest.fixture
def sample_analysis() -> dict:
    """LLM analysis result."""
    return {
        "summary": "Caller requested an appointment booking for tomorrow at 2pm.",
        "category": "Appointment",
        "urgency": "Medium",
        "sentiment": "Positive",
        "action_required": True,
        "action_items": ["Confirm appointment for tomorrow 2pm"],
    }


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.scalar = AsyncMock()
    return session


# =============================================================================
# E2E TEST: HAPPY PATH - FULL CALL FLOW
# =============================================================================


class TestHappyPathCallFlow:
    """
    Pipeline test: agent SQS send -> worker poll -> process_message -> analyzer -> update_analysis.

    Real code: agent/sqs.py, worker poll_sqs/process_message, analyzer parsing and
    validation. Mocked: boto3/SQS client, the LLM HTTP call, and the DB
    (fetch_call_data/update_analysis). Not a true end-to-end run.
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_call_flow_happy_path(self, room_name, sample_transcript, sample_analysis):
        from sqs import send_to_analysis_queue
        from worker import poll_sqs, process_message

        # Agent enqueues the room for analysis
        with patch("sqs.SQS_QUEUE_URL", "https://sqs.test/queue"),              patch("sqs.boto3.client") as mock_boto:
            mock_boto.return_value.send_message.return_value = {"MessageId": "msg-123"}
            assert await send_to_analysis_queue(room_name) is True
            sent = mock_boto.return_value.send_message.call_args.kwargs
            assert json.loads(sent["MessageBody"])["room_name"] == room_name

        # Worker polls exactly what the agent sent
        sqs_client = MagicMock()
        sqs_client.receive_message.return_value = {
            "Messages": [{"MessageId": "msg-123", "ReceiptHandle": "r-1", "Body": sent["MessageBody"]}]
        }
        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            messages = poll_sqs(sqs_client)
        assert messages[0]["body"]["room_name"] == room_name

        # Worker analyses with the real analyzer (LLM HTTP mocked) and persists the result
        llm_response = MagicMock(status_code=200)
        llm_response.json.return_value = {"choices": [{"message": {"content": json.dumps(sample_analysis)}}]}
        with patch("worker.fetch_call_data", return_value={"transcript": sample_transcript, "output_config": {}}),              patch("analyzer.OPENROUTER_API_KEY", "test_key"),              patch("httpx.AsyncClient") as mock_http,              patch("worker.update_analysis", return_value=True) as update:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=llm_response)
            assert await process_message(messages[0]) is True

        kwargs = update.call_args.kwargs
        assert kwargs["room_name"] == room_name
        assert kwargs["category"] == "Appointment"
        assert kwargs["action_required"] is True
        assert kwargs["action_items"] == sample_analysis["action_items"]


# =============================================================================
# E2E TEST: ABNORMAL DISCONNECT
# =============================================================================


class TestAbnormalDisconnectFlow:
    """
    E2E Test: Call drops unexpectedly.

    Flow:
    1. Call in progress
    2. User disconnects abruptly (no goodbye)
    3. Agent's finally block saves transcript
    4. SQS message sent for analysis
    5. Analysis completes with partial data
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_analysis_runs_on_partial_transcript(self):
        """Analysis of a transcript cut off mid-sentence still returns a valid result."""

        # Partial transcript (no farewell)
        partial_transcript = [
            {"role": "agent", "content": "Hello! How can I help?", "timestamp": 1700000000.0},
            {"role": "user", "content": "I have a question about--", "timestamp": 1700000005.0},
            # Call drops here
        ]

        # === Analysis still runs on partial data ===
        from analyzer import analyze_transcript

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), \
             patch("httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": json.dumps({
                    "summary": "Call disconnected before completion.",
                    "category": "Other",
                    "urgency": "Low",
                    "sentiment": "Neutral",
                    "action_required": False,
                    "action_items": [],
                })}}]
            }
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            analysis = await analyze_transcript(partial_transcript)
            assert analysis["category"] == "Other"


# =============================================================================
# E2E TEST: ERROR RECOVERY
# =============================================================================


class TestErrorRecovery:
    """
    E2E Test: System recovers from failures.
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_llm_failure_uses_fallback(self, sample_transcript):
        """E2E: LLM failure returns valid fallback analysis."""
        from analyzer import analyze_transcript

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), \
             patch("httpx.AsyncClient") as mock_http:
            # LLM returns error
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("LLM unavailable")
            )

            analysis = await analyze_transcript(sample_transcript)

            # Fallback values returned
            assert analysis is not None
            assert analysis["category"] in {"Other", "Inquiry"}
            assert "failed" in analysis["summary"].lower() or "error" in analysis["summary"].lower() or analysis["summary"] == "Analysis pending"
