"""Voice agent: shared asyncpg pool and verified TLS."""

import asyncio
import importlib.util
import os
import ssl
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

_AGENT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_AGENT, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# agent/database.py does `from config import ...`; load agent/config.py as `config`
# only while importing, then restore whatever was there.
_saved = sys.modules.get("config")
sys.modules["config"] = _load("config", "config.py")
try:
    db = _load("agent_database", "database.py")
finally:
    if _saved is None:
        sys.modules.pop("config", None)
    else:
        sys.modules["config"] = _saved


@pytest.fixture(autouse=True)
def _reset_pool(monkeypatch):
    monkeypatch.setattr(db, "_pool", None)
    monkeypatch.setattr(db, "_pool_lock", asyncio.Lock())
    monkeypatch.setattr(db, "DATABASE_URL", "postgresql://u:p@host/db?sslmode=require")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("postgresql://u@h/d?sslmode=require", "postgres://u@h/d"),
        ("postgresql://u@h/d?sslmode=require&channel_binding=require", "postgres://u@h/d"),
        ("postgresql://u@h/d?channel_binding=require&sslmode=require", "postgres://u@h/d"),
        ("postgresql://u@h/d?application_name=x&sslmode=require", "postgres://u@h/d?application_name=x"),
        ("postgres://u@h/d", "postgres://u@h/d"),
    ],
)
def test_url_normalisation(raw, expected):
    assert db._normalize_url(raw)[0] == expected


def test_ssl_context_verifies():
    _, ctx = db._normalize_url("postgresql://u@h/d?sslmode=require")
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_no_sslmode_means_no_ssl():
    assert db._normalize_url("postgresql://u@localhost/d")[1] is None


def test_pool_created_once_under_concurrency(monkeypatch):
    pool = MagicMock()

    async def slow_create(*_a, **_k):
        await asyncio.sleep(0)  # yield so concurrent callers interleave
        return pool

    create = AsyncMock(side_effect=slow_create)
    monkeypatch.setattr(db.asyncpg, "create_pool", create)

    async def run():
        return await asyncio.gather(*[db._get_pool() for _ in range(10)])

    pools = asyncio.run(run())
    assert create.await_count == 1
    assert all(p is pool for p in pools)
    assert create.await_args.kwargs["statement_cache_size"] == 0  # Neon pooler (PgBouncer)
    assert create.await_args.kwargs["ssl"].check_hostname is True


def test_query_uses_pool(monkeypatch):
    conn = MagicMock()
    conn.fetchrow = AsyncMock(return_value={"talk_seconds_used": 100})
    pool = MagicMock()
    pool.acquire = AsyncMock(return_value=conn)
    pool.release = AsyncMock()
    monkeypatch.setattr(db, "_pool", pool)

    remaining = asyncio.run(db.get_user_remaining_seconds("u1"))

    assert remaining == max(0, db.DAILY_TALK_LIMIT_SECONDS - 100)
    pool.release.assert_awaited_once_with(conn)


def test_errors_still_swallowed(monkeypatch):
    monkeypatch.setattr(db.asyncpg, "create_pool", AsyncMock(side_effect=OSError("down")))
    assert asyncio.run(db.get_user_remaining_seconds("u1")) is None
    assert asyncio.run(db.get_session_config("r")) is None
    assert asyncio.run(db.save_call_log("r", [], 1)) is False
