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






class TestSoftDeleteBehavior:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_soft_delete_sets_timestamp(self, mock_session, user_id):
        from app.db.repos import agent_repo

        agent = MagicMock(deleted_at=None, user_id=user_id)
        await agent_repo.soft_delete(mock_session, agent)

        assert agent.deleted_at is not None
        mock_session.delete.assert_not_called()  # row (and call history) preserved
