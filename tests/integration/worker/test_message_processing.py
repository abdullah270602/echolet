"""
Integration Tests - Worker Message Processing

Tests the worker's message processing pipeline with mocked SQS and database.
Verifies the full flow from message receipt to analysis completion.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
import os

# Worker must be first in path for correct config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "worker"))


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def room_name() -> str:
    """Test room name."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_transcript() -> list[dict]:
    """Sample conversation transcript."""
    return [
        {"role": "agent", "content": "Hello! How can I help you?", "timestamp": 1700000000.0},
        {"role": "user", "content": "I need to schedule an appointment.", "timestamp": 1700000005.0},
        {"role": "agent", "content": "Sure, when works for you?", "timestamp": 1700000010.0},
        {"role": "user", "content": "Tomorrow at 3pm.", "timestamp": 1700000015.0},
        {"role": "agent", "content": "Done! Anything else?", "timestamp": 1700000020.0},
        {"role": "user", "content": "No, thanks!", "timestamp": 1700000025.0},
        {"role": "agent", "content": "Have a great day!", "timestamp": 1700000030.0},
    ]


@pytest.fixture
def sample_analysis() -> dict:
    """Sample LLM analysis result."""
    return {
        "summary": "Caller scheduled an appointment for tomorrow at 3pm.",
        "category": "Appointment",
        "urgency": "Medium",
        "sentiment": "Positive",
        "action_required": True,
        "action_items": ["Confirm appointment for tomorrow 3pm"],
    }


@pytest.fixture
def mock_sqs_message(room_name) -> dict:
    """Mock SQS message."""
    return {
        "MessageId": str(uuid.uuid4()),
        "ReceiptHandle": f"receipt_{uuid.uuid4().hex}",
        "Body": json.dumps({"room_name": room_name}),
    }


# =============================================================================
# MESSAGE POLLING INTEGRATION TESTS
# =============================================================================


class TestMessagePolling:
    """Integration tests for SQS message polling."""

    @pytest.mark.integration
    def test_poll_receives_and_parses_messages(self, mock_sqs_message, room_name):
        """Integration: Poll receives messages and parses JSON body."""
        from worker import poll_sqs

        mock_client = MagicMock()
        mock_client.receive_message.return_value = {
            "Messages": [mock_sqs_message]
        }

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            messages = poll_sqs(mock_client)

            assert len(messages) == 1
            assert messages[0]["body"]["room_name"] == room_name
            assert "receipt_handle" in messages[0]

    @pytest.mark.integration
    def test_poll_handles_empty_queue(self):
        """Integration: Poll returns empty list for empty queue."""
        from worker import poll_sqs

        mock_client = MagicMock()
        mock_client.receive_message.return_value = {"Messages": []}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            messages = poll_sqs(mock_client)

            assert messages == []

    @pytest.mark.integration
    def test_poll_deletes_invalid_json_messages(self):
        """Integration: Invalid JSON messages are deleted."""
        from worker import poll_sqs

        invalid_message = {
            "MessageId": "msg-123",
            "ReceiptHandle": "receipt-123",
            "Body": "not valid json",
        }

        mock_client = MagicMock()
        mock_client.receive_message.return_value = {"Messages": [invalid_message]}
        mock_client.delete_message = MagicMock()

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            messages = poll_sqs(mock_client)

            assert messages == []
            mock_client.delete_message.assert_called_once()


# =============================================================================
# MESSAGE PROCESSING INTEGRATION TESTS
# =============================================================================


class TestMessageProcessing:
    """Integration tests for full message processing flow."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_message_full_flow(self, room_name, sample_transcript, sample_analysis):
        """Integration: Full message processing from receipt to DB update."""
        from worker import process_message

        message = {
            "body": {"room_name": room_name},
            "receipt_handle": "receipt-123",
        }

        with patch("worker.fetch_call_data", return_value={"transcript": sample_transcript, "output_config": {}}), \
             patch("worker.analyze_transcript", return_value=sample_analysis), \
             patch("worker.update_analysis", return_value=True):

            result = await process_message(message)

            assert result is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_message_missing_room_name(self):
        """Integration: Message without room_name returns True (skip)."""
        from worker import process_message

        message = {
            "body": {},  # No room_name
            "receipt_handle": "receipt-123",
        }

        result = await process_message(message)

        assert result is True  # Skipped, delete message

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_message_no_transcript(self, room_name):
        """Integration: No transcript found returns True (skip)."""
        from worker import process_message

        message = {
            "body": {"room_name": room_name},
            "receipt_handle": "receipt-123",
        }

        with patch("worker.fetch_call_data", return_value=None):
            result = await process_message(message)

            assert result is True  # No transcript, skip

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_message_db_update_failure(self, room_name, sample_transcript, sample_analysis):
        """Integration: DB update failure returns False (retry)."""
        from worker import process_message

        message = {
            "body": {"room_name": room_name},
            "receipt_handle": "receipt-123",
        }

        with patch("worker.fetch_call_data", return_value={"transcript": sample_transcript, "output_config": {}}), \
             patch("worker.analyze_transcript", return_value=sample_analysis), \
             patch("worker.update_analysis", return_value=False):

            result = await process_message(message)

            assert result is False  # Should retry


# =============================================================================
# TRANSCRIPT FETCHING INTEGRATION TESTS
# =============================================================================


class TestTranscriptFetching:
    """Integration tests for transcript fetching from database."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_transcript_success(self, room_name, sample_transcript):
        """Integration: Fetch transcript returns parsed JSON."""
        from database import fetch_transcript

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {"transcript": json.dumps(sample_transcript), "output_config": None}
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await fetch_transcript(room_name)

            assert result == sample_transcript
            assert len(result) == 7

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_transcript_not_found(self, room_name):
        """Integration: Fetch returns None when room not found."""
        from database import fetch_transcript

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = None
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await fetch_transcript(room_name)

            assert result is None


