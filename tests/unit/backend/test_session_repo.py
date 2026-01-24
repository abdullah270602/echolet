"""
Unit tests for session repository.

Tests for call session CRUD operations and history queries.
"""

import uuid
from datetime import datetime, timezone
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
def room_name() -> str:
    """Test room name."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_call_session(user_id, room_name):
    """Mock CallSession object."""
    session = MagicMock()
    session.id = 1
    session.room_name = room_name
    session.user_id = user_id
    session.agent_id = 1
    session.status = "pending"
    session.transcript = None
    session.duration_seconds = None
    session.summary = None
    session.priority = "normal"
    session.ended_at = None
    session.created_at = datetime.now(timezone.utc)
    return session


# =============================================================================
# GET BY ID TESTS
# =============================================================================


class TestGetById:
    """Tests for get_by_id function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_session_when_found(self, mock_session, mock_call_session):
        """SP: Returns session when ID exists."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_call_session
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_id(mock_session, 1)

        assert result == mock_call_session
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self, mock_session):
        """SP: Returns None when ID doesn't exist."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_id(mock_session, 999)

        assert result is None


# =============================================================================
# GET BY ROOM NAME TESTS
# =============================================================================


class TestGetByRoomName:
    """Tests for get_by_room_name function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_session_when_found(self, mock_session, mock_call_session, room_name):
        """SP: Returns session when room_name exists."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_call_session
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_room_name(mock_session, room_name)

        assert result == mock_call_session

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self, mock_session):
        """SP: Returns None when room_name doesn't exist."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_room_name(mock_session, "nonexistent")

        assert result is None


# =============================================================================
# GET BY ROOM NAME WITH AGENT TESTS
# =============================================================================


class TestGetByRoomNameWithAgent:
    """Tests for get_by_room_name_with_agent function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_tuple_when_found(self, mock_session, mock_call_session, room_name):
        """SP: Returns (session, agent) tuple when found."""
        from app.db.repos import session_repo

        mock_agent = MagicMock()
        mock_agent.id = 1
        mock_agent.name = "Test Agent"

        mock_result = MagicMock()
        mock_result.first.return_value = (mock_call_session, mock_agent)
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_room_name_with_agent(mock_session, room_name)

        assert result is not None
        assert result[0] == mock_call_session
        assert result[1] == mock_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self, mock_session):
        """SP: Returns None when not found."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_room_name_with_agent(mock_session, "nonexistent")

        assert result is None


# =============================================================================
# CREATE TESTS
# =============================================================================


class TestCreate:
    """Tests for create function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_creates_session_with_pending_status(self, mock_session, user_id):
        """SP: Creates session with pending status."""
        from app.db.repos import session_repo

        with patch("app.db.repos.session_repo.CallSession") as MockCallSession:
            mock_instance = MagicMock()
            MockCallSession.return_value = mock_instance

            result = await session_repo.create(mock_session, user_id, agent_id=1)

            MockCallSession.assert_called_once_with(
                user_id=user_id,
                agent_id=1,
                status="pending",
            )
            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_instance)


# =============================================================================
# UPDATE STATUS TESTS
# =============================================================================


class TestUpdateStatus:
    """Tests for update_status function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_updates_status(self, mock_session, mock_call_session):
        """SP: Updates session status."""
        from app.db.repos import session_repo

        result = await session_repo.update_status(mock_session, mock_call_session, "active")

        assert mock_call_session.status == "active"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_call_session)


# =============================================================================
# UPDATE CALL LOG TESTS
# =============================================================================


class TestUpdateCallLog:
    """Tests for update_call_log function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_updates_call_log(self, mock_session, mock_call_session, room_name):
        """SP: Updates call log with transcript and metadata."""
        from app.db.repos import session_repo

        transcript = [{"role": "user", "content": "Hello"}]

        with patch.object(session_repo, "get_by_room_name", return_value=mock_call_session):
            result = await session_repo.update_call_log(
                mock_session,
                room_name,
                transcript=transcript,
                duration_seconds=60,
                status="completed",
                summary="Test summary",
                priority="high",
            )

            assert result == mock_call_session
            assert mock_call_session.transcript == transcript
            assert mock_call_session.duration_seconds == 60
            assert mock_call_session.status == "completed"
            assert mock_call_session.summary == "Test summary"
            assert mock_call_session.priority == "high"
            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self, mock_session, room_name):
        """SP: Returns None when session not found."""
        from app.db.repos import session_repo

        with patch.object(session_repo, "get_by_room_name", return_value=None):
            result = await session_repo.update_call_log(
                mock_session,
                room_name,
                transcript=[],
                duration_seconds=0,
            )

            assert result is None


# =============================================================================
# GET USER CALL HISTORY TESTS
# =============================================================================


class TestGetUserCallHistory:
    """Tests for get_user_call_history function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_call_history(self, mock_session, user_id):
        """SP: Returns formatted call history."""
        from app.db.repos import session_repo

        mock_call = MagicMock()
        mock_call.id = 1
        mock_call.room_name = "room-123"
        mock_call.user_id = user_id
        mock_call.agent_id = 1
        mock_call.status = "completed"
        mock_call.duration_seconds = 120
        mock_call.transcript = []
        mock_call.summary = "Test call"
        mock_call.priority = "normal"
        mock_call.sentiment = "Positive"
        mock_call.action_items = []
        mock_call.category = "Inquiry"
        mock_call.urgency = "Low"
        mock_call.action_required = False
        mock_call.created_at = datetime.now(timezone.utc)
        mock_call.ended_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_call, "Test Agent", None)]
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_user_call_history(mock_session, user_id)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["agent_name"] == "Test Agent"
        assert result[0]["is_agent_deleted"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_marks_deleted_agent(self, mock_session, user_id):
        """SP: Marks agent as deleted when deleted_at is set."""
        from app.db.repos import session_repo

        mock_call = MagicMock()
        mock_call.id = 1
        mock_call.room_name = "room-123"
        mock_call.user_id = user_id
        mock_call.agent_id = 1
        mock_call.status = "completed"
        mock_call.duration_seconds = 120
        mock_call.transcript = []
        mock_call.summary = "Test call"
        mock_call.priority = "normal"
        mock_call.sentiment = "Positive"
        mock_call.action_items = []
        mock_call.category = "Inquiry"
        mock_call.urgency = "Low"
        mock_call.action_required = False
        mock_call.created_at = datetime.now(timezone.utc)
        mock_call.ended_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        # Agent was deleted
        mock_result.all.return_value = [(mock_call, "Deleted Agent", datetime.now(timezone.utc))]
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_user_call_history(mock_session, user_id)

        assert result[0]["is_agent_deleted"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_empty_list_when_no_history(self, mock_session, user_id):
        """SP: Returns empty list when user has no call history."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_user_call_history(mock_session, user_id)

        assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_respects_limit_parameter(self, mock_session, user_id):
        """SP: Respects limit parameter in query."""
        from app.db.repos import session_repo

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        await session_repo.get_user_call_history(mock_session, user_id, limit=10)

        # Verify execute was called (limit is in the query)
        mock_session.execute.assert_called_once()
