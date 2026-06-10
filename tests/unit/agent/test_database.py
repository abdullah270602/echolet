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


class _FakeConn:
    """Tiny stand-in for the call_sessions/user_daily_usage tables."""

    def __init__(self, sessions):
        self.ended = {room: False for room in sessions}
        self.usage = 0
        self.in_tx = False
        self.usage_writes_outside_tx = 0
        self.sql = []

    def transaction(self):
        conn = self

        class _Tx:
            async def __aenter__(self):
                conn.in_tx = True

            async def __aexit__(self, *exc):
                conn.in_tx = False

        return _Tx()

    async def fetchrow(self, sql, *args):
        self.sql.append(sql)
        room = args[-1]
        if room not in self.ended or ("ended_at IS NULL" in sql and self.ended[room]):
            return None
        self.ended[room] = True
        return {"user_id": "user-1"}

    async def fetchval(self, sql, room):
        return 1 if room in self.ended else None

    async def execute(self, sql, user_id, day, seconds, now):
        if not self.in_tx:
            self.usage_writes_outside_tx += 1
        self.usage += seconds


def _pool_for(conn):
    pool = MagicMock()
    pool.acquire = AsyncMock(return_value=conn)
    pool.release = AsyncMock()
    return pool


def test_save_call_log_counts_usage_once_and_inside_a_transaction(monkeypatch):
    conn = _FakeConn(["room-1"])
    monkeypatch.setattr(db, "_pool", _pool_for(conn))

    assert asyncio.run(db.save_call_log("room-1", [{"role": "user"}], 90)) is True
    # end_call tool then the cleanup path both save the same room
    assert asyncio.run(db.save_call_log("room-1", [], 400, status="failed")) is True

    assert conn.usage == 90  # second call must not add 400
    assert conn.usage_writes_outside_tx == 0
    assert "ended_at IS NULL" in conn.sql[0]


def test_save_call_log_unknown_room_is_false_and_adds_no_usage(monkeypatch):
    conn = _FakeConn(["room-1"])
    monkeypatch.setattr(db, "_pool", _pool_for(conn))
    assert asyncio.run(db.save_call_log("nope", [], 90)) is False
    assert conn.usage == 0


def test_session_config_query_excludes_soft_deleted_agents(monkeypatch):
    conn = MagicMock()
    conn.fetchrow = AsyncMock(return_value=None)
    monkeypatch.setattr(db, "_pool", _pool_for(conn))
    assert asyncio.run(db.get_session_config("room-1")) is None
    assert "ac.deleted_at IS NULL" in conn.fetchrow.call_args.args[0]


def test_billing_clock_starts_after_participant_joins():
    import ast
    src = open(os.path.join(_AGENT, "agent.py")).read()
    fn = next(n for n in ast.walk(ast.parse(src)) if getattr(n, "name", "") == "agent_session")
    lines = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "session_start_time":
            lines.setdefault("start", []).append(n.lineno)
        if isinstance(n, ast.Attribute) and n.attr == "wait_for_participant":
            lines["join"] = n.lineno
    assert lines["start"] == [lines["join"] + 1]  # the only assignment follows the join
    assert "session_start_time: float | None = None" in src
