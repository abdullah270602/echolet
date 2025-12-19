from fastapi import APIRouter, HTTPException

from app.schemas.livekit import TokenRequest, TokenResponse
from app.services.livekit_service import create_access_token
from app.config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def get_token(request: TokenRequest) -> TokenResponse:
    """
    Generate a LiveKit access token for voice-only room access.

    All parameters are optional:
    - room_name: Room to join (auto-generated if not provided)
    - identity: Participant identity (auto-generated if not provided)
    - name: Display name for the participant
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="LiveKit API credentials not configured",
        )

    result = create_access_token(
        room_name=request.room_name,
        identity=request.identity,
        name=request.name,
    )

    return TokenResponse(**result)
