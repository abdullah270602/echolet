"""
Phase 2: Backend API Unit Tests - Usage Service

Tests for daily talk limit enforcement and usage tracking.

Test Categories:
- SP (Sole Purpose): Usage limits always enforced
- BREAK: Attempts to bypass limits
- EDGE: Boundary conditions at limit thresholds
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))

from app.services import usage_service


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
    return AsyncMock()


# =============================================================================
# SOLE PURPOSE TESTS: Usage Limit Enforcement
# =============================================================================


class TestUsageLimitEnforcement:
    """Tests ensuring daily usage limits are always enforced."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_fresh_user_allowed(self, mock_session, user_id):
        """SP-USAGE-001: Fresh user with 0 seconds used is allowed."""
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=0
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", 3600):
            result = await usage_service.check_user_limit(mock_session, user_id)

            assert result["allowed"] is True
            assert result["remaining_seconds"] == 3600
            assert result["used_seconds"] == 0
            assert result["limit_seconds"] == 3600

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_within_limit_allowed(self, mock_session, user_id):
        """SP-USAGE-002: User with 3000 seconds used (600 remaining) is allowed."""
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=3000
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", 3600):
            result = await usage_service.check_user_limit(mock_session, user_id)

            assert result["allowed"] is True
            assert result["remaining_seconds"] == 600
            assert result["used_seconds"] == 3000

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_at_limit_blocked(self, mock_session, user_id):
        """SP-USAGE-003: User with exactly 3600 seconds used is BLOCKED."""
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=3600
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", 3600):
            result = await usage_service.check_user_limit(mock_session, user_id)

            assert result["allowed"] is False
            assert result["remaining_seconds"] == 0
            assert result["used_seconds"] == 3600

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_over_limit_blocked(self, mock_session, user_id):
        """SP-USAGE-004: User with 4000 seconds (over limit) is BLOCKED."""
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=4000
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", 3600):
            result = await usage_service.check_user_limit(mock_session, user_id)

            assert result["allowed"] is False
            assert result["remaining_seconds"] == 0  # max(0, 3600-4000) = 0
            assert result["used_seconds"] == 4000


# =============================================================================
# SOLE PURPOSE TESTS: Usage Recording
# =============================================================================




# =============================================================================
# EDGE CASES: Boundary Conditions
# =============================================================================


class TestEdgeCases:
    """Edge case tests for usage service."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edge_one_second_remaining(self, mock_session, user_id):
        """EDGE: User with exactly 1 second remaining is still allowed."""
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=3599
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", 3600):
            result = await usage_service.check_user_limit(mock_session, user_id)

            assert result["allowed"] is True
            assert result["remaining_seconds"] == 1




# =============================================================================
# BREAK-IT TESTS: Bypass Attempts
# =============================================================================


class TestBreakItScenarios:
    """Adversarial tests attempting to bypass usage limits."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_negative_remaining_clamped(self, mock_session, user_id):
        """BREAK: Negative remaining should be clamped to 0."""
        # If somehow usage > limit, remaining should never be negative
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=5000
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", 3600):
            result = await usage_service.check_user_limit(mock_session, user_id)

            # max(0, 3600-5000) = max(0, -1400) = 0
            assert result["remaining_seconds"] == 0
            assert result["remaining_seconds"] >= 0  # Never negative

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_boundary_at_exact_limit(self, mock_session, user_id):
        """BREAK: Boundary test at exact limit value."""
        limit = 3600
        with patch.object(
            usage_service.usage_repo, "get_daily_usage", return_value=limit
        ), patch.object(usage_service, "DAILY_TALK_LIMIT_SECONDS", limit):
            result = await usage_service.check_user_limit(mock_session, user_id)

            # At exactly the limit, user should be blocked
            assert result["allowed"] is False
            assert result["remaining_seconds"] == 0
