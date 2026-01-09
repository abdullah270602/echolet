# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Echolet is an AI receptionist platform with four main components: a Python backend API, a Python LiveKit voice agent, an async analysis worker, and a React frontend. The platform enables users to create and manage configurable AI voice agents that use LiveKit for real-time communication, with automatic post-call analysis.

## Development Commands

### Backend (FastAPI)
```bash
cd echolet/backend
uv sync                           # Install dependencies
uv run uvicorn main:app --reload  # Run development server
uv run alembic upgrade head       # Run database migrations
uv run alembic revision --autogenerate -m "description"  # Create new migration
```

### Agent (LiveKit Voice Agent)
```bash
cd echolet/agent
uv sync                # Install dependencies
uv run agent.py dev    # Development mode
uv run agent.py start  # Production mode
```

### Frontend (React + Vite)
```bash
cd echolet/frontend
npm install           # Install dependencies
npm run dev           # Run development server
npm run build         # Build for production
npm run lint          # Run ESLint
```

### Worker (Call Analysis)
```bash
cd echolet/worker
uv sync              # Install dependencies
uv run worker.py     # Run worker (polls SQS continuously)
```

## Architecture

### Four-Component System
- **Backend** (`backend/`): FastAPI server handling authentication (Clerk), agent configuration CRUD, LiveKit token generation, and session management. Uses async SQLAlchemy with PostgreSQL (Neon).
- **Agent** (`agent/`): LiveKit Agents SDK voice pipeline that connects to rooms, fetches configuration from the database, and runs voice conversations using Deepgram STT, OpenRouter LLM (Gemini), and Inworld TTS.
- **Worker** (`worker/`): Async call analysis service that polls SQS, fetches transcripts, runs LLM analysis (summary, sentiment, action items), and updates the database.
- **Frontend** (`frontend/`): React SPA with Clerk auth, agent configuration forms, call history, and LiveKit components for voice sessions.

### Data Flow
1. Frontend authenticates via Clerk and creates/configures agents via backend API
2. When user initiates a call, frontend requests a LiveKit token from backend
3. Backend creates a LiveKit room with the agent config ID embedded in the room name
4. Agent receives the room connection, extracts config from room name, fetches full config from database
5. Agent runs the voice session with dynamic prompts, voice settings, and usage limits
6. Call transcript and duration are saved to database when session ends
7. Agent sends room_name to SQS queue for async analysis
8. Worker picks up message, fetches transcript, calls Gemini for analysis
9. Worker updates call_session with summary, sentiment, and action_items

### Key Integration Points
- **LiveKit**: Rooms connect frontend and agent. Room names encode the agent config ID for lookup.
- **Database**: Shared PostgreSQL database accessed by backend, agent, and worker for config and session data.
- **SQS**: Decouples call completion from analysis. Agent sends to queue, worker processes async.
- **Authentication**: Backend uses Clerk JWT verification; agent trusts participant metadata from backend.

### Backend Structure
- `app/routes/`: API endpoints (agents, livekit tokens, session)
- `app/services/`: Business logic layer
- `app/db/repos/`: Database repository pattern for queries
- `app/db/models/`: SQLAlchemy ORM models
- `app/schemas/`: Pydantic request/response models

### Agent Structure
- `agent.py`: Main entry point with LiveKit session handler
- `prompts.py`: Dynamic prompt building from agent configuration
- `database.py`: Direct async PostgreSQL queries for config lookup
- `transcript.py`: Handlers for capturing conversation transcript
- `usage.py`: Per-user daily usage limit enforcement
- `sqs.py`: Sends call IDs to SQS queue after call ends

### Worker Structure
- `worker.py`: Main entry point, SQS polling loop with graceful shutdown
- `config.py`: Environment variable loading
- `database.py`: Fetch transcript and update analysis results
- `analyzer.py`: LLM prompt and OpenRouter API call for analysis

## Environment Variables

Required in `.env` at repository root:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`: LiveKit Cloud credentials
- `DATABASE_URL`: PostgreSQL connection string (Neon)
- `CLERK_JWKS_URL`: Clerk JWKS endpoint for JWT validation
- `DEEPGRAM_API_KEY`: For speech-to-text
- `OPENROUTER_API_KEY`: For LLM (routes to Gemini)
- `INWORLD_API_KEY`: For text-to-speech
- `SQS_QUEUE_URL`: AWS SQS queue URL for call analysis
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AWS_REGION`: AWS region (default: eu-north-1)
