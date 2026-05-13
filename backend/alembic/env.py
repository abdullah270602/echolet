import asyncio
import ssl
from logging.config import fileConfig
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.db.base import Base
from app.db.models import UserDailyUsage, AgentConfig  # noqa: F401 - Import to register models
from app.config import DATABASE_URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_async_url() -> tuple[str, dict]:
    """Convert DATABASE_URL to asyncpg format with SSL handling."""
    if DATABASE_URL is None:
        raise ValueError("DATABASE_URL environment variable is not set")

    url = DATABASE_URL
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


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url, _ = get_async_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    url, connect_args = get_async_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# Tables owned outside the ORM (written by the landing page's Vercel function).
# Without this, `alembic revision --autogenerate` would propose dropping them.
UNMANAGED_TABLES = {"waitlist"}


def include_object(obj, name, type_, reflected, compare_to):
    return not (type_ == "table" and name in UNMANAGED_TABLES)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
