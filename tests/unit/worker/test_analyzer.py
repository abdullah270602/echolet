"""
Phase 3: Worker Service Unit Tests - Analyzer

Tests for LLM transcript analysis, JSON parsing, and validation.

Test Categories:
- SP (Sole Purpose): Analysis always returns valid structure
- BREAK: Malformed LLM responses, validation failures
- EDGE: Boundary conditions
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "worker"))

from analyzer import (
    format_transcript,
    get_default_analysis,
    analyze_transcript,
    VALID_CATEGORIES,
    VALID_URGENCIES,
    VALID_SENTIMENTS,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_transcript() -> list:
    """Sample valid transcript."""
    return [
        {"role": "agent", "content": "Hello, how can I help?"},
        {"role": "user", "content": "I want to book an appointment"},
        {"role": "agent", "content": "Sure, when would you like?"},
        {"role": "user", "content": "Tomorrow at 2pm"},
    ]


@pytest.fixture
def valid_llm_response() -> dict:
    """Valid LLM analysis response."""
    return {
        "summary": "Caller requested an appointment for tomorrow at 2pm.",
        "category": "Appointment",
        "urgency": "Medium",
        "sentiment": "Positive",
        "action_required": True,
        "action_items": ["Confirm appointment for tomorrow 2pm"],
    }


# =============================================================================
# SOLE PURPOSE TESTS: format_transcript
# =============================================================================


class TestFormatTranscript:
    """Tests for transcript formatting."""

    @pytest.mark.unit
    def test_sp_formats_basic_transcript(self, sample_transcript):
        """SP: Basic transcript is formatted correctly."""
        result = format_transcript(sample_transcript)

        assert "[agent]: Hello, how can I help?" in result
        assert "[user]: I want to book an appointment" in result
        assert "\n" in result  # Multiple lines

    @pytest.mark.unit
    def test_sp_handles_empty_transcript(self):
        """SP: Empty transcript returns empty string."""
        result = format_transcript([])
        assert result == ""

    @pytest.mark.unit
    def test_sp_handles_missing_fields(self):
        """SP: Missing fields use defaults."""
        transcript = [
            {},  # Empty dict
            {"role": "agent"},  # Missing content
            {"content": "hello"},  # Missing role
        ]
        result = format_transcript(transcript)

        assert "[unknown]:" in result
        assert "[agent]:" in result

    @pytest.mark.unit
    def test_edge_unicode_content(self):
        """EDGE: Unicode characters preserved."""
        transcript = [
            {"role": "user", "content": "Hello 你好 مرحبا 👋"},
        ]
        result = format_transcript(transcript)
        assert "你好" in result
        assert "مرحبا" in result
        assert "👋" in result


# =============================================================================
# SOLE PURPOSE TESTS: get_default_analysis
# =============================================================================


class TestGetDefaultAnalysis:
    """Tests for default analysis fallback."""

    @pytest.mark.unit
    def test_sp_returns_valid_structure(self):
        """SP: Default analysis has all required fields."""
        result = get_default_analysis()

        assert "summary" in result
        assert "category" in result
        assert "urgency" in result
        assert "sentiment" in result
        assert "action_required" in result
        assert "action_items" in result

    @pytest.mark.unit
    def test_sp_default_values_are_valid(self):
        """SP: Default values pass validation."""
        result = get_default_analysis()

        assert result["category"] in VALID_CATEGORIES
        assert result["urgency"] in VALID_URGENCIES
        assert result["sentiment"] in VALID_SENTIMENTS
        assert isinstance(result["action_required"], bool)
        assert isinstance(result["action_items"], list)


# =============================================================================
# SOLE PURPOSE TESTS: analyze_transcript
# =============================================================================


class TestAnalyzeTranscript:
    """Tests for LLM analysis."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_empty_transcript_returns_default(self):
        """SP-TE-001: Empty transcript returns default with specific message."""
        result = await analyze_transcript([])

        assert "Empty call" in result["summary"]
        assert result["category"] == "Other"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_missing_api_key_returns_default(self, sample_transcript):
        """SP: Missing API key returns default analysis."""
        with patch("analyzer.OPENROUTER_API_KEY", ""):
            result = await analyze_transcript(sample_transcript)

            assert "API key not configured" in result["summary"]
            assert result["category"] == "Other"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_valid_response_parsed(
        self, sample_transcript, valid_llm_response
    ):
        """SP-AP-001: Valid LLM response is parsed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(valid_llm_response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert result["summary"] == valid_llm_response["summary"]
            assert result["category"] == valid_llm_response["category"]
            assert result["urgency"] == valid_llm_response["urgency"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_markdown_json_parsed(self, sample_transcript, valid_llm_response):
        """SP-AP-002: JSON in markdown code blocks is parsed."""
        # LLM sometimes wraps JSON in ```json ... ```
        markdown_response = f"```json\n{json.dumps(valid_llm_response)}\n```"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": markdown_response}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert result["summary"] == valid_llm_response["summary"]


# =============================================================================
# BREAK-IT TESTS: Invalid LLM Responses
# =============================================================================


class TestInvalidLLMResponses:
    """Tests for handling invalid LLM responses."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_invalid_json(self, sample_transcript):
        """BREAK-LV-001: Invalid JSON returns fallback."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "not valid json {"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            # Should return fallback
            assert "failed" in result["summary"].lower()
            assert result["category"] in VALID_CATEGORIES

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_invalid_category(self, sample_transcript):
        """BREAK-LV-002: Invalid category falls back to 'Other'."""
        invalid_response = {
            "summary": "Test summary",
            "category": "Emergency",  # Not in VALID_CATEGORIES
            "urgency": "Medium",
            "sentiment": "Neutral",
            "action_required": False,
            "action_items": [],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(invalid_response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert result["category"] == "Other"  # Fallback

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_invalid_urgency(self, sample_transcript):
        """BREAK-LV-003: Invalid urgency falls back to 'Medium'."""
        invalid_response = {
            "summary": "Test",
            "category": "Inquiry",
            "urgency": "Critical",  # Not in VALID_URGENCIES
            "sentiment": "Neutral",
            "action_required": False,
            "action_items": [],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(invalid_response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert result["urgency"] == "Medium"  # Fallback

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_invalid_sentiment(self, sample_transcript):
        """BREAK-LV-004: Invalid sentiment falls back to 'Neutral'."""
        invalid_response = {
            "summary": "Test",
            "category": "Inquiry",
            "urgency": "Medium",
            "sentiment": "Sad",  # Not in VALID_SENTIMENTS
            "action_required": False,
            "action_items": [],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(invalid_response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert result["sentiment"] == "Neutral"  # Fallback

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_http_error_returns_fallback(self, sample_transcript):
        """BREAK-LF-002: HTTP 429 (rate limit) returns fallback."""
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

            result = await analyze_transcript(sample_transcript)

            assert "failed" in result["summary"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_timeout_returns_fallback(self, sample_transcript):
        """BREAK-LF-001: Timeout returns fallback."""
        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            result = await analyze_transcript(sample_transcript)

            assert "failed" in result["summary"].lower()


# =============================================================================
# EDGE CASES: Truncation and Limits
# =============================================================================


class TestTruncationAndLimits:
    """Tests for data truncation and limits."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_summary_truncated_to_1000(self, sample_transcript):
        """EDGE-AP-004: Summary > 1000 chars is truncated."""
        long_summary = "a" * 1500
        response = {
            "summary": long_summary,
            "category": "Inquiry",
            "urgency": "Medium",
            "sentiment": "Neutral",
            "action_required": False,
            "action_items": [],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert len(result["summary"]) == 1000

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_action_items_limited_to_10(self, sample_transcript):
        """EDGE-AP-005: Action items limited to 10."""
        response = {
            "summary": "Test",
            "category": "Inquiry",
            "urgency": "Medium",
            "sentiment": "Neutral",
            "action_required": True,
            "action_items": [f"Item {i}" for i in range(15)],  # 15 items
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert len(result["action_items"]) == 10

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_missing_fields_use_defaults(self, sample_transcript):
        """EDGE-PR-004: Missing fields use defaults."""
        response = {"summary": "Just a summary"}  # Missing all other fields

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(response)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("analyzer.OPENROUTER_API_KEY", "test_key"), patch(
            "httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_transcript(sample_transcript)

            assert result["summary"] == "Just a summary"
            assert result["category"] == "Other"  # Default
            assert result["urgency"] == "Medium"  # Default
            assert result["sentiment"] == "Neutral"  # Default
            assert result["action_required"] is False  # Default
            assert result["action_items"] == []  # Default