# =============================================================================
# ANALYSIS INTEGRATION TESTS
# =============================================================================


class TestAnalysisIntegration:
    """Integration tests for transcript analysis."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_transcript_success(self, sample_transcript, sample_analysis):
        """Integration: Analyze transcript returns valid analysis."""
        from analyzer import analyze_transcript

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), \
             patch("httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": json.dumps(sample_analysis)}}]
            }
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await analyze_transcript(sample_transcript)

            assert result["category"] == "Appointment"
            assert result["sentiment"] == "Positive"
            assert result["action_required"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_transcript_llm_error_fallback(self, sample_transcript):
        """Integration: LLM error returns fallback analysis."""
        from analyzer import analyze_transcript

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), \
             patch("httpx.AsyncClient") as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("LLM unavailable")
            )

            result = await analyze_transcript(sample_transcript)

            # Should return fallback, not crash
            assert result is not None
            assert "category" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_empty_transcript(self):
        """Integration: Empty transcript returns default analysis."""
        from analyzer import analyze_transcript

        result = await analyze_transcript([])

        assert result is not None
        assert result["category"] in {"Other", "Inquiry"}


# =============================================================================
# DATABASE UPDATE INTEGRATION TESTS
# =============================================================================


class TestDatabaseUpdateIntegration:
    """Integration tests for database updates."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_analysis_success(self, room_name, sample_analysis):
        """Integration: Update analysis writes to database."""
        from database import update_analysis

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "UPDATE 1"
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await update_analysis(
                room_name=room_name,
                summary=sample_analysis["summary"],
                category=sample_analysis["category"],
                urgency=sample_analysis["urgency"],
                sentiment=sample_analysis["sentiment"],
                action_required=sample_analysis["action_required"],
                action_items=sample_analysis["action_items"],
            )

            assert result is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_analysis_room_not_found(self, room_name, sample_analysis):
        """Integration: Update returns False when room not found."""
        from database import update_analysis

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "UPDATE 0"  # No rows updated
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await update_analysis(
                room_name=room_name,
                summary="Test",
                category="Other",
                urgency="Low",
                sentiment="Neutral",
                action_required=False,
                action_items=[],
            )

            assert result is False


# =============================================================================
# MESSAGE DELETION INTEGRATION TESTS
# =============================================================================


class TestMessageDeletion:
    """Integration tests for SQS message deletion."""

    @pytest.mark.integration
    def test_delete_message_success(self):
        """Integration: Delete message removes from queue."""
        from worker import delete_message

        mock_client = MagicMock()
        mock_client.delete_message.return_value = {}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = delete_message(mock_client, "receipt-123")

            assert result is True
            mock_client.delete_message.assert_called_once()

    @pytest.mark.integration
    def test_delete_message_failure(self):
        """Integration: Delete failure returns False."""
        from worker import delete_message
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.delete_message.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Error"}},
            "DeleteMessage",
        )

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = delete_message(mock_client, "receipt-123")

            assert result is False


# =============================================================================
# FULL PIPELINE INTEGRATION TESTS
# =============================================================================


class TestFullPipeline:
    """Integration tests for complete worker pipeline."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, room_name, sample_transcript, sample_analysis):
        """Integration: Complete pipeline from SQS to DB update."""
        from worker import poll_sqs, process_message, delete_message

        # Setup SQS mock
        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.return_value = {
            "Messages": [{
                "MessageId": "msg-123",
                "ReceiptHandle": "receipt-123",
                "Body": json.dumps({"room_name": room_name}),
            }]
        }
        mock_sqs_client.delete_message.return_value = {}

        # Step 1: Poll SQS
        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            messages = poll_sqs(mock_sqs_client)
            assert len(messages) == 1

        # Step 2: Process message
        message = messages[0]

        with patch("worker.fetch_call_data", return_value={"transcript": sample_transcript, "output_config": {}}), \
             patch("worker.analyze_transcript", return_value=sample_analysis), \
             patch("worker.update_analysis", return_value=True):

            success = await process_message(message)
            assert success is True

        # Step 3: Delete message
        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            deleted = delete_message(mock_sqs_client, message["receipt_handle"])
            assert deleted is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pipeline_retries_on_failure(self, room_name, sample_transcript, sample_analysis):
        """Integration: Pipeline doesn't delete message on failure."""
        from worker import poll_sqs, process_message, delete_message

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

        message = messages[0]

        # Simulate DB update failure
        with patch("worker.fetch_call_data", return_value={"transcript": sample_transcript, "output_config": {}}), \
             patch("worker.analyze_transcript", return_value=sample_analysis), \
             patch("worker.update_analysis", return_value=False):

            success = await process_message(message)
            assert success is False

        # Message should NOT be deleted (will retry after visibility timeout)
        mock_sqs_client.delete_message.assert_not_called()
