from pydantic import BaseModel


class SessionStartRequest(BaseModel):
    """Request body for starting a new session."""

    agent_id: int


class SessionStartResponse(BaseModel):
    """Response for session start containing LiveKit connection details."""

    token: str
    room_name: str
    session_id: int
    identity: str
    livekit_url: str
    remaining_seconds: int
