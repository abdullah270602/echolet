"""
Phase 5: Resilience Tests - External Service Failures

Tests for graceful degradation when external services fail.

Test Categories:
- BREAK: Service unavailability, timeouts, errors
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from botocore.exceptions import ClientError

import sys
import os

# Order matters: worker must be first so worker/config.py is found before agent/config.py
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
def mock_session() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


# =============================================================================
# LLM API FAILURE TESTS
# =============================================================================


class TestLLMAPIFailures:
    """Tests for LLM API unavailability scenarios."""

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_llm_rate_limited(self):
        """BREAK-P5-B2: LLM returns 429 rate limit."""
        from analyzer import analyze_transcript

        transcript = [{"role": "user", "content": "Hello"}]

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limited"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Rate limited", request=MagicMock(), response=mock_response
                )
            )

            result = await analyze_transcript(transcript)

            # Should return fallback, not crash
            assert result is not None
            assert "failed" in result["summary"].lower()

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_llm_server_error(self):
        """BREAK: LLM returns 500 server error."""
        from analyzer import analyze_transcript

        transcript = [{"role": "user", "content": "Hello"}]

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Server error", request=MagicMock(), response=mock_response
                )
            )

            result = await analyze_transcript(transcript)

            assert result is not None
            assert result["category"] in {"Other", "Inquiry"}  # Valid default

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_llm_network_unreachable(self):
        """BREAK: Network unreachable to LLM."""
        from analyzer import analyze_transcript

        transcript = [{"role": "user", "content": "Hello"}]

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectError("Network unreachable")
            )

            result = await analyze_transcript(transcript)

            assert result is not None


# =============================================================================
# SQS FAILURE TESTS
# =============================================================================


class TestSQSFailures:
    """Tests for SQS unavailability scenarios."""

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_sqs_unavailable(self):
        """BREAK-P5-B4: SQS queue unavailable."""
        from worker import poll_sqs

        mock_client = MagicMock()
        mock_client.receive_message.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}},
            "ReceiveMessage",
        )

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_client)

        # Should return empty list, not crash
        assert result == []

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_sqs_access_denied(self):
        """BREAK: SQS access denied (permissions)."""
        from worker import poll_sqs

        mock_client = MagicMock()
        mock_client.receive_message.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "ReceiveMessage",
        )

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/queue"):
            result = poll_sqs(mock_client)

        assert result == []

    @pytest.mark.resilience
    def test_sqs_queue_not_found(self):
        """BREAK: SQS queue doesn't exist."""
        from worker import poll_sqs

        mock_client = MagicMock()
        mock_client.receive_message.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AWS.SimpleQueueService.NonExistentQueue",
                    "Message": "Queue does not exist",
                }
            },
            "ReceiveMessage",
        )

        with patch("worker.SQS_QUEUE_URL", "https://sqs.test/nonexistent"):
            result = poll_sqs(mock_client)

        assert result == []


# =============================================================================
# AGENT SQS SEND FAILURE TESTS
# =============================================================================


class TestAgentSQSFailures:
    """Tests for agent SQS send failures."""

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_agent_sqs_send_failure(self):
        """BREAK: Agent SQS send fails gracefully."""
        from sqs import send_to_analysis_queue

        with patch("sqs.SQS_QUEUE_URL", "https://sqs.test/queue"), patch(
            "sqs.boto3.client"
        ) as mock_boto:
            mock_client = MagicMock()
            mock_client.send_message.side_effect = ClientError(
                {"Error": {"Code": "500", "Message": "Error"}},
                "SendMessage",
            )
            mock_boto.return_value = mock_client

            result = await send_to_analysis_queue("room-123")

            # Should return False (graceful failure), not crash
            assert result is False

    @pytest.mark.resilience
    @pytest.mark.asyncio
    async def test_agent_sqs_not_configured(self):
        """BREAK: Agent SQS URL not configured."""
        from sqs import send_to_analysis_queue

        with patch("sqs.SQS_QUEUE_URL", ""):
            result = await send_to_analysis_queue("room-123")

            # Should return False gracefully
            assert result is False
