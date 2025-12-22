from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.database import get_async_session
from app.schemas.session import SessionStartRequest, SessionStartResponse
from app.services import session_service

router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    request: SessionStartRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SessionStartResponse:
    """
    Start a new voice session with a specific agent.

    - Validates agent exists and belongs to user
    - Checks daily usage limit
    - Creates CallSession record
    - Returns LiveKit token and session info

    Returns 404 if agent not found.
    Returns 403 if not authorized or daily limit reached.
    """
    user_id = current_user["user_id"]
    result = await session_service.start_session(
        session,
        user_id=user_id,
        agent_id=request.agent_id,
    )
    return SessionStartResponse(**result)
