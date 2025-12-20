from fastapi import Depends, HTTPException
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials

from app.config import CLERK_JWKS_URL

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
