import json
import uuid
from datetime import timedelta

from livekit.api import AccessToken, VideoGrants

from app.config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL


def create_access_token(
    room_name: str | None = None,
    identity: str | None = None,
    name: str | None = None,
    remaining_seconds: int | None = None,
) -> dict:
    """
    Generate a LiveKit access token for voice-only communication.

    Args:
        room_name: Optional room name. Auto-generated UUID if not provided.
        identity: Optional participant identity. Auto-generated UUID if not provided.
        name: Optional display name for the participant.
        remaining_seconds: Optional remaining talk time in seconds (for usage limits).

    Returns:
        Dictionary containing token, room_name, identity, and livekit_url.
    """
    room = room_name or str(uuid.uuid4())
    participant_identity = identity or str(uuid.uuid4())

    # Voice-only grants - microphone only, no video
    grants = VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_publish_sources=["microphone"],
        can_subscribe=True,
        can_publish_data=True,
    )

    token = AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
    token.with_identity(participant_identity)
    token.with_grants(grants)
    token.with_ttl(timedelta(minutes=10))

    if name:
        token.with_name(name)

    # Include remaining_seconds in participant metadata for agent to read
    if remaining_seconds is not None:
        metadata = json.dumps({"remaining_seconds": remaining_seconds})
        token.with_metadata(metadata)

    return {
        "token": token.to_jwt(),
        "room_name": room,
        "identity": participant_identity,
        "livekit_url": LIVEKIT_URL,
    }
