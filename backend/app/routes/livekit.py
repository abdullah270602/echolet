from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.livekit import TokenRequest, TokenResponse
from app.schemas.usage import UsageRecordRequest, UsageStatus
from app.services.livekit_service import create_access_token
from app.services import usage_service
from app.config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET
from app.auth import get_current_user
from app.db.database import get_async_session

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def get_token(
    request: TokenRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """
    Generate a LiveKit access token for voice-only room access.
    Requires Clerk authentication.

    The user's Clerk ID is used as the participant identity.
    - room_name: Room to join (auto-generated if not provided)
    - name: Display name for the participant

    Returns 403 if daily talk limit has been reached.
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="LiveKit API credentials not configured",
        )

    # Use Clerk user_id as the participant identity
    identity = current_user["user_id"]

    # Check usage limit
    usage = await usage_service.check_user_limit(session, identity)
    if not usage["allowed"]:
        raise HTTPException(
            status_code=403,
            detail="Daily talk limit reached. Please try again tomorrow.",
        )

    result = create_access_token(
        room_name=request.room_name,
        identity=identity,
        name=request.name,
        remaining_seconds=usage["remaining_seconds"],
    )

    return TokenResponse(**result, remaining_seconds=usage["remaining_seconds"])


@router.get("/usage", response_model=UsageStatus)
async def get_usage(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> UsageStatus:
    """
    Get current usage status for the authenticated user.
    Returns used_seconds, remaining_seconds, and limit_seconds.
    """
    identity = current_user["user_id"]
    result = await usage_service.check_user_limit(session, identity)
    return UsageStatus(
        remaining_seconds=result["remaining_seconds"],
        used_seconds=result["used_seconds"],
        limit_seconds=result["limit_seconds"],
    )


@router.post("/usage", response_model=UsageStatus)
async def record_usage(
    request: UsageRecordRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> UsageStatus:
    """
    Record talk time usage for the current user.
    Called by the agent when a session ends.
    """
    identity = current_user["user_id"]
    result = await usage_service.record_usage(session, identity, request.talk_seconds)
    return UsageStatus(**result)
