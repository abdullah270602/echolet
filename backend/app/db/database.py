import ssl
from typing import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import DATABASE_URL


def get_async_database_url(url: str | None) -> tuple[str, dict]:
    """
    Convert a standard PostgreSQL URL to an asyncpg-compatible URL.
    Handles sslmode conversion for asyncpg.

    Returns:
        Tuple of (url, connect_args)
    """
    if url is None:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Replace protocol
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Parse URL to handle sslmode
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    connect_args: dict = {}

    # Handle sslmode for asyncpg
    if "sslmode" in query_params:
        sslmode = query_params.pop("sslmode")[0]
        if sslmode in ("require", "verify-ca", "verify-full"):
            connect_args["ssl"] = ssl.create_default_context()
        elif sslmode == "prefer":
            connect_args["ssl"] = "prefer"

        # Rebuild URL without sslmode
        new_query = urlencode({k: v[0] for k, v in query_params.items()})
        parsed = parsed._replace(query=new_query)
        url = urlunparse(parsed)

    return url, connect_args


# Create async database URL
ASYNC_DATABASE_URL, CONNECT_ARGS = get_async_database_url(DATABASE_URL)

# Create async engine with connection pooling
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
    connect_args=CONNECT_ARGS,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @router.get("/endpoint")
        async def endpoint(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database connection pool. Call on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)


async def close_db() -> None:
    """Close database connection pool. Call on app shutdown."""
    await engine.dispose()
