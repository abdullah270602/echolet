"""
Phase 2: Security Tests - Authentication

Tests for JWT authentication, token validation, and auth bypass attempts.

Test Categories:
- SP (Sole Purpose): Auth always works correctly
- BREAK: JWT manipulation, forgery, bypass attempts
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_clerk_id() -> str:
    """Valid Clerk user ID."""
    return "user_2abc123def456"


@pytest.fixture
def valid_token_data(valid_clerk_id: str) -> dict:
    """Valid decoded JWT token data."""
    return {
        "sub": valid_clerk_id,
        "sid": "sess_abc123",
        "email": "test@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,
    }


@pytest.fixture
def mock_user() -> MagicMock:
    """Mock user from database."""
    user = MagicMock()
    user.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    user.clerk_id = "user_2abc123def456"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


# =============================================================================
# SOLE PURPOSE TESTS: Authentication
# =============================================================================


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_valid_jwt_returns_user_data(self, valid_token_data):
        """SP-AUTH-001: Valid JWT returns correct user data."""
        from app.auth import get_current_user

        mock_credentials = MagicMock()
        mock_credentials.decoded = valid_token_data

        result = await get_current_user(mock_credentials)

        assert result["user_id"] == valid_token_data["sub"]
        assert result["session_id"] == valid_token_data["sid"]
        assert result["email"] == valid_token_data["email"]




class TestGetCurrentUserWithDB:
    """Tests for get_current_user_with_db dependency."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_valid_user_returns_db_data(
        self, mock_session, valid_clerk_id, mock_user
    ):
        """SP-AUTH-001: Valid user returns database user data."""
        from app.auth import get_current_user_with_db
        from app.db.repos import user_repo

        token_data = {"user_id": valid_clerk_id, "email": "test@example.com"}

        with patch.object(user_repo, "get_by_clerk_id", return_value=mock_user):
            result = await get_current_user_with_db(mock_session, token_data)

            assert result["id"] == mock_user.id
            assert result["clerk_id"] == valid_clerk_id
            assert result["email"] == mock_user.email

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_user_not_in_db_returns_401(self, mock_session, valid_clerk_id):
        """SP-AUTH-006: User not in database returns 401."""
        from app.auth import get_current_user_with_db
        from app.db.repos import user_repo

        token_data = {"user_id": valid_clerk_id, "email": "test@example.com"}

        with patch.object(user_repo, "get_by_clerk_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_with_db(mock_session, token_data)

            assert exc_info.value.status_code == 401
            assert "User not found in database" in exc_info.value.detail


# =============================================================================
# BREAK-IT TESTS: Authentication Bypass Attempts
# =============================================================================


class TestAuthenticationBypass:
    """Adversarial tests attempting to bypass authentication."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_empty_token_data(self, mock_session):
        """BREAK-JWT-005: Empty claims in token."""
        from app.auth import get_current_user_with_db
        from app.db.repos import user_repo

        token_data = {"user_id": None, "email": None}

        with patch.object(user_repo, "get_by_clerk_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_with_db(mock_session, token_data)

            assert exc_info.value.status_code == 401

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_modified_user_id(self, mock_session, mock_user):
        """BREAK-JWT-003: Modified user_id claim (tampered token)."""
        from app.auth import get_current_user_with_db
        from app.db.repos import user_repo

        # Attacker changes user_id to another user
        tampered_token_data = {
            "user_id": "user_attacker123",  # Not the original
            "email": "attacker@evil.com",
        }

        # If the attacker's clerk_id doesn't exist in DB, should fail
        with patch.object(user_repo, "get_by_clerk_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_with_db(mock_session, tampered_token_data)

            assert exc_info.value.status_code == 401


# =============================================================================
# END-TO-END JWT HANDLING (real RS256 keys, real ClerkHTTPBearer verification)
# =============================================================================


@pytest.fixture
def jwt_client():
    """FastAPI app guarded by the real get_current_user; JWKS fetch returns our public key."""
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from app.auth import clerk_auth_guard, get_current_user

    good = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    app = FastAPI()

    @app.get("/me")
    async def me(user: dict = Depends(get_current_user)):
        return user

    def make(key=good, exp_delta=3600, **claims):
        now = int(datetime.now(timezone.utc).timestamp())
        payload = {"sub": "user_abc", "sid": "sess_1", "email": "a@b.c", "iat": now - 10,
                   "exp": now + exp_delta, **claims}
        return jwt.encode(payload, key, algorithm="RS256", headers={"kid": "k1"})

    signing_key = MagicMock()
    signing_key.key = good.public_key()
    with patch.object(clerk_auth_guard.jwks_client, "get_signing_key_from_jwt", return_value=signing_key):
        yield TestClient(app), make, other


class TestJWTEndToEnd:
    @pytest.mark.security
    def test_valid_token_accepted(self, jwt_client):
        client, make, _ = jwt_client
        r = client.get("/me", headers={"Authorization": f"Bearer {make()}"})
        assert r.status_code == 200
        assert r.json() == {"user_id": "user_abc", "session_id": "sess_1", "email": "a@b.c"}

    @pytest.mark.security
    def test_expired_token_rejected(self, jwt_client):
        client, make, _ = jwt_client
        r = client.get("/me", headers={"Authorization": f"Bearer {make(exp_delta=-60)}"})
        assert r.status_code in (401, 403)

    @pytest.mark.security
    def test_wrong_signature_rejected(self, jwt_client):
        client, make, other = jwt_client
        r = client.get("/me", headers={"Authorization": f"Bearer {make(key=other)}"})
        assert r.status_code in (401, 403)

    @pytest.mark.security
    def test_tampered_payload_rejected(self, jwt_client):
        import base64, json
        client, make, _ = jwt_client
        h, p, sig = make().split(".")
        claims = json.loads(base64.urlsafe_b64decode(p + "=="))
        claims["sub"] = "user_attacker"
        p2 = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        r = client.get("/me", headers={"Authorization": f"Bearer {h}.{p2}.{sig}"})
        assert r.status_code in (401, 403)

    @pytest.mark.security
    def test_missing_or_malformed_token_rejected(self, jwt_client):
        client, _, _ = jwt_client
        assert client.get("/me").status_code in (401, 403)
        assert client.get("/me", headers={"Authorization": "Bearer not.a.jwt"}).status_code in (401, 403)
        assert client.get("/me", headers={"Authorization": "Basic abc"}).status_code in (401, 403)
