"""
Unit tests for user repository.

Tests for user CRUD operations including UPSERT.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Mock User object."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.clerk_id = "user_123abc"
    user.email = "test@example.com"
    return user


# =============================================================================
# UPSERT USER TESTS
# =============================================================================


class TestUpsertUser:
    """Tests for upsert_user function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_creates_new_user(self, mock_session, mock_user):
        """SP: Creates new user when clerk_id doesn't exist."""
        from app.db.repos import user_repo

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await user_repo.upsert_user(
            mock_session,
            clerk_id="user_123abc",
            email="test@example.com",
        )

        assert result == mock_user
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_updates_existing_user(self, mock_session, mock_user):
        """SP: Updates existing user when clerk_id exists."""
        from app.db.repos import user_repo

        mock_user.email = "updated@example.com"
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await user_repo.upsert_user(
            mock_session,
            clerk_id="user_123abc",
            email="updated@example.com",
        )

        assert result.email == "updated@example.com"


# =============================================================================
# GET BY CLERK ID TESTS
# =============================================================================


class TestGetByClerkId:
    """Tests for get_by_clerk_id function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_user_when_found(self, mock_session, mock_user):
        """SP: Returns user when clerk_id exists."""
        from app.db.repos import user_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await user_repo.get_by_clerk_id(mock_session, "user_123abc")

        assert result == mock_user
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self, mock_session):
        """SP: Returns None when clerk_id doesn't exist."""
        from app.db.repos import user_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await user_repo.get_by_clerk_id(mock_session, "nonexistent")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_special_characters_in_clerk_id(self, mock_session, mock_user):
        """EDGE: Handles special characters in clerk_id."""
        from app.db.repos import user_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Clerk IDs can have underscores and alphanumeric chars
        result = await user_repo.get_by_clerk_id(mock_session, "user_abc123_xyz")

        assert result == mock_user
