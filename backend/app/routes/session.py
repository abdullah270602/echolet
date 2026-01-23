from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_with_db
from app.db.database import get_async_session
from app.db.repos import session_repo
from app.schemas.session import SessionStartRequest, SessionStartResponse, CallHistoryResponse
from app.services import session_service

router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    request: SessionStartRequest,
    current_user: dict = Depends(get_current_user_with_db),
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
    user_id = current_user["id"]
    result = await session_service.start_session(
        session,
        user_id=user_id,
        agent_id=request.agent_id,
    )
    return SessionStartResponse(**result)


@router.get("/history", response_model=list[CallHistoryResponse])
async def get_call_history(
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, le=100, ge=1),
) -> list[CallHistoryResponse]:
    """
    Get the user's call history with transcripts.

    - Returns completed and failed calls ordered by most recent first
    - Includes full transcript if available
    - Limited to 100 records max per request

    Args:
        limit: Maximum number of records to return (default: 50, max: 100)
    """
    user_id = current_user["id"]
    call_sessions = await session_repo.get_user_call_history(
        session,
        user_id=user_id,
        limit=limit,
    )
    return [CallHistoryResponse.model_validate(cs) for cs in call_sessions]
