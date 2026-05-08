# Echolet

An AI voice receptionist for small service businesses. A business owner describes their
business once (identity, voice, services and prices, knowledge base, guardrails, which
details to capture), and Echolet answers callers in real time, saves every call with a
transcript, and turns it into a ticket with a summary, sentiment and action items.

Visitors can talk to a demo receptionist from the landing page without an account.

## Architecture

```mermaid
flowchart LR
    B[Browser<br/>React + LiveKit client] -- Clerk JWT --> API[Backend<br/>FastAPI]
    B -- WebRTC audio --> LK[(LiveKit Cloud)]
    API -- mints room token --> B
    LK -- dispatches job --> AG[Voice agent<br/>LiveKit Agents]
    AG -- STT / LLM / TTS --> P[Deepgram · Gemini via OpenRouter · Inworld]
    AG -- config, transcript, usage --> DB[(Postgres)]
    API --- DB
    AG -- room name --> Q[[SQS]]
    Q --> W[Analysis worker]
    W -- ticket --> DB
    CL[Clerk] -- signed webhook --> API
```

| Service | Path | Responsibility |
|---|---|---|
| Backend | `backend/` | Clerk auth, agent CRUD, starts call sessions and mints LiveKit tokens, public demo endpoint, Clerk webhooks, usage read-out. Async SQLAlchemy + Alembic. |
| Voice agent | `agent/` | Joins each room, loads that session's agent config, runs the STT → LLM → TTS pipeline, enforces the talk-time cap, saves the transcript, queues analysis. |
| Worker | `worker/` | Long-polls SQS, runs the LLM analysis against the agent's ticket fields, writes the result. Idempotent per call. |
| Frontend | `frontend/` | Landing page with live demo, dashboard (agents, sandbox calls, call history and tickets). |

### How a call works

1. The dashboard calls `POST /api/session/start` with an agent id. The backend checks the
   agent belongs to the caller and that they have talk time left today, creates a
   `call_sessions` row whose `room_name` is a fresh UUID, and returns a 10-minute LiveKit
   token scoped to that room (microphone only).
2. The agent is dispatched into the room, looks the session up by room name, and builds its
   prompt from the agent's JSONB config. Rooms with no matching session get no agent, so
   there is no way to start an unmetered conversation.
3. A background task ends the call (with a spoken goodbye) when the user's daily allowance
   runs out. On hang-up the agent writes the transcript, duration and usage, then sends the
   room name to SQS.
4. The worker picks it up, analyses the transcript, and stores the ticket.

**Talk time is accounted for only by the agent, on the server.** The browser never reports
usage.

### Public demo

`POST /api/demo/session` needs no account. It returns a 2-minute join token for a
`demo-<uuid>` room. The demo agent config (a fictional dental clinic, `backend/app/agent_templates/default.py`)
and the call length cap travel in the token's metadata, which is signed with the LiveKit
secret, so the agent can trust them without a database lookup. Demo calls are never stored or
analysed. Cost is bounded three ways: a per-IP hourly limit, a global daily budget, and the
per-call cap (clamped again by the agent). All are environment variables (`DEMO_*`, see
`.env.example`). The rate limiter is in-process: limits are per backend replica.

## Running locally

Prerequisites: Python 3.13 with [uv](https://docs.astral.sh/uv/), Node 20, a Postgres
database, and accounts for LiveKit Cloud, Clerk, Deepgram, OpenRouter, Inworld and AWS SQS.

```bash
cp .env.example .env                 # fill in credentials
cp frontend/.env.example frontend/.env

cd backend && uv sync && uv run alembic upgrade head && cd ..
./dev.sh                             # backend :8000, agent, worker  (dev.ps1 on Windows)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

For the Clerk `user.created` webhook (which seeds a starter agent for each new user),
expose `/api/clerk/webhooks` with a tunnel and set `CLERK_WEBHOOK_SIGNING_SECRET`.

Production runs all services with `docker compose up -d --build` behind Caddy
(`Caddyfile`). The backend has a `/health` endpoint that checks database connectivity and is
used as the compose health check.

## Tests

```bash
cd tests && uv sync
uv run pytest                        # all suites
uv run pytest --cov                  # with coverage (backend + worker)
cd ../frontend && npm run lint && npm run build
```

The suite (`tests/`) is organised as `unit`, `integration`, `e2e`, `security` and
`resilience`. External services (LiveKit, OpenRouter, SQS, Postgres) are mocked; the e2e
test drives the real queue → worker → analyzer path with only I/O mocked. CI
(`.github/workflows/test.yml`) runs the Python suite with a coverage gate and lints and
builds the frontend.

## Known limitations

- **No telephony yet.** Calls run over WebRTC from the browser. The agent already handles SIP
  participants (telephony noise cancellation), but phone-number provisioning and inbound
  SIP trunking are not built.
- **Website knowledge sources are not crawled.** A website source is passed to the model as a
  URL reference only; text sources are what the agent actually answers from.
- **Integrations and actions** in the agent config are stored but not executed.
- **The voice agent has little automated coverage.** Its demo handling is unit-tested; the
  LiveKit session lifecycle is verified by hand.
