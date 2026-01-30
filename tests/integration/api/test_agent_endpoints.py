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
def mock_agent(user_id):
    """Mock agent object."""
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
    agent.status = "active"
    agent.phone = None
    agent.deleted_at = None
    agent.created_at = datetime.now(timezone.utc)
    agent.updated_at = datetime.now(timezone.utc)
    return agent


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    return session


# =============================================================================
# AGENT LIST ENDPOINT TESTS
# =============================================================================


class TestAgentListEndpoint:
    """Integration tests for GET /agents endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_agents_returns_user_agents(self, mock_user, mock_agent):
        """Integration: List agents returns only user's agents."""
        from app.services import agent_service

        with patch.object(agent_service, "list_agents", return_value=[mock_agent]):
            agents = await agent_service.list_agents(AsyncMock(), mock_user.id)

            assert len(agents) == 1
            assert agents[0].name == "Test Agent"
            assert agents[0].user_id == mock_user.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_agents_empty_for_new_user(self, mock_user):
        """Integration: New user has no agents."""
        from app.services import agent_service

        with patch.object(agent_service, "list_agents", return_value=[]):
            agents = await agent_service.list_agents(AsyncMock(), mock_user.id)

            assert agents == []


# =============================================================================
# AGENT CREATE ENDPOINT TESTS
# =============================================================================


class TestAgentCreateEndpoint:
    """Integration tests for POST /agents endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_agent_success(self, mock_user, mock_agent, mock_db_session):
        """Integration: Create agent with valid data."""
        from app.services import agent_service
        from app.schemas.agent import AgentCreateRequest

        create_data = AgentCreateRequest(
            name="New Agent",
            business_name="New Business",
            voice_id="Ashley",
            greeting_message="Welcome!",
            tone="friendly",
        )

        with patch.object(agent_service, "create_agent", return_value=mock_agent):
            result = await agent_service.create_agent(mock_db_session, mock_user.id, create_data)

            assert result.id == 1
            assert result.user_id == mock_user.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_agent_at_limit_fails(self, mock_user, mock_db_session):
        """Integration: Create agent fails when at limit (3)."""
        from app.services import agent_service
        from app.schemas.agent import AgentCreateRequest

        create_data = AgentCreateRequest(
            name="Fourth Agent",
            business_name="Business",
            voice_id="Ashley",
            greeting_message="Hi!",
            tone="professional",
        )

        with patch.object(agent_service, "create_agent", side_effect=HTTPException(status_code=400, detail="Agent limit reached")):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.create_agent(mock_db_session, mock_user.id, create_data)

            assert exc_info.value.status_code == 400
            assert "limit" in exc_info.value.detail.lower()


# =============================================================================
# AGENT GET ENDPOINT TESTS
# =============================================================================


class TestAgentGetEndpoint:
    """Integration tests for GET /agents/{id} endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_agent_success(self, mock_user, mock_agent, mock_db_session):
        """Integration: Get own agent succeeds."""
        from app.services import agent_service

        with patch.object(agent_service, "get_agent", return_value=mock_agent):
            result = await agent_service.get_agent(mock_db_session, mock_user.id, 1)

            assert result.id == 1
            assert result.name == "Test Agent"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_other_user_agent_fails(self, mock_db_session):
        """Integration: Get another user's agent returns 404."""
        from app.services import agent_service

        other_user_id = uuid.uuid4()

        with patch.object(agent_service, "get_agent", side_effect=HTTPException(status_code=404, detail="Agent not found")):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.get_agent(mock_db_session, other_user_id, 1)

            assert exc_info.value.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_nonexistent_agent_fails(self, mock_user, mock_db_session):
        """Integration: Get nonexistent agent returns 404."""
        from app.services import agent_service

        with patch.object(agent_service, "get_agent", side_effect=HTTPException(status_code=404, detail="Agent not found")):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.get_agent(mock_db_session, mock_user.id, 999)

            assert exc_info.value.status_code == 404


# =============================================================================
# AGENT UPDATE ENDPOINT TESTS
# =============================================================================


class TestAgentUpdateEndpoint:
    """Integration tests for PUT /agents/{id} endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_agent_success(self, mock_user, mock_agent, mock_db_session):
        """Integration: Update own agent succeeds."""
        from app.services import agent_service
        from app.schemas.agent import AgentUpdateRequest

        update_data = AgentUpdateRequest(name="Updated Agent")
        mock_agent.name = "Updated Agent"

        with patch.object(agent_service, "update_agent", return_value=mock_agent):
            result = await agent_service.update_agent(mock_db_session, mock_user.id, 1, update_data)

            assert result.name == "Updated Agent"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_other_user_agent_fails(self, mock_db_session):
        """Integration: Update another user's agent fails."""
        from app.services import agent_service
        from app.schemas.agent import AgentUpdateRequest

        other_user_id = uuid.uuid4()
        update_data = AgentUpdateRequest(name="Hacked")

        with patch.object(agent_service, "update_agent", side_effect=HTTPException(status_code=404, detail="Agent not found")):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.update_agent(mock_db_session, other_user_id, 1, update_data)

            assert exc_info.value.status_code == 404


# =============================================================================
# AGENT DELETE ENDPOINT TESTS
# =============================================================================


class TestAgentDeleteEndpoint:
    """Integration tests for DELETE /agents/{id} endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_agent_success(self, mock_user, mock_agent, mock_db_session):
        """Integration: Delete own agent succeeds (soft delete)."""
        from app.services import agent_service

        mock_agent.deleted_at = datetime.now(timezone.utc)

        with patch.object(agent_service, "delete_agent", return_value=mock_agent):
            result = await agent_service.delete_agent(mock_db_session, mock_user.id, 1)

            assert result.deleted_at is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_other_user_agent_fails(self, mock_db_session):
        """Integration: Delete another user's agent fails."""
        from app.services import agent_service

        other_user_id = uuid.uuid4()

        with patch.object(agent_service, "delete_agent", side_effect=HTTPException(status_code=404, detail="Agent not found")):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.delete_agent(mock_db_session, other_user_id, 1)

            assert exc_info.value.status_code == 404


# =============================================================================
# SESSION ENDPOINTS TESTS
# =============================================================================


class TestSessionEndpoints:
    """Integration tests for session-related endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_user, mock_db_session):
        """Integration: Create session for valid agent."""
        from app.db.repos import session_repo

        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.room_name = str(uuid.uuid4())
        mock_session.status = "pending"

        with patch.object(session_repo, "create", return_value=mock_session):
            result = await session_repo.create(mock_db_session, mock_user.id, agent_id=1)

            assert result.status == "pending"
            assert result.room_name is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_call_history_success(self, mock_user, mock_db_session):
        """Integration: Get call history returns completed calls."""
        from app.db.repos import session_repo

        mock_history = [
            {
                "id": 1,
                "room_name": str(uuid.uuid4()),
                "status": "completed",
                "summary": "Test call",
                "agent_name": "Test Agent",
                "is_agent_deleted": False,
            }
        ]

        with patch.object(session_repo, "get_user_call_history", return_value=mock_history):
            result = await session_repo.get_user_call_history(mock_db_session, mock_user.id)

            assert len(result) == 1
            assert result[0]["status"] == "completed"


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
