"""
Unit tests for worker database module.

Tests for SSL handling, URL parsing, and database operations.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

import sys
import os

# Worker must be first in path for correct config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "worker"))


# =============================================================================
# SSL CONTEXT TESTS
# =============================================================================


class TestGetSslContext:
    """Tests for get_ssl_context function."""

    @pytest.mark.unit
    def test_sp_returns_context_for_sslmode_require(self):
        """SP: Returns SSL context when sslmode=require."""
        from database import get_ssl_context

        url = "postgresql://user:pass@host/db?sslmode=require"
        result = get_ssl_context(url)

        assert result is not None

    @pytest.mark.unit
    def test_sp_returns_context_for_verify_ca(self):
        """SP: Returns SSL context for sslmode=verify-ca."""
        from database import get_ssl_context

        url = "postgresql://user:pass@host/db?sslmode=verify-ca"
        result = get_ssl_context(url)

        assert result is not None

    @pytest.mark.unit
    def test_sp_returns_context_for_verify_full(self):
        """SP: Returns SSL context for sslmode=verify-full."""
        from database import get_ssl_context

        url = "postgresql://user:pass@host/db?sslmode=verify-full"
        result = get_ssl_context(url)

        assert result is not None

    @pytest.mark.unit
    def test_sp_returns_none_without_sslmode(self):
        """SP: Returns None when no sslmode in URL."""
        from database import get_ssl_context

        url = "postgresql://user:pass@host/db"
        result = get_ssl_context(url)

        assert result is None

    @pytest.mark.unit
    def test_sp_returns_none_for_sslmode_disable(self):
        """SP: Returns None for sslmode=disable."""
        from database import get_ssl_context

        url = "postgresql://user:pass@host/db?sslmode=disable"
        result = get_ssl_context(url)

        assert result is None


# =============================================================================
# GET CLEAN URL TESTS
# =============================================================================


class TestGetCleanUrl:
    """Tests for get_clean_url function."""

    @pytest.mark.unit
    def test_sp_removes_sslmode_from_url(self):
        """SP: Removes sslmode parameter from URL."""
        from database import get_clean_url

        url = "postgresql://user:pass@host/db?sslmode=require"
        result = get_clean_url(url)

        assert "sslmode" not in result
        assert "postgresql://user:pass@host/db" in result

    @pytest.mark.unit
    def test_sp_preserves_other_params(self):
        """SP: Preserves other query parameters."""
        from database import get_clean_url

        url = "postgresql://user:pass@host/db?sslmode=require&timeout=30"
        result = get_clean_url(url)

        assert "sslmode" not in result
        assert "timeout=30" in result

    @pytest.mark.unit
    def test_sp_returns_unchanged_without_sslmode(self):
        """SP: Returns URL unchanged when no sslmode."""
        from database import get_clean_url

        url = "postgresql://user:pass@host/db?timeout=30"
        result = get_clean_url(url)

        assert result == url


# =============================================================================
# FETCH TRANSCRIPT TESTS
# =============================================================================


class TestFetchTranscript:
    """Tests for fetch_transcript function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_transcript_when_found(self):
        """SP: Returns transcript list when found."""
        from database import fetch_transcript

        transcript = [{"role": "user", "content": "Hello"}]

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {"transcript": json.dumps(transcript), "output_config": None}
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await fetch_transcript("room-123")

            assert result == transcript
            mock_conn.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_transcript_dict_format(self):
        """SP: Handles transcript as dict (not JSON string)."""
        from database import fetch_transcript

        transcript = [{"role": "agent", "content": "Hi"}]

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            # Transcript already as dict (PostgreSQL JSONB)
            mock_conn.fetchrow.return_value = {"transcript": transcript, "output_config": None}
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await fetch_transcript("room-123")

            assert result == transcript

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self):
        """SP: Returns None when room not found."""
        from database import fetch_transcript

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = None
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await fetch_transcript("nonexistent")

            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_transcript_empty(self):
        """SP: Returns None when transcript is empty."""
        from database import fetch_transcript

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {"transcript": None, "output_config": None}
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await fetch_transcript("room-123")

            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_no_database_url(self):
        """SP: Returns None when DATABASE_URL not configured."""
        from database import fetch_transcript

        with patch("database.DATABASE_URL", ""):
            result = await fetch_transcript("room-123")

            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_handles_connection_error(self):
        """BREAK: Handles connection errors gracefully."""
        from database import fetch_transcript

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect", side_effect=Exception("Connection failed")):
            result = await fetch_transcript("room-123")

            assert result is None


