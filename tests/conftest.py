"""
Echolet Test Suite - Shared Fixtures and Configuration

This module provides shared pytest fixtures for testing the Echolet platform:
- Agent (Voice AI)
- Backend API (FastAPI)
- Worker (Call Analysis)
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Add project paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))


# =============================================================================
# Test Data Factories
# =============================================================================


@pytest.fixture
def user_id() -> uuid.UUID:
    """Generate a random user UUID."""
    return uuid.uuid4()


@pytest.fixture
def user_id_str(user_id: uuid.UUID) -> str:
    """User ID as string."""
    return str(user_id)


@pytest.fixture
def clerk_id() -> str:
    """Generate a Clerk-style user ID."""
    return f"user_{uuid.uuid4().hex[:24]}"


@pytest.fixture
def agent_id() -> int:
    """Generate a random agent ID."""
    return 1


@pytest.fixture
def room_name() -> str:
    """Generate a random LiveKit room name (UUID)."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_user(user_id: uuid.UUID, clerk_id: str) -> dict[str, Any]:
    """Sample user data."""
    return {
        "id": user_id,
        "clerk_id": clerk_id,
        "email": "test@example.com",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def build_agent_config(**overrides: Any) -> dict[str, Any]:
    """Valid AgentConfigData payload (JSONB shape); top-level keys can be overridden."""
    config: dict[str, Any] = {
        "agent": {
            "name": "Test Agent",
            "business_name": "Test Business",
            "greeting_message": "Hello! How can I help you today?",
        },
        "voice": {"provider": "inworld", "voice_id": "Ashley"},
        "knowledge_base": {
            "sources": [{"type": "text", "name": "hours", "content": "Business hours are 9am-5pm."}]
        },
        "output": {
            "ticket_fields": [
                {"id": "call_summary", "label": "Call Summary", "type": "text", "required": True}
            ],
            "custom_tags": ["new_patient"],
        },
        "custom_instructions": "Be helpful and concise.",
    }
    config.update(overrides)
    return config


@pytest.fixture
def make_agent_config():
    """Factory for a valid agent config dict: make_agent_config(custom_instructions="x")."""
    return build_agent_config


@pytest.fixture
def sample_agent_config(user_id: uuid.UUID, agent_id: int) -> dict[str, Any]:
    """Sample agent row (columns + JSONB config)."""
    return {
        "id": agent_id,
        "user_id": user_id,
        "config": build_agent_config(),
        "status": "active",
        "phone": None,
        "deleted_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_transcript() -> list[dict[str, Any]]:
    """Sample conversation transcript."""
    base_time = 1700000000.0
    return [
        {
            "role": "agent",
            "content": "Hello! How can I help you today?",
            "timestamp": base_time,
        },
        {
            "role": "user",
            "content": "I'd like to book an appointment.",
            "timestamp": base_time + 5,
            "language": "en",
        },
        {
            "role": "agent",
            "content": "Sure! What day works best for you?",
            "timestamp": base_time + 10,
        },
        {
            "role": "user",
            "content": "Tomorrow at 2pm would be great.",
            "timestamp": base_time + 15,
            "language": "en",
        },
        {
            "role": "agent",
            "content": "I've noted that down. Is there anything else I can help with?",
            "timestamp": base_time + 20,
        },
        {
            "role": "user",
            "content": "No, that's all. Thank you!",
            "timestamp": base_time + 25,
            "language": "en",
        },
        {
            "role": "agent",
            "content": "You're welcome! Have a great day. Goodbye!",
            "timestamp": base_time + 30,
        },
        {
            "role": "user",
            "content": "Bye!",
            "timestamp": base_time + 35,
            "language": "en",
        },
    ]


@pytest.fixture
def sample_call_session(
    user_id: uuid.UUID, agent_id: int, room_name: str, sample_transcript: list
) -> dict[str, Any]:
    """Sample call session data."""
    return {
        "id": 1,
        "room_name": room_name,
        "user_id": user_id,
        "agent_id": agent_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc),
        "started_at": datetime.now(timezone.utc),
        "ended_at": datetime.now(timezone.utc),
        "duration_seconds": 35,
        "transcript": sample_transcript,
        "summary": "Caller requested an appointment for tomorrow at 2pm.",
        "category": "Appointment",
        "urgency": "Medium",
        "sentiment": "Positive",
        "action_required": True,
        "action_items": ["Confirm appointment for tomorrow 2pm"],
        "priority": "normal",
    }


@pytest.fixture
def sample_analysis() -> dict[str, Any]:
    """Sample LLM analysis response."""
    return {
        "summary": "Caller requested an appointment booking for tomorrow at 2pm.",
        "category": "Appointment",
        "urgency": "Medium",
        "sentiment": "Positive",
        "action_required": True,
        "action_items": ["Confirm appointment for tomorrow 2pm"],
    }


# =============================================================================
# JWT / Authentication Fixtures
# =============================================================================


@pytest.fixture
def mock_jwt_payload(clerk_id: str) -> dict[str, Any]:
    """Mock JWT payload from Clerk."""
    return {
        "sub": clerk_id,
        "sid": f"sess_{uuid.uuid4().hex[:24]}",
        "email": "test@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,
    }


@pytest.fixture
def mock_auth_user(user_id: uuid.UUID, clerk_id: str) -> dict[str, Any]:
    """Mock authenticated user (after DB lookup)."""
    return {
        "id": user_id,
        "clerk_id": clerk_id,
        "email": "test@example.com",
    }


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Mock Authorization headers."""
    return {"Authorization": "Bearer mock_jwt_token"}


# =============================================================================
# Database Fixtures (SQLite in-memory for speed)
# =============================================================================


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def mock_db_connection() -> AsyncMock:
    """Mock asyncpg connection (for agent/worker direct queries)."""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    return conn


# =============================================================================
# AWS SQS Fixtures
# =============================================================================


@pytest.fixture
def mock_sqs_client() -> MagicMock:
    """Mock boto3 SQS client."""
    client = MagicMock()
    client.receive_message = MagicMock(return_value={"Messages": []})
    client.send_message = MagicMock(return_value={"MessageId": str(uuid.uuid4())})
    client.delete_message = MagicMock(return_value={})
    return client


@pytest.fixture
def sample_sqs_message(room_name: str) -> dict[str, Any]:
    """Sample SQS message."""
    return {
        "MessageId": str(uuid.uuid4()),
        "ReceiptHandle": f"receipt_{uuid.uuid4().hex}",
        "Body": json.dumps(
            {"room_name": room_name, "timestamp": datetime.now(timezone.utc).timestamp()}
        ),
    }


# =============================================================================
# HTTP / API Client Fixtures
# =============================================================================


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Mock httpx.AsyncClient for LLM API calls."""
    client = AsyncMock()
    client.post = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock()
    return client


# =============================================================================
# LiveKit Fixtures
# =============================================================================


@pytest.fixture
def mock_livekit_api() -> MagicMock:
    """Mock LiveKit API client."""
    api = MagicMock()
    api.room = MagicMock()
    api.room.delete_room = AsyncMock()
    return api


@pytest.fixture
def mock_agent_session() -> MagicMock:
    """Mock LiveKit AgentSession."""
    session = MagicMock()
    session.generate_reply = AsyncMock()
    session.interrupt = AsyncMock()
    session.say = AsyncMock()
    return session


@pytest.fixture
def mock_job_context() -> MagicMock:
    """Mock LiveKit JobContext."""
    ctx = MagicMock()
    ctx.room = MagicMock()
    ctx.room.name = str(uuid.uuid4())
    ctx.room.disconnect = AsyncMock()
    return ctx


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "test_api_key",
        "LIVEKIT_API_SECRET": "test_api_secret",
        "CLERK_JWKS_URL": "https://test.clerk.accounts.dev/.well-known/jwks.json",
        "CLERK_WEBHOOK_SIGNING_SECRET": "whsec_test_secret",
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "SQS_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        "AWS_REGION": "us-east-1",
        "DAILY_TALK_LIMIT_SECONDS": "3600",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


# =============================================================================
# Utility Functions
# =============================================================================


def create_mock_user_response(
    user_id: uuid.UUID, clerk_id: str, email: str = "test@example.com"
) -> dict[str, Any]:
    """Create a mock user response dict."""
    return {
        "id": user_id,
        "clerk_id": clerk_id,
        "email": email,
    }


def create_mock_agent_response(
    agent_id: int,
    user_id: uuid.UUID,
    name: str = "Test Agent",
    business_name: str = "Test Business",
) -> dict[str, Any]:
    """Create a mock agent response dict."""
    config = build_agent_config()
    config["agent"].update(name=name, business_name=business_name)
    return {
        "id": agent_id,
        "user_id": user_id,
        "config": config,
        "status": "active",
        "phone": None,
        "deleted_at": None,
    }
