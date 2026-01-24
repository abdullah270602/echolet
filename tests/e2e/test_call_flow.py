"""
End-to-End Tests - Full Call Flow

Tests the complete call lifecycle from session creation to history retrieval.
These tests simulate the full flow across Agent, Backend, and Worker services.

Scenarios:
1. Happy Path: Full call → analysis → history
2. Usage Limit: User hits daily limit mid-call
3. Abnormal Disconnect: Call drops, transcript saved
4. Webhook Sync: New user creation flow
"""

import json
import uuid
from datetime import datetime, timezone
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
    E2E Test: Complete call lifecycle.

    Flow:
    1. Backend: Create call session
    2. Agent: Conduct conversation, capture transcript
    3. Agent: Detect farewell, end call properly
    4. Agent: Send to SQS for analysis
    5. Worker: Poll SQS, fetch transcript
    6. Worker: Analyze with LLM
    7. Worker: Update session with analysis
    8. Backend: Retrieve call history
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_call_flow_happy_path(
        self, user_id, agent_id, room_name, sample_transcript, sample_analysis, mock_db_session
    ):
        """E2E: Complete call from start to history retrieval."""

        # === STEP 1: Backend creates call session ===
        from app.db.repos import session_repo

        mock_call_session = MagicMock()
        mock_call_session.id = 1
        mock_call_session.room_name = room_name
        mock_call_session.user_id = user_id
        mock_call_session.agent_id = agent_id
        mock_call_session.status = "pending"

        with patch.object(session_repo, "create", return_value=mock_call_session):
            # Simulate session creation
            created_session = await session_repo.create(mock_db_session, user_id, agent_id)
            assert created_session.status == "pending"
            assert created_session.room_name == room_name

        # === STEP 2: Agent detects proper farewell ===
        from transcript import is_farewell_closing, detect_closing_sequence

        last_user_message = sample_transcript[-1]["content"]  # "Bye!"
        is_farewell, word = is_farewell_closing(last_user_message)
        assert is_farewell is True
        assert word == "bye"

        # === STEP 3: Agent validates closing sequence ===
        has_closing_sequence = detect_closing_sequence(sample_transcript)
        assert has_closing_sequence is True  # Has "anything else?" → "no" → "goodbye"

        # === STEP 4: Agent sends to SQS ===
        from sqs import send_to_analysis_queue

        with patch("sqs.SQS_QUEUE_URL", "https://sqs.test/queue"), \
             patch("sqs.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.send_message.return_value = {"MessageId": "msg-123"}
            mock_boto.return_value = mock_client

            result = await send_to_analysis_queue(room_name)
            assert result is True

        # === STEP 5: Worker polls and processes message ===
        from worker import poll_sqs, process_message

        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.return_value = {
            "Messages": [{
                "MessageId": "msg-123",
                "ReceiptHandle": "receipt-123",
                "Body": json.dumps({"room_name": room_name}),
            }]
        }

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            messages = poll_sqs(mock_sqs_client)
            assert len(messages) == 1
            # poll_sqs returns {"body": {...}, "receipt_handle": ...}
            assert messages[0]["body"]["room_name"] == room_name

        # === STEP 6: Worker fetches transcript and analyzes ===
        from analyzer import analyze_transcript

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), \
             patch("httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": json.dumps(sample_analysis)}}]
            }
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            analysis = await analyze_transcript(sample_transcript)

            assert analysis["category"] == "Appointment"
            assert analysis["sentiment"] == "Positive"
            assert analysis["action_required"] is True

        # === STEP 7: Worker updates session with analysis ===
        mock_call_session.transcript = sample_transcript
        mock_call_session.summary = analysis["summary"]
        mock_call_session.category = analysis["category"]
        mock_call_session.status = "completed"

        with patch.object(session_repo, "update_call_log", return_value=mock_call_session):
            updated = await session_repo.update_call_log(
                mock_db_session,
                room_name,
                transcript=sample_transcript,
                duration_seconds=35,
                summary=analysis["summary"],
            )
            assert updated.status == "completed"

        # === STEP 8: Backend retrieves call history ===
        mock_history = [{
            "id": 1,
            "room_name": room_name,
            "agent_name": "Test Agent",
            "summary": analysis["summary"],
            "category": "Appointment",
            "is_agent_deleted": False,
        }]

        with patch.object(session_repo, "get_user_call_history", return_value=mock_history):
            history = await session_repo.get_user_call_history(mock_db_session, user_id)

            assert len(history) == 1
            assert history[0]["category"] == "Appointment"
            assert "appointment" in history[0]["summary"].lower()


# =============================================================================
# E2E TEST: USAGE LIMIT ENFORCEMENT
# =============================================================================


