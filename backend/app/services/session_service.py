import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repos import agent_repo, session_repo
from app.services.livekit_service import create_access_token
from app.services import usage_service


# Usage is only written when a call ends, so without this guard N tabs would each
# get the full remaining allowance. Un-ended rows older than this are crashed calls.
ACTIVE_SESSION_MAX_AGE_MINUTES = 15


async def start_session(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    agent_id: int,
) -> dict:
    """
    Start a new call session for the specified agent.

    1. Validates agent exists and belongs to user
    2. Refuses if the user already has a live call (409)
    3. Checks user's usage limit
    4. Creates CallSession record with UUID room_name
    5. Mints LiveKit token with session UUID as room_name

    Args:
        db_session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID to use for this session

    Returns:
        dict with token, room_name, session_id, identity, livekit_url, remaining_seconds

    Raises:
        HTTPException: 404 if agent not found or soft-deleted
        HTTPException: 409 if the user already has an active call
        HTTPException: 403 if user not authorized or usage limit reached
    """
    # 1. Validate agent exists and belongs to user
    agent = await agent_repo.get_active_by_id(db_session, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to use this agent")

    # 2. One live call per user. Row-locking the user serialises concurrent
    # start_session calls (double click, many tabs): the second waits until the
    # first has committed its call_session, then sees it below. Chosen over a
    # partial unique index because crashed calls leave ended_at NULL forever and
    # an index cannot express "...and started recently". Lock is released by
    # session_repo.create()'s commit (or on rollback if we raise).
    await session_repo.lock_user(db_session, user_id)
    active = await session_repo.get_active_for_user(
        db_session, user_id, ACTIVE_SESSION_MAX_AGE_MINUTES
    )
    if active:
        await db_session.rollback()  # release the user lock
        raise HTTPException(
            status_code=409,
            detail="You already have a call in progress. End it before starting another.",
        )

    # 3. Check usage limit
    usage = await usage_service.check_user_limit(db_session, user_id)
    if not usage["allowed"]:
        await db_session.rollback()  # release the user lock
        raise HTTPException(
            status_code=403,
            detail="Daily talk limit reached. Please try again tomorrow.",
        )

    # 4. Create CallSession record
    call_session = await session_repo.create(
        db_session,
        user_id=user_id,
        agent_id=agent_id,
    )

    # 5. Mint LiveKit token with session room_name (UUID)
    # Use string representation of UUID for LiveKit identity
    token_result = create_access_token(
        room_name=call_session.room_name,
        identity=str(user_id),
        name=None,
    )

    return {
        "token": token_result["token"],
        "room_name": call_session.room_name,
        "session_id": call_session.id,
        "identity": token_result["identity"],
        "livekit_url": token_result["livekit_url"],
        "remaining_seconds": usage["remaining_seconds"],
    }