# =============================================================================
# UPDATE ANALYSIS TESTS
# =============================================================================


class TestUpdateAnalysis:
    """Tests for update_analysis function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_updates_analysis_successfully(self):
        """SP: Updates analysis and returns True."""
        from database import update_analysis

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "UPDATE 1"
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await update_analysis(
                room_name="room-123",
                summary="Test summary",
                category="Inquiry",
                urgency="Low",
                sentiment="Positive",
                action_required=False,
                action_items=["Follow up"],
            )

            assert result is True
            mock_conn.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_false_when_not_found(self):
        """SP: Returns False when room not found."""
        from database import update_analysis

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "UPDATE 0"
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await update_analysis(
                room_name="nonexistent",
                summary="Test",
                category="Other",
                urgency="Low",
                sentiment="Neutral",
                action_required=False,
                action_items=[],
            )

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_false_when_no_database_url(self):
        """SP: Returns False when DATABASE_URL not configured."""
        from database import update_analysis

        with patch("database.DATABASE_URL", ""):
            result = await update_analysis(
                room_name="room-123",
                summary="Test",
                category="Other",
                urgency="Low",
                sentiment="Neutral",
                action_required=False,
                action_items=[],
            )

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_handles_connection_error(self):
        """BREAK: Handles connection errors gracefully."""
        from database import update_analysis

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect", side_effect=Exception("Connection failed")):
            result = await update_analysis(
                room_name="room-123",
                summary="Test",
                category="Other",
                urgency="Low",
                sentiment="Neutral",
                action_required=False,
                action_items=[],
            )

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_serializes_action_items_as_json(self):
        """EDGE: Properly serializes action_items list."""
        from database import update_analysis

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "UPDATE 1"
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            action_items = ["Call back", "Send email", "Schedule meeting"]

            result = await update_analysis(
                room_name="room-123",
                summary="Test",
                category="Appointment",
                urgency="High",
                sentiment="Positive",
                action_required=True,
                action_items=action_items,
            )

            assert result is True
            # Verify execute was called with JSON-serialized action_items
            call_args = mock_conn.execute.call_args[0]
            assert json.dumps(action_items) in str(call_args)


# =============================================================================
# FETCH CALL DATA TESTS (transcript + agent output config)
# =============================================================================


class TestFetchCallData:
    """Tests for fetch_call_data (reads agent_configs.config->'output')."""

    @staticmethod
    async def _fetch(row):
        from database import fetch_call_data

        with patch("database.DATABASE_URL", "postgresql://test"), \
             patch("database.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = row
            mock_connect.return_value = mock_conn
            return await fetch_call_data("room-123")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_output_config_dict_passthrough(self):
        cfg = {"ticket_fields": [{"id": "x", "type": "string"}], "custom_tags": ["vip"]}
        result = await self._fetch({"transcript": [{"role": "user", "content": "hi"}], "output_config": cfg})
        assert result["transcript"] == [{"role": "user", "content": "hi"}]
        assert result["output_config"] == cfg
        assert result["call_data"] == {"timestamp": None, "duration_seconds": None}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_output_config_json_string_decoded(self):
        cfg = {"custom_tags": ["vip"]}
        result = await self._fetch({"transcript": None, "output_config": json.dumps(cfg)})
        assert result["output_config"] == cfg
        assert result["transcript"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_missing_agent_gives_empty_output_config(self):
        """LEFT JOIN with deleted/absent agent yields NULL config -> {}."""
        result = await self._fetch({"transcript": None, "output_config": None})
        assert result["output_config"] == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_unknown_room_returns_none(self):
        assert await self._fetch(None) is None
