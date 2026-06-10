# Echolet

Echolet is an AI voice receptionist for small service businesses. An owner configures an
agent with their services, prices, hours and rules. The agent talks to callers in real time,
saves each call with a transcript, and writes a ticket with a summary, sentiment and action
items.

## Architecture

![Echolet architecture: browser, LiveKit rooms and the voice agent, speech and language models, Postgres, the analysis queue and worker, the backend API and Vercel functions](docs/architecture.svg)

| Path | What it is |
|---|---|
| `backend/` | FastAPI. Clerk auth, agent CRUD, call sessions and LiveKit tokens (one live call per user), Clerk webhooks. Async SQLAlchemy and Alembic. |
| `agent/` | LiveKit voice agent. Loads the session's agent config, runs speech-to-text, the LLM and text-to-speech, enforces the daily talk-time cap, saves the transcript, queues analysis. |
| `worker/` | Polls SQS, builds the analysis prompt and validation from the agent's configured ticket fields and tags, stores the ticket. Failed analyses stay on the queue for retry (SQS redrive to a dead-letter queue). |
| `frontend/` | React app: landing page with a live demo and waitlist, and the dashboard. `frontend/api/` holds two Vercel Functions (demo token, waitlist). |
| `tests/` | Python test suite for backend, worker and agent modules. |

### A call, end to end

1. The dashboard calls `POST /api/session/start`. The backend checks that the agent belongs
   to the user and that they have talk time left today, creates a `call_sessions` row, and
   returns a short-lived, microphone-only LiveKit token for that room.
2. The agent joins the room, finds the session by room name and builds its prompt from the
   agent's config. A room with no session gets no agent.
3. When the daily allowance runs out, the agent says goodbye and ends the call. On hang-up it
   saves the transcript, duration and usage, then sends the room name to SQS.
4. The worker writes the ticket.

Talk time is recorded only by the agent on the server, once per call and in the same
transaction as the call log. A user can have one live call at a time, so parallel tabs
can't stretch the daily allowance.

### Demo calls

The landing page's `POST /api/demo/session` (a Vercel Function) needs no account. It returns a two-minute join token for a
`demo-<uuid>` room, with the demo clinic's config and a call-length cap in the token
metadata. The metadata is signed with the LiveKit secret, so the agent uses it without a
database lookup. Demo calls are not stored. The demo agent also gets a demo calendar for the clinic
(`agent/demo_calendar.py`): it checks real open slots, books them during the call and
says a confirmation text is on its way; the page shows that text as a preview, since a
demo can't send one (customer agents have no calendar or SMS integration yet). When the call ends
the visitor sees a ticket written from their own call, delivered over LiveKit RPC.

The function (`frontend/api/demo/session.js`) has layered abuse protection: a Vercel Firewall rate limit; per-visitor hourly and daily
limits and a global daily budget kept in Postgres (IPs stored as salted hashes); a cap on
simultaneous demo calls read live from LiveKit; and the per-call time cap enforced by the
agent. If the database or LiveKit can't be reached it refuses the call. Limits are the
`DEMO_*` variables in `.env.example`, set on the Vercel project.

### Latency

The agent logs LiveKit's per-stage metrics during a call and, when it ends, one summary
line with p50/p95 of end-of-utterance delay, LLM time-to-first-token, TTS time-to-first-byte
and their sum, the reply delay a caller hears (`agent/telemetry.py`; see `lk agent logs`).

## Getting started

Requirements: Python 3.13 with [uv](https://docs.astral.sh/uv/), Node 20, Postgres, and
accounts for LiveKit Cloud, Clerk, Deepgram, OpenRouter, Inworld and AWS SQS.

```bash
cp .env.example .env                       # fill in credentials
cp frontend/.env.example frontend/.env

cd backend && uv sync && uv run alembic upgrade head && cd ..
./dev.sh                                   # backend on :8000, agent, worker (dev.ps1 on Windows)
cd frontend && npm install && npm run dev  # http://localhost:5173
```

New users get a starter agent from the Clerk `user.created` webhook. To receive it locally,
expose `/api/clerk/webhooks` through a tunnel and set `CLERK_WEBHOOK_SIGNING_SECRET`.

## Tests

```bash
cd tests && uv sync && uv run pytest --cov   # unit, integration, e2e, security, resilience
cd frontend && npm run lint && npm test && npm run build
```

External services are mocked: SQS, the LLM HTTP call and the database in the pipeline test,
which exercises the agent → queue → worker → analyzer code path rather than real services.
Auth tests verify real RS256 JWTs through the FastAPI guard. CI (`.github/workflows/test.yml`)
runs both with a coverage gate.

### Agent evals

`agent/evals/` runs the production agent in LiveKit's text test mode against the demo clinic,
using the real prompt builder, tools and model. Each case combines fixed checks (quoted price,
no markdown in speech, whether `end_call` fired) with an LLM judge from a different model
family than the agent's. Runs are text-only, so speech recognition errors, latency and
interruptions are not covered here.

```bash
cd agent && uv sync
uv run pytest evals -n 6                       # 306 cases + core and demo suites, ~3 min
EVAL_REPEAT=3 uv run pytest evals/test_dataset.py -n 8   # each case 3x, to separate noise
```

Current baseline, each case run 3 times with the independent judge: **535 / 918 (58%)**.
86 cases fail every run; those are the real gaps. They cluster in booking (customer agents
can't confirm a slot, so callers are told the front desk will), very long answers to
"tell me everything" prompts, and prompt injection. Per-category numbers and history are in
`agent/evals/DATASET.md`. The suite is a measuring tool, not a green badge.

Cases cover answers from the knowledge base, invented prices, calendar claims, medical
advice, prompt injection, booking and hanging up. They run nightly and on demand
(`.github/workflows/evals.yml`), gated on the overall pass rate (`evals/check_threshold.py`)
since the dataset deliberately includes cases the agent still fails. Early runs found two
issues, both fixed: the model
ended calls mid-booking (`end_call` now requires a goodbye from the caller, see
`agent/call_ending.py`), and the starter agent sent dental emergencies to the ER.

## Deployment

**Full stack:** `docker compose up -d --build` runs everything behind Caddy. The backend's
`/health` endpoint checks the database and is the compose health check.

**Landing page only:** the landing page, live demo and waitlist can run without the backend.

1. Deploy the agent to LiveKit Cloud. Demo calls need no database or SQS.
   ```bash
   cd agent
   lk cloud auth
   lk agent create --secrets-file demo.secrets   # DEEPGRAM_API_KEY, OPENROUTER_API_KEY, INWORLD_API_KEY
   ```
2. Deploy `frontend/` to Vercel. Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
   (same LiveKit project as the agent), `DATABASE_URL` (for the waitlist) and
   `VITE_CLERK_PUBLISHABLE_KEY`. Leave `VITE_API_BASE_URL` unset.
3. Add a Vercel Firewall rate limit on `/api/demo/session` and spend limits with the AI
   providers.

Without a deployed agent, set `DEMO_ENABLED=false` (or build with `VITE_LIVE_DEMO=false`)
and the demo panel shows a scripted example call. The dashboard always needs the backend.
