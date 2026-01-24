"""
Unit tests for agent repository.

Tests for agent CRUD operations and counting.
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
def mock_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_agent(user_id):
    """Mock AgentConfig object."""
    agent = MagicMock()
    agent.id = 1
    agent.user_id = user_id
    agent.name = "Test Agent"
    agent.business_name = "Test Business"
    agent.voice_id = "Ashley"
    agent.greeting_message = "Hello!"
    agent.tone = "professional"
    agent.custom_instructions = None
    agent.knowledge_base_text = None
    agent.max_duration_seconds = 300
    agent.deleted_at = None
    return agent


@pytest.fixture
def mock_create_request():
    """Mock AgentCreateRequest."""
    request = MagicMock()
    request.name = "New Agent"
    request.business_name = "New Business"
    request.voice_id = "Ashley"
    request.greeting_message = "Welcome!"
    request.tone = "friendly"
    request.custom_instructions = "Be helpful"
    request.knowledge_base_text = "FAQ here"
    request.max_duration_seconds = 600
    return request


@pytest.fixture
def mock_update_request():
    """Mock AgentUpdateRequest."""
    request = MagicMock()
    request.model_dump.return_value = {"name": "Updated Agent", "tone": "casual"}
    return request


# =============================================================================
# GET BY ID TESTS
# =============================================================================


class TestGetById:
    """Tests for get_by_id function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_agent_when_found(self, mock_session, mock_agent):
        """SP: Returns agent when ID exists."""
        from app.db.repos import agent_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_session.execute.return_value = mock_result

        result = await agent_repo.get_by_id(mock_session, 1)

        assert result == mock_agent
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_none_when_not_found(self, mock_session):
        """SP: Returns None when ID doesn't exist."""
        from app.db.repos import agent_repo

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await agent_repo.get_by_id(mock_session, 999)

        assert result is None


# =============================================================================
# GET BY USER ID TESTS
# =============================================================================


class TestGetByUserId:
    """Tests for get_by_user_id function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_user_agents(self, mock_session, mock_agent, user_id):
        """SP: Returns all active agents for user."""
        from app.db.repos import agent_repo

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_agent]
        mock_session.execute.return_value = mock_result

        result = await agent_repo.get_by_user_id(mock_session, user_id)

        assert len(result) == 1
        assert result[0] == mock_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_excludes_deleted_agents(self, mock_session, user_id):
        """SP: Excludes soft-deleted agents from results."""
        from app.db.repos import agent_repo

        # Only active agents returned
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await agent_repo.get_by_user_id(mock_session, user_id)

        assert result == []


# =============================================================================
# GET USER AGENT COUNT TESTS
# =============================================================================


class TestGetUserAgentCount:
    """Tests for get_user_agent_count function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_count(self, mock_session, user_id):
        """SP: Returns correct count of active agents."""
        from app.db.repos import agent_repo

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2
        mock_session.execute.return_value = mock_result

        result = await agent_repo.get_user_agent_count(mock_session, user_id)

        assert result == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_returns_zero_when_no_agents(self, mock_session, user_id):
        """SP: Returns zero when user has no agents."""
        from app.db.repos import agent_repo

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_result

        result = await agent_repo.get_user_agent_count(mock_session, user_id)

        assert result == 0


# =============================================================================
# CREATE TESTS
# =============================================================================


class TestCreate:
    """Tests for create function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_creates_agent(self, mock_session, user_id, mock_create_request):
        """SP: Creates agent with all fields."""
        from app.db.repos import agent_repo

        with patch("app.db.repos.agent_repo.AgentConfig") as MockAgentConfig:
            mock_instance = MagicMock()
            MockAgentConfig.return_value = mock_instance

            result = await agent_repo.create(mock_session, user_id, mock_create_request)

            MockAgentConfig.assert_called_once_with(
                user_id=user_id,
                name=mock_create_request.name,
                business_name=mock_create_request.business_name,
                voice_id=mock_create_request.voice_id,
                greeting_message=mock_create_request.greeting_message,
                tone=mock_create_request.tone,
                custom_instructions=mock_create_request.custom_instructions,
                knowledge_base_text=mock_create_request.knowledge_base_text,
                max_duration_seconds=mock_create_request.max_duration_seconds,
            )
            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_instance)


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdate:
    """Tests for update function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_updates_agent_fields(self, mock_session, mock_agent, mock_update_request):
        """SP: Updates only provided fields."""
        from app.db.repos import agent_repo

        result = await agent_repo.update(mock_session, mock_agent, mock_update_request)

        assert mock_agent.name == "Updated Agent"
        assert mock_agent.tone == "casual"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_agent)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_skips_none_values(self, mock_session, mock_agent):
        """SP: Skips None values in update."""
        from app.db.repos import agent_repo

        mock_request = MagicMock()
        mock_request.model_dump.return_value = {"name": "Updated", "tone": None}

        original_tone = mock_agent.tone
        await agent_repo.update(mock_session, mock_agent, mock_request)

        # tone should remain unchanged (was None in update)
        assert mock_agent.tone == original_tone


# =============================================================================
# SOFT DELETE TESTS
# =============================================================================


class TestSoftDelete:
    """Tests for soft_delete function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_sets_deleted_at(self, mock_session, mock_agent):
        """SP: Sets deleted_at timestamp."""
        from app.db.repos import agent_repo

        assert mock_agent.deleted_at is None

        result = await agent_repo.soft_delete(mock_session, mock_agent)

        assert mock_agent.deleted_at is not None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_agent)


# =============================================================================
# HARD DELETE TESTS
# =============================================================================


class TestDelete:
    """Tests for delete function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_hard_deletes_agent(self, mock_session, mock_agent):
        """SP: Permanently deletes agent."""
        from app.db.repos import agent_repo

        await agent_repo.delete(mock_session, mock_agent)

        mock_session.delete.assert_called_once_with(mock_agent)
        mock_session.commit.assert_called_once()
