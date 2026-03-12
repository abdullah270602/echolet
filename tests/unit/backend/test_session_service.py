"""start_session: the only path that mints a token for a user's own agent."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services import session_service


@pytest.fixture
def owner():
    return uuid.uuid4()


def _patches(agent, allowed=True):
    usage = {"allowed": allowed, "remaining_seconds": 300 if allowed else 0}
    return (
        patch.object(session_service.agent_repo, "get_by_id", AsyncMock(return_value=agent)),
        patch.object(session_service.usage_service, "check_user_limit", AsyncMock(return_value=usage)),
        patch.object(session_service.session_repo, "create",
                     AsyncMock(return_value=MagicMock(id=7, room_name="room-uuid"))),
        patch.object(session_service, "create_access_token",
                     return_value={"token": "t", "identity": "i", "livekit_url": "wss://x"}),
    )


async def _start(agent, user_id, allowed=True):
    p1, p2, p3, p4 = _patches(agent, allowed)
    with p1, p2, p3 as create_session, p4 as mint:
        try:
            return await session_service.start_session(AsyncMock(), user_id, 1), create_session, mint
        except HTTPException as e:
            return e, create_session, mint


@pytest.mark.asyncio
async def test_unknown_agent_is_404(owner):
    err, create_session, mint = await _start(None, owner)
    assert err.status_code == 404
    create_session.assert_not_awaited()
    mint.assert_not_called()


@pytest.mark.asyncio
async def test_someone_elses_agent_is_403(owner):
    err, create_session, mint = await _start(MagicMock(user_id=uuid.uuid4()), owner)
    assert err.status_code == 403
    create_session.assert_not_awaited()
    mint.assert_not_called()


@pytest.mark.asyncio
async def test_exhausted_daily_limit_is_403(owner):
    err, create_session, mint = await _start(MagicMock(user_id=owner), owner, allowed=False)
    assert err.status_code == 403
    create_session.assert_not_awaited()
    mint.assert_not_called()


@pytest.mark.asyncio
async def test_success_mints_token_for_the_session_room(owner):
    result, create_session, mint = await _start(MagicMock(user_id=owner), owner)
    create_session.assert_awaited_once()
    assert mint.call_args.kwargs["room_name"] == "room-uuid"
    assert mint.call_args.kwargs["identity"] == str(owner)
    assert result["session_id"] == 7
    assert result["remaining_seconds"] == 300
