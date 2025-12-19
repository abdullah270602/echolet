from pydantic import BaseModel


class TokenRequest(BaseModel):
    room_name: str | None = None
    identity: str | None = None
    name: str | None = None


class TokenResponse(BaseModel):
    token: str
    room_name: str
    identity: str
    livekit_url: str
