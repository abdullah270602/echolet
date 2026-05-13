"""Clerk user.created webhook seeds a usable starter agent."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.agent import AgentConfigData


class TestUserCreatedSeedsStarterAgent:
    @pytest.mark.asyncio
    async def test_new_user_gets_valid_starter_agent(self):
        from app.webhook_handlers import user_events

        user = MagicMock(id=uuid.uuid4())
        session = AsyncMock()
        with patch.object(user_events.user_repo, "upsert_user", AsyncMock(return_value=user)), \
             patch.object(user_events.agent_repo, "get_user_agent_count", AsyncMock(return_value=0)), \
             patch.object(user_events.agent_repo, "create", AsyncMock()) as create:
            await user_events.handle_user_created(
                session,
                {"id": "user_abc", "primary_email_address_id": "e1",
                 "email_addresses": [{"id": "e1", "email_address": "a@b.co"}]},
            )

        create.assert_awaited_once()
        kwargs = create.await_args.kwargs
        assert kwargs["user_id"] == user.id
        assert kwargs["status"] == "active"
        # Must round-trip through the API schema, i.e. the dashboard can load it.
        AgentConfigData.model_validate(kwargs["config"])

    @pytest.mark.asyncio
    async def test_existing_agents_are_not_reseeded(self):
        from app.webhook_handlers import user_events

        with patch.object(user_events.user_repo, "upsert_user", AsyncMock(return_value=MagicMock())), \
             patch.object(user_events.agent_repo, "get_user_agent_count", AsyncMock(return_value=1)), \
             patch.object(user_events.agent_repo, "create", AsyncMock()) as create:
            await user_events.handle_user_created(AsyncMock(), {"id": "user_abc"})
        create.assert_not_awaited()
