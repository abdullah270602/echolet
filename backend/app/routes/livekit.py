from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.usage import UsageStatus
from app.services import usage_service
from app.auth import get_current_user_with_db
from app.db.database import get_async_session

router = APIRouter()

# Tokens are minted only by POST /api/session/start (tied to an owned agent and a
# call_sessions row); demo tokens come from the Vercel function frontend/api/demo/session.js.
# Talk time is recorded by the
# voice agent when a call ends, never reported by the browser.


@router.get("/usage", response_model=UsageStatus)
async def get_usage(
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> UsageStatus:
    """Today's talk-time usage for the authenticated user."""
    result = await usage_service.check_user_limit(session, current_user["id"])
    return UsageStatus(
        remaining_seconds=result["remaining_seconds"],
        used_seconds=result["used_seconds"],
        limit_seconds=result["limit_seconds"],
    )
