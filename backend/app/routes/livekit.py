from fastapi import APIRouter, Depends, HTTPException

from app.schemas.livekit import TokenRequest, TokenResponse
from app.services.livekit_service import create_access_token
from app.config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET
from app.auth import get_current_user

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def get_token(
    request: TokenRequest,
    current_user: dict = Depends(get_current_user),
) -> TokenResponse:
    """
    Generate a LiveKit access token for voice-only room access.
    Requires Clerk authentication.

    The user's Clerk ID is used as the participant identity.
    - room_name: Room to join (auto-generated if not provided)
    - name: Display name for the participant
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="LiveKit API credentials not configured",
        )

    # Use Clerk user_id as the participant identity
    identity = current_user["user_id"]

    result = create_access_token(
        room_name=request.room_name,
        identity=identity,
        name=request.name,
    )

    return TokenResponse(**result)
