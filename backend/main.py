from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.routes.livekit import router as livekit_router
from app.routes.agents import router as agents_router
from app.routes.session import router as session_router
from app.routes.clerk import router as clerk_router
from app.config import ALLOWED_ORIGINS
from app.db.database import engine, init_db, close_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Initializing database connection pool...")
    await init_db()
    logger.info("Database connection pool initialized.")

    yield

    # Shutdown
    logger.info("Closing database connection pool...")
    await close_db()
    logger.info("Database connection pool closed.")


app = FastAPI(title="Echolet", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(livekit_router, prefix="/api/livekit", tags=["livekit"])
app.include_router(agents_router, prefix="/api", tags=["agents"])
app.include_router(session_router, prefix="/api/session", tags=["session"])
app.include_router(clerk_router, prefix="/api/clerk", tags=["clerk"])


@app.get("/health")
async def health():
    """Liveness + database reachability, for Docker/Caddy health checks."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: database unreachable")
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}
