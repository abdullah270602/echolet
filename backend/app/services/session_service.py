from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repos import agent_repo, session_repo
from app.services.livekit_service import create_access_token
from app.services import usage_service


async def start_session(
    db_session: AsyncSession,
    user_id: str,
    agent_id: int,
) -> dict:
    """
    Start a new call session for the specified agent.

    1. Validates agent exists and belongs to user
    2. Checks user's usage limit
    3. Creates CallSession record with UUID room_name
    4. Mints LiveKit token with session UUID as room_name

    Args:
        db_session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID to use for this session

    Returns:
        dict with token, room_name, session_id, identity, livekit_url, remaining_seconds

    Raises:
        HTTPException: 404 if agent not found
        HTTPException: 403 if user not authorized or usage limit reached
    """
    # 1. Validate agent exists and belongs to user
    agent = await agent_repo.get_by_id(db_session, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to use this agent")

    # 2. Check usage limit
    usage = await usage_service.check_user_limit(db_session, user_id)
    if not usage["allowed"]:
        raise HTTPException(
            status_code=403,
            detail="Daily talk limit reached. Please try again tomorrow.",
        )

    # 3. Create CallSession record
    call_session = await session_repo.create(
        db_session,
        user_id=user_id,
        agent_id=agent_id,
    )

    # 4. Mint LiveKit token with session room_name (UUID)
    token_result = create_access_token(
        room_name=call_session.room_name,
        identity=user_id,
        name=None,
        remaining_seconds=usage["remaining_seconds"],
    )

    return {
        "token": token_result["token"],
        "room_name": call_session.room_name,
        "session_id": call_session.id,
        "identity": token_result["identity"],
        "livekit_url": token_result["livekit_url"],
        "remaining_seconds": usage["remaining_seconds"],
    }
