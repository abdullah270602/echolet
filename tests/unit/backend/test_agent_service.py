"""
Phase 2: Backend API Unit Tests - Agent Service

Tests for agent CRUD operations, authorization checks, and limit enforcement.

Test Categories:
- SP (Sole Purpose): Agent limit always enforced, data isolation maintained
- BREAK: IDOR attacks, bypassing limits, unauthorized access
- EDGE: Boundary conditions
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))

from app.services import agent_service
from app.schemas.agent import AgentCreateRequest, AgentUpdateRequest


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user_a_id() -> uuid.UUID:
    """User A's UUID."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def user_b_id() -> uuid.UUID:
    """User B's UUID (different user for IDOR tests)."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_agent(user_a_id: uuid.UUID) -> MagicMock:
    """Mock agent belonging to User A."""
    agent = MagicMock()
    agent.id = 1
    agent.user_id = user_a_id
    agent.name = "Test Agent"
    agent.business_name = "Test Business"
    agent.deleted_at = None
    return agent


@pytest.fixture
def agent_create_data() -> AgentCreateRequest:
    """Valid agent creation request."""
    return AgentCreateRequest(
        name="New Agent",
        business_name="New Business",
        voice_id="Ashley",
        greeting_message="Hello!",
        tone="professional",
    )


@pytest.fixture
def agent_update_data() -> AgentUpdateRequest:
    """Valid agent update request."""
    return AgentUpdateRequest(name="Updated Agent")


# =============================================================================
# SOLE PURPOSE TESTS: Data Isolation (IDOR Prevention)
# =============================================================================


class TestDataIsolation:
    """Tests ensuring users can only access their own agents."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_get_own_agent_succeeds(
        self, mock_session, user_a_id, mock_agent
    ):
        """SP-ISO-002: User can get their own agent."""
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ):
            result = await agent_service.get_agent(mock_session, user_a_id, 1)
            assert result == mock_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_get_other_user_agent_rejected(
        self, mock_session, user_b_id, mock_agent
    ):
        """SP-ISO-003: User cannot get another user's agent (IDOR)."""
        # mock_agent belongs to user_a, but user_b is requesting
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.get_agent(mock_session, user_b_id, 1)

            assert exc_info.value.status_code == 403
            assert "Not authorized" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_update_own_agent_succeeds(
        self, mock_session, user_a_id, mock_agent, agent_update_data
    ):
        """SP-ISO-004: User can update their own agent."""
        updated_agent = MagicMock()
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ), patch.object(
            agent_service.agent_repo, "update", return_value=updated_agent
        ):
            result = await agent_service.update_agent(
                mock_session, user_a_id, 1, agent_update_data
            )
            assert result == updated_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_update_other_user_agent_rejected(
        self, mock_session, user_b_id, mock_agent, agent_update_data
    ):
        """SP-ISO-005: User cannot update another user's agent (IDOR)."""
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.update_agent(
                    mock_session, user_b_id, 1, agent_update_data
                )

            assert exc_info.value.status_code == 403
            assert "Not authorized to update" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_delete_own_agent_succeeds(
        self, mock_session, user_a_id, mock_agent
    ):
        """SP-ISO-006: User can delete their own agent."""
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ), patch.object(agent_service.agent_repo, "soft_delete") as mock_delete:
            await agent_service.delete_agent(mock_session, user_a_id, 1)
            mock_delete.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_delete_other_user_agent_rejected(
        self, mock_session, user_b_id, mock_agent
    ):
        """SP-ISO-007: User cannot delete another user's agent (IDOR)."""
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.delete_agent(mock_session, user_b_id, 1)

            assert exc_info.value.status_code == 403
            assert "Not authorized to delete" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_list_only_own_agents(self, mock_session, user_a_id):
        """SP-ISO-001: List agents only returns user's own agents."""
        user_agents = [MagicMock(), MagicMock()]
        with patch.object(
            agent_service.agent_repo, "get_by_user_id", return_value=user_agents
        ) as mock_get:
            result = await agent_service.list_agents(mock_session, user_a_id)

            mock_get.assert_called_once_with(mock_session, user_a_id)
            assert result == user_agents


# =============================================================================
# SOLE PURPOSE TESTS: Agent Limit Enforcement (Max 3)
# =============================================================================


