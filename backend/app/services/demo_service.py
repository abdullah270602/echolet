"""
Public landing-page demo: anyone can talk to the starter agent without signing in.

Nothing is written to the database. The agent config and the hard time cap
travel inside the signed LiveKit token metadata, and the voice agent treats any
room prefixed with DEMO_ROOM_PREFIX as a demo (no call log, no analysis).
Cost is bounded by a per-IP hourly limit, a global daily budget and the per-call cap.
"""

import json
import time
import uuid
from collections import defaultdict, deque
from datetime import date, timedelta

from app.agent_templates.default import DEFAULT_AGENT_CONFIG

DEMO_ROOM_PREFIX = "demo-"


class DemoRateLimiter:
    # ponytail: in-process state, so limits are per backend replica and reset on
    # restart. Move to Redis/Postgres if the backend is scaled horizontally.

    def __init__(self, per_ip_per_hour: int, per_day: int):
        self.per_ip_per_hour = per_ip_per_hour
        self.per_day = per_day
        self._by_ip: dict[str, deque[float]] = defaultdict(deque)
        self._day = date.today()
        self._today = 0

    def check(self, ip: str, now: float | None = None, today: date | None = None) -> str | None:
        """Record an attempt. Returns None if allowed, else a reason for the visitor."""
        now = time.monotonic() if now is None else now
        today = today or date.today()
        if today != self._day:
            self._day, self._today = today, 0
            self._by_ip.clear()

        if self._today >= self.per_day:
            return "Today's live demo slots are used up. Try again tomorrow."

        hits = self._by_ip[ip]
        while hits and now - hits[0] > 3600:
            hits.popleft()
        if len(hits) >= self.per_ip_per_hour:
            return "You've used your demo calls for this hour. Try again in an hour."

        hits.append(now)
        self._today += 1
        return None


def build_demo_session(max_seconds: int) -> dict:
    """Room name, token metadata and token TTL for one demo call."""
    room_name = f"{DEMO_ROOM_PREFIX}{uuid.uuid4()}"
    metadata = json.dumps({
        "demo": True,
        "max_seconds": max_seconds,
        "config": DEFAULT_AGENT_CONFIG.model_dump(mode="json"),
    })
    # Token only needs to live long enough to join; the agent enforces the call cap.
    return {"room_name": room_name, "metadata": metadata, "ttl": timedelta(minutes=2)}
