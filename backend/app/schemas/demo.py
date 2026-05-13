from pydantic import BaseModel


class DemoSessionResponse(BaseModel):
    token: str
    livekit_url: str
    room_name: str
    max_seconds: int