class TestAgentLimitEnforcement:
    """Tests ensuring max 3 agents per user is always enforced."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_create_first_agent_allowed(
        self, mock_session, user_a_id, agent_create_data
    ):
        """SP-LIMIT-001: User with 0 agents can create."""
        new_agent = MagicMock()
        with patch.object(
            agent_service.agent_repo, "get_user_agent_count", return_value=0
        ), patch.object(
            agent_service.agent_repo, "create", return_value=new_agent
        ):
            result = await agent_service.create_agent(
                mock_session, user_a_id, agent_create_data
            )
            assert result == new_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_create_second_agent_allowed(
        self, mock_session, user_a_id, agent_create_data
    ):
        """SP-LIMIT-002: User with 1 agent can create."""
        new_agent = MagicMock()
        with patch.object(
            agent_service.agent_repo, "get_user_agent_count", return_value=1
        ), patch.object(
            agent_service.agent_repo, "create", return_value=new_agent
        ):
            result = await agent_service.create_agent(
                mock_session, user_a_id, agent_create_data
            )
            assert result == new_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_create_third_agent_allowed(
        self, mock_session, user_a_id, agent_create_data
    ):
        """SP-LIMIT-003: User with 2 agents can create."""
        new_agent = MagicMock()
        with patch.object(
            agent_service.agent_repo, "get_user_agent_count", return_value=2
        ), patch.object(
            agent_service.agent_repo, "create", return_value=new_agent
        ):
            result = await agent_service.create_agent(
                mock_session, user_a_id, agent_create_data
            )
            assert result == new_agent

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_create_fourth_agent_blocked(
        self, mock_session, user_a_id, agent_create_data
    ):
        """SP-LIMIT-004: User with 3 agents CANNOT create fourth."""
        with patch.object(
            agent_service.agent_repo, "get_user_agent_count", return_value=3
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.create_agent(
                    mock_session, user_a_id, agent_create_data
                )

            assert exc_info.value.status_code == 400
            assert "Agent limit reached" in exc_info.value.detail
            assert "3" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_create_blocked_at_exactly_limit(
        self, mock_session, user_a_id, agent_create_data
    ):
        """SP: Boundary test - exactly at limit should block."""
        # DEFAULT_CONFIG.max_agents_per_user = 3
        with patch.object(
            agent_service.agent_repo, "get_user_agent_count", return_value=3
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.create_agent(
                    mock_session, user_a_id, agent_create_data
                )

            assert exc_info.value.status_code == 400


# =============================================================================
# BREAK-IT TESTS: Bypass Attempts
# =============================================================================


class TestBreakItScenarios:
    """Adversarial tests attempting to bypass security controls."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_idor_sequential_enumeration(
        self, mock_session, user_b_id
    ):
        """BREAK-P2-B1: Sequential ID enumeration should be blocked."""
        # User B tries to access agents with IDs 1, 2, 3 (belonging to others)
        for agent_id in [1, 2, 3]:
            mock_agent = MagicMock()
            mock_agent.id = agent_id
            mock_agent.user_id = uuid.uuid4()  # Random other user

            with patch.object(
                agent_service.agent_repo, "get_by_id", return_value=mock_agent
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await agent_service.get_agent(mock_session, user_b_id, agent_id)

                assert exc_info.value.status_code == 403

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_agent_not_found(self, mock_session, user_a_id):
        """BREAK: Requesting non-existent agent returns 404."""
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=None
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.get_agent(mock_session, user_a_id, 99999)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_delete_already_deleted(
        self, mock_session, user_a_id
    ):
        """BREAK-STATE-004: Double delete should fail."""
        mock_agent = MagicMock()
        mock_agent.user_id = user_a_id
        mock_agent.deleted_at = datetime.now(timezone.utc)  # Already deleted

        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ):
            with pytest.raises(HTTPException) as exc_info:
                await agent_service.delete_agent(mock_session, user_a_id, 1)

            assert exc_info.value.status_code == 400
            assert "already deleted" in exc_info.value.detail.lower()


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests for agent service."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_empty_agent_list(self, mock_session, user_a_id):
        """EDGE: New user with no agents."""
        with patch.object(
            agent_service.agent_repo, "get_by_user_id", return_value=[]
        ):
            result = await agent_service.list_agents(mock_session, user_a_id)
            assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_update_with_no_changes(
        self, mock_session, user_a_id, mock_agent
    ):
        """EDGE: Update with empty request should still work."""
        empty_update = AgentUpdateRequest()  # No fields set
        with patch.object(
            agent_service.agent_repo, "get_by_id", return_value=mock_agent
        ), patch.object(
            agent_service.agent_repo, "update", return_value=mock_agent
        ) as mock_update:
            result = await agent_service.update_agent(
                mock_session, user_a_id, 1, empty_update
            )
            mock_update.assert_called_once()
