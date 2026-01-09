from datetime import datetime
from typing import Optional, Any

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


class TranscriptMessage(BaseModel):
    """A single message in a call transcript."""

    role: str  # "user" or "agent"
    content: str
    timestamp: float
    language: Optional[str] = None


class CallHistoryResponse(BaseModel):
    """Response for a single call history entry."""

    id: int
    room_name: str
    agent_id: int
    status: str
    duration_seconds: Optional[int] = None
    transcript: Optional[list[dict[str, Any]]] = None
    summary: Optional[str] = None
    priority: str = "normal"
    created_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    # Analysis fields
    category: Optional[str] = None
    urgency: Optional[str] = None
    sentiment: Optional[str] = None
    action_required: Optional[bool] = None
    action_items: Optional[list[str]] = None

    class Config:
        from_attributes = True
