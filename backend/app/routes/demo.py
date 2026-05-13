from fastapi import APIRouter, HTTPException, Request

from app import config
from app.schemas.demo import DemoSessionResponse
from app.services.demo_service import DemoRateLimiter, build_demo_session
from app.services.livekit_service import create_access_token

router = APIRouter()

limiter = DemoRateLimiter(
    per_ip_per_hour=config.DEMO_SESSIONS_PER_IP_PER_HOUR,
    per_day=config.DEMO_SESSIONS_PER_DAY,
)


@router.post("/session", response_model=DemoSessionResponse)
async def start_demo_session(request: Request) -> DemoSessionResponse:
    """Mint a short-lived LiveKit token for an anonymous call with the demo agent."""
    if not (config.DEMO_ENABLED and config.LIVEKIT_API_KEY and config.LIVEKIT_API_SECRET):
        raise HTTPException(status_code=503, detail="The live demo is unavailable right now.")

    # Behind Caddy, uvicorn's --proxy-headers sets client.host from X-Forwarded-For.
    ip = request.client.host if request.client else "unknown"
    reason = limiter.check(ip)
    if reason:
        raise HTTPException(status_code=429, detail=reason)

    demo = build_demo_session(config.DEMO_MAX_SECONDS)
    token = create_access_token(
        room_name=demo["room_name"],
        name="Demo visitor",
        metadata=demo["metadata"],
        ttl=demo["ttl"],
    )
    return DemoSessionResponse(
        token=token["token"],
        livekit_url=token["livekit_url"],
        room_name=token["room_name"],
        max_seconds=config.DEMO_MAX_SECONDS,
    )