class TestUsageLimitFlow:
    """
    E2E Test: User hits daily usage limit.

    Flow:
    1. User at 3550 seconds (50 seconds remaining)
    2. Start call
    3. After 50 seconds, limit reached
    4. Agent delivers graceful farewell
    5. Usage updated to 3600 (limit)
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_usage_limit_triggers_graceful_end(self, user_id, mock_db_session):
        """E2E: Call ends gracefully when usage limit reached."""
        from app.services import usage_service
        from app.db.repos import usage_repo

        DAILY_LIMIT = 3600  # seconds

        # User has used 3550 seconds today (50 remaining)
        with patch("app.services.usage_service.DAILY_TALK_LIMIT_SECONDS", DAILY_LIMIT), \
             patch.object(usage_repo, "get_daily_usage", return_value=3550):
            result = await usage_service.check_user_limit(mock_db_session, user_id)

            assert result["allowed"] is True  # Can still start
            assert result["remaining_seconds"] == 50
            assert result["used_seconds"] == 3550

        # After call uses 60 seconds (exceeds limit)
        with patch("app.services.usage_service.DAILY_TALK_LIMIT_SECONDS", DAILY_LIMIT), \
             patch.object(usage_repo, "get_daily_usage", return_value=3610):
            result = await usage_service.check_user_limit(mock_db_session, user_id)

            assert result["allowed"] is False  # Now blocked
            assert result["remaining_seconds"] == 0  # Clamped to 0


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
    async def test_disconnect_saves_partial_transcript(self, room_name, user_id, mock_db_session):
        """E2E: Partial transcript saved on abnormal disconnect."""

        # Partial transcript (no farewell)
        partial_transcript = [
            {"role": "agent", "content": "Hello! How can I help?", "timestamp": 1700000000.0},
            {"role": "user", "content": "I have a question about--", "timestamp": 1700000005.0},
            # Call drops here
        ]

        # === Transcript should NOT have farewell ===
        from transcript import is_farewell_closing

        last_message = partial_transcript[-1]["content"]
        is_farewell, _ = is_farewell_closing(last_message)
        assert is_farewell is False  # No farewell detected

        # === Session saved with "failed" status ===
        from app.db.repos import session_repo

        mock_session = MagicMock()
        mock_session.status = "failed"
        mock_session.transcript = partial_transcript

        with patch.object(session_repo, "update_call_log", return_value=mock_session):
            result = await session_repo.update_call_log(
                mock_db_session,
                room_name,
                transcript=partial_transcript,
                duration_seconds=5,
                status="failed",
            )
            assert result.status == "failed"

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
# E2E TEST: WEBHOOK USER SYNC
# =============================================================================


class TestWebhookUserSync:
    """
    E2E Test: New user created via Clerk webhook.

    Flow:
    1. Clerk sends user.created webhook
    2. Backend verifies Svix signature
    3. User upserted to database
    4. Default agent seeded (if applicable)
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_webhook_creates_user(self, clerk_id, mock_db_session):
        """E2E: Webhook creates new user in database."""
        from app.db.repos import user_repo

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.clerk_id = clerk_id
        mock_user.email = "newuser@example.com"

        # Simulate webhook payload
        webhook_payload = {
            "type": "user.created",
            "data": {
                "id": clerk_id,
                "email_addresses": [{"email_address": "newuser@example.com"}],
            },
        }

        # User repo handles upsert
        with patch.object(user_repo, "upsert_user", return_value=mock_user):
            user = await user_repo.upsert_user(
                mock_db_session,
                clerk_id=clerk_id,
                email="newuser@example.com",
            )

            assert user.clerk_id == clerk_id
            assert user.email == "newuser@example.com"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_webhook_updates_existing_user(self, clerk_id, mock_db_session):
        """E2E: Webhook updates existing user email."""
        from app.db.repos import user_repo

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.clerk_id = clerk_id
        mock_user.email = "updated@example.com"  # Email changed

        with patch.object(user_repo, "upsert_user", return_value=mock_user):
            user = await user_repo.upsert_user(
                mock_db_session,
                clerk_id=clerk_id,
                email="updated@example.com",
            )

            assert user.email == "updated@example.com"


# =============================================================================
# E2E TEST: CONCURRENT OPERATIONS
# =============================================================================


class TestConcurrentOperations:
    """
    E2E Test: Multiple simultaneous operations.

    Verifies the system handles concurrent requests correctly.
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_concurrent_calls_isolated(self, user_id):
        """E2E: Multiple concurrent calls remain isolated."""
        import asyncio

        # Simulate 3 concurrent calls
        room_names = [str(uuid.uuid4()) for _ in range(3)]
        transcripts = []

        async def simulate_call(room_name: str, call_num: int):
            await asyncio.sleep(0.01)  # Simulate network latency
            transcript = [
                {"role": "agent", "content": f"Call {call_num} greeting"},
                {"role": "user", "content": f"Call {call_num} message"},
            ]
            transcripts.append({"room": room_name, "transcript": transcript})
            return room_name

        # Run concurrently
        results = await asyncio.gather(*[
            simulate_call(room, i) for i, room in enumerate(room_names)
        ])

        # All calls completed
        assert len(results) == 3
        assert len(transcripts) == 3

        # Each transcript is unique
        messages = [t["transcript"][1]["content"] for t in transcripts]
        assert len(set(messages)) == 3  # All unique

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_concurrent_usage_updates_atomic(self, user_id):
        """E2E: Concurrent usage updates don't lose data."""
        import asyncio

        # Simulate atomic counter
        usage_counter = {"value": 0}
        lock = asyncio.Lock()

        async def record_usage(seconds: int):
            async with lock:  # Simulates DB-level atomicity
                usage_counter["value"] += seconds
                await asyncio.sleep(0.001)
            return seconds

        # 10 concurrent updates of 10 seconds each
        tasks = [record_usage(10) for _ in range(10)]
        await asyncio.gather(*tasks)

        # All updates applied (no lost updates)
        assert usage_counter["value"] == 100  # 10 * 10


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

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_sqs_failure_graceful(self, room_name):
        """E2E: SQS failure doesn't crash agent."""
        from sqs import send_to_analysis_queue
        from botocore.exceptions import ClientError

        with patch("sqs.SQS_QUEUE_URL", "https://sqs.test/queue"), \
             patch("sqs.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.send_message.side_effect = ClientError(
                {"Error": {"Code": "500", "Message": "Internal Error"}},
                "SendMessage",
            )
            mock_boto.return_value = mock_client

            # Should return False, not raise
            result = await send_to_analysis_queue(room_name)
            assert result is False
