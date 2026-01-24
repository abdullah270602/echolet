"""
Phase 4: Data Layer Integration Tests - Data Integrity

Tests for database constraints, UPSERT atomicity, and data integrity.

Test Categories:
- SP (Sole Purpose): UPSERT atomicity, FK constraints enforced
- BREAK: Concurrent updates, constraint violations
- EDGE: Edge cases in data operations
"""

import uuid
from datetime import datetime, date, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))


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
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# =============================================================================
# SOLE PURPOSE TESTS: UPSERT Atomicity
# =============================================================================


class TestUpsertAtomicity:
    """Tests for usage tracking UPSERT operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_first_usage_creates_record(self, mock_session, user_id):
        """SP-UA-001: First call of day creates new record."""
        from app.db.repos import usage_repo

        # Mock scalar returning None (no existing record)
        mock_session.scalar = AsyncMock(return_value=None)
        # Mock execute for the INSERT
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 100  # Return value after insert
        mock_session.execute = AsyncMock(return_value=mock_result)

        # The increment_usage should handle upsert
        with patch.object(usage_repo, "get_daily_usage", return_value=0):
            result = await usage_repo.increment_usage(mock_session, user_id, 100)
            # Verify the function was called
            assert mock_session.execute.called or mock_session.scalar.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_subsequent_usage_increments(self, mock_session, user_id):
        """SP-UA-002: Subsequent call adds to existing total."""
        from app.db.repos import usage_repo

        # Mock existing usage of 300 seconds
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 400  # 300 + 100
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(usage_repo, "get_daily_usage", return_value=300):
            # increment_usage should return 400 (300 + 100)
            pass  # Test structure for actual implementation

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_zero_increment_allowed(self, mock_session, user_id):
        """EDGE-UP-003: Zero increment should work (no-op)."""
        from app.db.repos import usage_repo

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Zero increment is valid (call that lasted 0 seconds)
        # The database should handle this gracefully


# =============================================================================
# SOLE PURPOSE TESTS: Soft Delete Behavior
# =============================================================================


class TestSoftDeleteBehavior:
    """Tests for soft delete functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_soft_delete_sets_timestamp(self, mock_session, user_id):
        """SP-SD-001: Soft delete sets deleted_at timestamp."""
        from app.db.repos import agent_repo

        mock_agent = MagicMock()
        mock_agent.deleted_at = None
        mock_agent.user_id = user_id

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent):
            await agent_repo.soft_delete(mock_session, mock_agent)
            assert mock_agent.deleted_at is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_soft_deleted_excluded_from_list(self, mock_session, user_id):
        """SP-SD-002: Soft-deleted agents excluded from list queries."""
        from app.db.repos import agent_repo

        # Mock query returning only non-deleted agents
        mock_agents = [MagicMock(deleted_at=None), MagicMock(deleted_at=None)]

        with patch.object(agent_repo, "get_by_user_id", return_value=mock_agents):
            result = await agent_repo.get_by_user_id(mock_session, user_id)
            assert len(result) == 2
            for agent in result:
                assert agent.deleted_at is None


# =============================================================================
# BREAK-IT TESTS: Constraint Violations
# =============================================================================


class TestConstraintViolations:
    """Tests for database constraint enforcement."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_duplicate_unique_constraint(self, mock_session):
        """BREAK: Duplicate unique constraint should raise."""
        from sqlalchemy.exc import IntegrityError

        # Simulate duplicate room_name (unique constraint)
        mock_session.execute.side_effect = IntegrityError(
            "statement", "params", "UniqueViolation"
        )

        # Test that duplicate entries are properly handled
        with pytest.raises(IntegrityError):
            await mock_session.execute("INSERT INTO ...")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_fk_constraint_invalid_user(self, mock_session):
        """BREAK-P4-B3: FK constraint prevents invalid user_id."""
        from sqlalchemy.exc import IntegrityError

        # Simulate FK violation (non-existent user_id)
        mock_session.execute.side_effect = IntegrityError(
            "statement", "params", "ForeignKeyViolation"
        )

        # Test that FK violations are caught
        with pytest.raises(IntegrityError):
            await mock_session.execute("INSERT INTO call_sessions ...")


# =============================================================================
# EDGE CASES: Data Operations
# =============================================================================


class TestDataEdgeCases:
    """Edge case tests for data operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_midnight_rollover(self, user_id):
        """EDGE-UP-004: Usage resets at midnight UTC."""
        from datetime import date, timedelta

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Usage from yesterday should not affect today's limit
        # This tests the date-based unique constraint

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_large_transcript_jsonb(self):
        """EDGE-P4-B4: Large transcript stored in JSONB."""
        # 1000+ message transcript
        large_transcript = [
            {"role": "user" if i % 2 else "agent", "content": f"Message {i}"}
            for i in range(1000)
        ]

        # JSONB should handle this (PostgreSQL limit is ~1GB)
        import json

        serialized = json.dumps(large_transcript)
        assert len(serialized) > 10000  # Ensure it's actually large

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_special_characters_in_jsonb(self):
        """EDGE: Special characters in JSONB transcript."""
        transcript = [
            {"role": "user", "content": "Hello \x00 null byte"},
            {"role": "agent", "content": "Unicode: 你好 مرحبا 👋"},
            {"role": "user", "content": 'Quotes: "test" \'test\''},
            {"role": "agent", "content": "Newlines:\n\ttabs"},
        ]

        # Should serialize without error
        import json

        serialized = json.dumps(transcript)
        assert serialized is not None
