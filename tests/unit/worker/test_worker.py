"""
Phase 3: Worker Service Unit Tests - Message Lifecycle

Tests for SQS message polling, processing, and deletion logic.

Test Categories:
- SP (Sole Purpose): Messages processed and deleted correctly
- BREAK: Malformed messages, processing failures
- EDGE: Edge cases in message handling
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "worker"))

from worker import poll_sqs, delete_message, process_message


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_sqs_client() -> MagicMock:
    """Mock SQS client."""
    return MagicMock()


@pytest.fixture
def valid_sqs_message() -> dict:
    """Valid SQS message."""
    return {
        "MessageId": "msg-123",
        "ReceiptHandle": "receipt-abc",
        "Body": json.dumps({"room_name": "room-uuid-123", "timestamp": 1700000000}),
    }


@pytest.fixture
def sample_transcript() -> list:
    """Sample transcript from database."""
    return [
        {"role": "agent", "content": "Hello!"},
        {"role": "user", "content": "Hi, I need help"},
    ]


@pytest.fixture
def sample_analysis() -> dict:
    """Sample analysis result."""
    return {
        "summary": "Test summary",
        "category": "Inquiry",
        "urgency": "Medium",
        "sentiment": "Neutral",
        "action_required": False,
        "action_items": [],
    }


# =============================================================================
# SOLE PURPOSE TESTS: poll_sqs
# =============================================================================


class TestPollSQS:
    """Tests for SQS polling."""

    @pytest.mark.unit
    def test_sp_returns_parsed_messages(self, mock_sqs_client, valid_sqs_message):
        """SP: Valid messages are parsed correctly."""
        mock_sqs_client.receive_message.return_value = {
            "Messages": [valid_sqs_message]
        }

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_sqs_client)

        assert len(result) == 1
        assert result[0]["body"]["room_name"] == "room-uuid-123"
        assert result[0]["receipt_handle"] == "receipt-abc"

    @pytest.mark.unit
    def test_sp_empty_queue_returns_empty_list(self, mock_sqs_client):
        """SP: Empty queue returns empty list."""
        mock_sqs_client.receive_message.return_value = {"Messages": []}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_sqs_client)

        assert result == []

    @pytest.mark.unit
    def test_sp_no_messages_key_returns_empty(self, mock_sqs_client):
        """SP: Response without 'Messages' key returns empty list."""
        mock_sqs_client.receive_message.return_value = {}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_sqs_client)

        assert result == []


# =============================================================================
# BREAK-IT TESTS: Malformed Messages
# =============================================================================


class TestMalformedMessages:
    """Tests for handling malformed SQS messages."""

    @pytest.mark.unit
    def test_break_invalid_json_deleted(self, mock_sqs_client):
        """BREAK-BM-001: Invalid JSON message is deleted."""
        invalid_message = {
            "MessageId": "msg-bad",
            "ReceiptHandle": "receipt-bad",
            "Body": "not valid json {",
        }
        mock_sqs_client.receive_message.return_value = {"Messages": [invalid_message]}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"), patch(
            "worker.delete_message"
        ) as mock_delete:
            result = poll_sqs(mock_sqs_client)

        # Invalid message should be deleted
        mock_delete.assert_called_once_with(mock_sqs_client, "receipt-bad")
        # And not returned
        assert result == []

    @pytest.mark.unit
    def test_break_sqs_client_error(self, mock_sqs_client):
        """BREAK-SR-001: SQS ClientError returns empty list."""
        mock_sqs_client.receive_message.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "ReceiveMessage",
        )

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_sqs_client)

        assert result == []


# =============================================================================
# SOLE PURPOSE TESTS: delete_message
# =============================================================================


class TestDeleteMessage:
    """Tests for SQS message deletion."""

    @pytest.mark.unit
    def test_sp_successful_delete(self, mock_sqs_client):
        """SP: Successful delete returns True."""
        mock_sqs_client.delete_message.return_value = {}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = delete_message(mock_sqs_client, "receipt-123")

        assert result is True
        mock_sqs_client.delete_message.assert_called_once()

    @pytest.mark.unit
    def test_sp_delete_failure_returns_false(self, mock_sqs_client):
        """SP: Delete failure returns False."""
        mock_sqs_client.delete_message.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Error"}},
            "DeleteMessage",
        )

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = delete_message(mock_sqs_client, "receipt-123")

        assert result is False


# =============================================================================
# SOLE PURPOSE TESTS: process_message
# =============================================================================


class TestProcessMessage:
    """Tests for message processing logic."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_successful_processing(
        self, sample_transcript, sample_analysis
    ):
        """SP-SM-001: Successful processing returns True."""
        message = {
            "body": {"room_name": "room-123"},
            "receipt_handle": "receipt-abc",
        }

        with patch("worker.fetch_transcript", return_value=sample_transcript), patch(
            "worker.analyze_transcript", return_value=sample_analysis
        ), patch("worker.update_analysis", return_value=True):
            result = await process_message(message)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_missing_room_name_returns_true(self):
        """BREAK-BM-002: Missing room_name returns True (delete message)."""
        message = {
            "body": {},  # No room_name
            "receipt_handle": "receipt-abc",
        }

        result = await process_message(message)

        # Returns True to delete invalid message (avoid infinite retry)
        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_no_transcript_returns_true(self):
        """BREAK-P3-B5: No transcript found returns True (delete message)."""
        message = {
            "body": {"room_name": "room-not-found"},
            "receipt_handle": "receipt-abc",
        }

        with patch("worker.fetch_transcript", return_value=None):
            result = await process_message(message)

        # Returns True to delete (avoid infinite retry for missing transcripts)
        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_db_update_failure_returns_false(
        self, sample_transcript, sample_analysis
    ):
        """SP-ML-002: DB update failure returns False (don't delete)."""
        message = {
            "body": {"room_name": "room-123"},
            "receipt_handle": "receipt-abc",
        }

        with patch("worker.fetch_transcript", return_value=sample_transcript), patch(
            "worker.analyze_transcript", return_value=sample_analysis
        ), patch("worker.update_analysis", return_value=False):  # DB update fails
            result = await process_message(message)

        # Returns False - message should NOT be deleted (retry later)
        assert result is False


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests for worker."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_empty_room_name(self):
        """EDGE: Empty string room_name treated as missing."""
        message = {
            "body": {"room_name": ""},  # Empty string
            "receipt_handle": "receipt-abc",
        }

        # Empty string is falsy, should be treated as missing
        result = await process_message(message)
        assert result is True  # Delete invalid message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_null_room_name(self):
        """EDGE: None room_name treated as missing."""
        message = {
            "body": {"room_name": None},
            "receipt_handle": "receipt-abc",
        }

        result = await process_message(message)
        assert result is True  # Delete invalid message

    @pytest.mark.unit
    def test_edge_multiple_messages_batch(self, mock_sqs_client):
        """EDGE: Multiple messages in single poll."""
        messages = [
            {
                "MessageId": f"msg-{i}",
                "ReceiptHandle": f"receipt-{i}",
                "Body": json.dumps({"room_name": f"room-{i}"}),
            }
            for i in range(5)
        ]
        mock_sqs_client.receive_message.return_value = {"Messages": messages}

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_sqs_client)

        assert len(result) == 5
        for i, msg in enumerate(result):
            assert msg["body"]["room_name"] == f"room-{i}"


# =============================================================================
# DUPLICATE HANDLING (Idempotency)
# =============================================================================


class TestDuplicateHandling:
    """Tests for duplicate message handling."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_message_idempotent(
        self, sample_transcript, sample_analysis
    ):
        """BREAK-DM-001: Same message processed twice is idempotent."""
        message = {
            "body": {"room_name": "room-123"},
            "receipt_handle": "receipt-abc",
        }

        with patch("worker.fetch_transcript", return_value=sample_transcript), patch(
            "worker.analyze_transcript", return_value=sample_analysis
        ), patch("worker.update_analysis", return_value=True) as mock_update:
            # Process same message twice
            result1 = await process_message(message)
            result2 = await process_message(message)

        # Both should succeed (UPDATE is idempotent)
        assert result1 is True
        assert result2 is True
        assert mock_update.call_count == 2
