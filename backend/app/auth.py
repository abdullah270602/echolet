from fastapi import Depends, HTTPException
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import CLERK_JWKS_URL
from app.db.database import get_async_session
from app.db.repos import user_repo

if not CLERK_JWKS_URL:
    raise RuntimeError("CLERK_JWKS_URL environment variable not configured")

clerk_config = ClerkConfig(jwks_url=CLERK_JWKS_URL)
clerk_auth_guard = ClerkHTTPBearer(config=clerk_config)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(clerk_auth_guard),
) -> dict:
    """
    Dependency that validates the Clerk JWT and returns user info.

    Returns a dict with:
    - user_id: The Clerk user ID (sub claim)
    - session_id: The Clerk session ID
    - Additional claims from the JWT
    """
    decoded = credentials.decoded

    return {
        "user_id": decoded.get("sub"),
        "session_id": decoded.get("sid"),
        "email": decoded.get("email"),
    }


async def get_current_user_with_db(
    session: AsyncSession = Depends(get_async_session),
    token_data: dict = Depends(get_current_user),
) -> dict:
    """
    Dependency that validates JWT and looks up the internal user ID.

    Returns a dict with:
    - id: The internal database UUID
    - clerk_id: The Clerk user ID (for reference)
    - email: User's email
    """
    clerk_id = token_data["user_id"]

    user = await user_repo.get_by_clerk_id(session, clerk_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found in database")

    return {
        "id": user.id,
        "clerk_id": clerk_id,
        "email": user.email,
    }
