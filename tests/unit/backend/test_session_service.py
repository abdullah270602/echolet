"""start_session: the only path that mints a token for a user's own agent."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services import session_service


@pytest.fixture
def owner():
    return uuid.uuid4()


def _patches(agent, allowed=True, active=None):
    usage = {"allowed": allowed, "remaining_seconds": 300 if allowed else 0}
    return (
        patch.object(session_service.agent_repo, "get_active_by_id", AsyncMock(return_value=agent)),
        patch.object(session_service.session_repo, "lock_user", AsyncMock()),
        patch.object(session_service.session_repo, "get_active_for_user", AsyncMock(return_value=active)),
        patch.object(session_service.usage_service, "check_user_limit", AsyncMock(return_value=usage)),
        patch.object(session_service.session_repo, "create",
                     AsyncMock(return_value=MagicMock(id=7, room_name="room-uuid"))),
        patch.object(session_service, "create_access_token",
                     return_value={"token": "t", "identity": "i", "livekit_url": "wss://x"}),
    )


async def _start(agent, user_id, allowed=True, active=None):
    p1, p_lock, p_active, p2, p3, p4 = _patches(agent, allowed, active)
    db = AsyncMock()
    with p1, p_lock, p_active, p2, p3 as create_session, p4 as mint:
        try:
            return await session_service.start_session(db, user_id, 1), create_session, mint
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


@pytest.mark.asyncio
async def test_live_call_blocks_a_second_one_with_409(owner):
    err, create_session, mint = await _start(
        MagicMock(user_id=owner), owner, active=MagicMock(id=3)
    )
    assert err.status_code == 409
    assert "in progress" in err.detail
    create_session.assert_not_awaited()
    mint.assert_not_called()


@pytest.mark.asyncio
async def test_active_check_uses_the_stale_cutoff_and_runs_after_locking(owner):
    p1, p_lock, p_active, p2, p3, p4 = _patches(MagicMock(user_id=owner))
    order = []
    with p1, p_lock as lock, p_active as active, p2, p3, p4:
        lock.side_effect = lambda *a, **k: order.append("lock")
        active.side_effect = lambda *a, **k: order.append("check")
        await session_service.start_session(AsyncMock(), owner, 1)
    assert order == ["lock", "check"]
    assert active.call_args.args[1:] == (owner, session_service.ACTIVE_SESSION_MAX_AGE_MINUTES)


def test_stale_cutoff_is_in_the_query():
    """get_active_for_user ignores ended calls and rows older than the cutoff."""
    from sqlalchemy.dialects import postgresql
    from app.db.repos import session_repo

    captured = {}

    class _Db:
        async def execute(self, stmt):
            captured["sql"] = str(stmt.compile(dialect=postgresql.dialect()))
            return MagicMock(scalar_one_or_none=lambda: None)

    import asyncio
    asyncio.run(session_repo.get_active_for_user(_Db(), uuid.uuid4(), 15))
    sql = captured["sql"]
    assert "ended_at IS NULL" in sql
    assert "now() - interval '15 minutes'" in sql
