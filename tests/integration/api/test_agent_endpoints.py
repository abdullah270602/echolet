"""
Integration Tests - Agent API Endpoints

Tests the FastAPI agent endpoints with mocked database.
Verifies request/response flow, validation, and error handling.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

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
def clerk_id() -> str:
    """Test Clerk ID."""
    return "user_test123abc"


@pytest.fixture
def mock_user(user_id, clerk_id):
    """Mock user object."""
    user = MagicMock()
    user.id = user_id
    user.clerk_id = clerk_id
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_agent(user_id, make_agent_config):
    """Mock agent row owned by user_id."""
    agent = MagicMock()
    agent.id = 1
    agent.user_id = user_id
    agent.config = make_agent_config()
    agent.status = "active"
    agent.phone = None
    agent.deleted_at = None
    return agent


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


# =============================================================================
# AGENT SERVICE FLOWS (real service logic, repository mocked)
# =============================================================================


class TestAgentCreateFlow:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_agent_persists_config_as_dict(self, mock_user, mock_agent, mock_db_session, make_agent_config):
        from app.services import agent_service
        from app.db.repos import agent_repo
        from app.schemas.agent import AgentCreateRequest

        data = AgentCreateRequest(config=make_agent_config(), status="active", phone="+15550001")

        with patch.object(agent_repo, "get_user_agent_count", return_value=0), \
             patch.object(agent_repo, "create", return_value=mock_agent) as create:
            result = await agent_service.create_agent(mock_db_session, mock_user.id, data)

        assert result is mock_agent
        kwargs = create.call_args.kwargs
        assert kwargs["user_id"] == mock_user.id
        assert kwargs["status"] == "active"
        assert kwargs["phone"] == "+15550001"
        # JSONB-ready plain dict with schema defaults filled in
        assert isinstance(kwargs["config"], dict)
        assert kwargs["config"]["agent"]["name"] == "Test Agent"
        assert kwargs["config"]["voice"]["language"] == "en-US"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_agent_at_limit_fails(self, mock_user, mock_db_session, make_agent_config):
        from app.services import agent_service
        from app.db.repos import agent_repo
        from app.schemas.agent import AgentCreateRequest

        data = AgentCreateRequest(config=make_agent_config())

        with patch.object(agent_repo, "get_user_agent_count", return_value=agent_service.MAX_AGENTS_PER_USER), \
             patch.object(agent_repo, "create") as create:
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.create_agent(mock_db_session, mock_user.id, data)

        assert exc_info.value.status_code == 400
        assert "limit" in exc_info.value.detail.lower()
        create.assert_not_called()

    @pytest.mark.integration
    def test_create_request_requires_config_and_identity(self, make_agent_config):
        from pydantic import ValidationError
        from app.schemas.agent import AgentCreateRequest

        with pytest.raises(ValidationError):
            AgentCreateRequest()
        with pytest.raises(ValidationError):
            AgentCreateRequest(config=make_agent_config(agent={"name": "no business"}))


class TestAgentGetFlow:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_own_agent(self, mock_user, mock_agent, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent):
            result = await agent_service.get_agent(mock_db_session, mock_user.id, 1)

        assert result.config["agent"]["name"] == "Test Agent"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_other_user_agent_forbidden(self, mock_agent, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.get_agent(mock_db_session, uuid.uuid4(), 1)

        assert exc_info.value.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_nonexistent_agent_404(self, mock_user, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo

        with patch.object(agent_repo, "get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.get_agent(mock_db_session, mock_user.id, 999)

        assert exc_info.value.status_code == 404


class TestAgentUpdateFlow:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_replaces_config_and_status(self, mock_user, mock_agent, mock_db_session, make_agent_config):
        from app.services import agent_service
        from app.db.repos import agent_repo
        from app.schemas.agent import AgentUpdateRequest

        cfg = make_agent_config(agent={"name": "Updated", "business_name": "Biz"})
        with patch.object(agent_repo, "get_by_id", return_value=mock_agent), \
             patch.object(agent_repo, "update", return_value=mock_agent) as update:
            await agent_service.update_agent(
                mock_db_session, mock_user.id, 1, AgentUpdateRequest(config=cfg, status="paused")
            )

        kwargs = update.call_args.kwargs
        assert kwargs["config"]["agent"]["name"] == "Updated"
        assert kwargs["status"] == "paused"
        assert kwargs["phone"] is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_status_only_update_leaves_config_untouched(self, mock_user, mock_agent, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo
        from app.schemas.agent import AgentUpdateRequest

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent), \
             patch.object(agent_repo, "update", return_value=mock_agent) as update:
            await agent_service.update_agent(mock_db_session, mock_user.id, 1, AgentUpdateRequest(status="active"))

        assert update.call_args.kwargs["config"] is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_other_user_agent_forbidden(self, mock_agent, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo
        from app.schemas.agent import AgentUpdateRequest

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent), \
             patch.object(agent_repo, "update") as update:
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.update_agent(mock_db_session, uuid.uuid4(), 1, AgentUpdateRequest(status="active"))

        assert exc_info.value.status_code == 403
        update.assert_not_called()


class TestAgentDeleteFlow:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_own_agent_soft_deletes(self, mock_user, mock_agent, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent), \
             patch.object(agent_repo, "soft_delete") as soft_delete:
            await agent_service.delete_agent(mock_db_session, mock_user.id, 1)

        soft_delete.assert_called_once_with(mock_db_session, mock_agent)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_other_user_agent_forbidden(self, mock_agent, mock_db_session):
        from app.services import agent_service
        from app.db.repos import agent_repo

        with patch.object(agent_repo, "get_by_id", return_value=mock_agent), \
             patch.object(agent_repo, "soft_delete") as soft_delete:
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.delete_agent(mock_db_session, uuid.uuid4(), 1)

        assert exc_info.value.status_code == 403
        soft_delete.assert_not_called()


# =============================================================================
# USAGE ENDPOINT TESTS
# =============================================================================


class TestUsageEndpoints:
    """Integration tests for usage-related endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_usage_within_limit(self, mock_user, mock_db_session):
        """Integration: Check usage returns allowed when within limit."""
        from app.services import usage_service
        from app.db.repos import usage_repo

        with patch("app.services.usage_service.DAILY_TALK_LIMIT_SECONDS", 3600), \
             patch.object(usage_repo, "get_daily_usage", return_value=1000):
            result = await usage_service.check_user_limit(mock_db_session, mock_user.id)

            assert result["allowed"] is True
            assert result["remaining_seconds"] == 2600

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_usage_at_limit(self, mock_user, mock_db_session):
        """Integration: Check usage returns blocked when at limit."""
        from app.services import usage_service
        from app.db.repos import usage_repo

        with patch("app.services.usage_service.DAILY_TALK_LIMIT_SECONDS", 3600), \
             patch.object(usage_repo, "get_daily_usage", return_value=3600):
            result = await usage_service.check_user_limit(mock_db_session, mock_user.id)

            assert result["allowed"] is False
            assert result["remaining_seconds"] == 0
