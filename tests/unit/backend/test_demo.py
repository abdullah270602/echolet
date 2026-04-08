"""Public demo endpoint, its rate limiter, and the starter agent template."""

import json
from datetime import date

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import config
from app.agent_templates.default import DEFAULT_AGENT_CONFIG
from app.routes import demo as demo_route
from app.schemas.agent import AgentConfigData
from app.services.demo_service import DEMO_ROOM_PREFIX, DemoRateLimiter


class TestDemoRateLimiter:
    def test_per_ip_limit_then_window_expires(self):
        limiter = DemoRateLimiter(per_ip_per_hour=2, per_day=100)
        day = date(2026, 3, 1)
        assert limiter.check("1.1.1.1", now=0, today=day) is None
        assert limiter.check("1.1.1.1", now=10, today=day) is None
        assert limiter.check("1.1.1.1", now=20, today=day) is not None
        # A different visitor is unaffected.
        assert limiter.check("2.2.2.2", now=20, today=day) is None
        # An hour after the first call, one slot frees up.
        assert limiter.check("1.1.1.1", now=3601, today=day) is None

    def test_daily_budget_is_global_and_resets(self):
        limiter = DemoRateLimiter(per_ip_per_hour=10, per_day=2)
        day = date(2026, 3, 1)
        assert limiter.check("a", now=0, today=day) is None
        assert limiter.check("b", now=0, today=day) is None
        assert "Today's" in limiter.check("c", now=0, today=day)
        assert limiter.check("c", now=0, today=date(2026, 3, 2)) is None

    def test_rejected_attempts_do_not_consume_budget(self):
        limiter = DemoRateLimiter(per_ip_per_hour=1, per_day=2)
        day = date(2026, 3, 1)
        assert limiter.check("a", now=0, today=day) is None
        for _ in range(5):
            assert limiter.check("a", now=1, today=day) is not None
        assert limiter.check("b", now=1, today=day) is None


@pytest.fixture
def demo_client(monkeypatch):
    monkeypatch.setattr(config, "DEMO_ENABLED", True)
    monkeypatch.setattr(config, "DEMO_MAX_SECONDS", 90)
    monkeypatch.setattr("app.services.livekit_service.LIVEKIT_API_KEY", "devkey")
    monkeypatch.setattr("app.services.livekit_service.LIVEKIT_API_SECRET", "x" * 32)
    monkeypatch.setattr("app.services.livekit_service.LIVEKIT_URL", "wss://example.livekit.cloud")
    monkeypatch.setattr(config, "LIVEKIT_API_KEY", "devkey")
    monkeypatch.setattr(config, "LIVEKIT_API_SECRET", "x" * 32)
    monkeypatch.setattr(demo_route, "limiter", DemoRateLimiter(per_ip_per_hour=1, per_day=100))
    app = FastAPI()
    app.include_router(demo_route.router, prefix="/api/demo")
    return TestClient(app)


class TestDemoEndpoint:
    def test_issues_signed_token_carrying_config_and_cap(self, demo_client):
        res = demo_client.post("/api/demo/session")
        assert res.status_code == 200
        body = res.json()
        assert body["room_name"].startswith(DEMO_ROOM_PREFIX)
        assert body["max_seconds"] == 90
        assert body["livekit_url"] == "wss://example.livekit.cloud"

        claims = jwt.decode(body["token"], "x" * 32, algorithms=["HS256"])
        assert claims["video"]["room"] == body["room_name"]
        assert claims["video"]["canPublishSources"] == ["microphone"]
        assert claims["exp"] - claims["nbf"] <= 120  # short-lived join token
        meta = json.loads(claims["metadata"])
        assert meta["demo"] is True and meta["max_seconds"] == 90
        assert AgentConfigData.model_validate(meta["config"]) == DEFAULT_AGENT_CONFIG

    def test_second_call_from_same_ip_is_rate_limited(self, demo_client):
        assert demo_client.post("/api/demo/session").status_code == 200
        res = demo_client.post("/api/demo/session")
        assert res.status_code == 429
        assert res.json()["detail"]

    def test_disabled_demo_returns_503(self, demo_client, monkeypatch):
        monkeypatch.setattr(config, "DEMO_ENABLED", False)
        assert demo_client.post("/api/demo/session").status_code == 503

    def test_missing_livekit_credentials_returns_503(self, demo_client, monkeypatch):
        monkeypatch.setattr(config, "LIVEKIT_API_SECRET", None)
        assert demo_client.post("/api/demo/session").status_code == 503
