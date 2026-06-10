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
def mock_agent(user_id, make_agent_config):
    """Mock AgentConfig object."""
    agent = MagicMock()
    agent.id = 1
    agent.user_id = user_id
    agent.config = make_agent_config()
    agent.status = "inactive"
    agent.phone = None
    agent.deleted_at = None
    return agent


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
    async def test_sp_creates_agent(self, mock_session, user_id, make_agent_config):
        """SP: Creates agent with config, status and phone."""
        from app.db.repos import agent_repo

        config = make_agent_config()
        with patch("app.db.repos.agent_repo.AgentConfig") as MockAgentConfig:
            mock_instance = MagicMock()
            MockAgentConfig.return_value = mock_instance

            result = await agent_repo.create(mock_session, user_id, config, status="active", phone="+1555")

            MockAgentConfig.assert_called_once_with(
                user_id=user_id, config=config, status="active", phone="+1555"
            )
            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_instance)
            assert result is mock_instance


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdate:
    """Tests for update function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_updates_provided_fields(self, mock_session, mock_agent, make_agent_config):
        """SP: Replaces config/status/phone when provided."""
        from app.db.repos import agent_repo

        new_config = make_agent_config(custom_instructions="New")
        await agent_repo.update(mock_session, mock_agent, config=new_config, status="active", phone="+1555")

        assert mock_agent.config == new_config
        assert mock_agent.status == "active"
        assert mock_agent.phone == "+1555"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_agent)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_skips_none_values(self, mock_session, mock_agent):
        """SP: None arguments leave existing values untouched."""
        from app.db.repos import agent_repo

        original_config = mock_agent.config
        await agent_repo.update(mock_session, mock_agent, status="paused")

        assert mock_agent.status == "paused"
        assert mock_agent.config is original_config
        assert mock_agent.phone is None


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


class TestGetActiveById:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filters_out_soft_deleted(self):
        from sqlalchemy.dialects import postgresql
        from app.db.repos import agent_repo

        session = AsyncMock()
        session.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)
        assert await agent_repo.get_active_by_id(session, 5) is None
        sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
        assert "deleted_at IS NULL" in sql
        assert "agent_configs.id" in sql
