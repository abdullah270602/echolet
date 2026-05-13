"""
Repository layer for agent configuration database operations.
"""
import uuid
from datetime import datetime, UTC
from typing import Optional, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_config import AgentConfig


async def get_by_id(
    session: AsyncSession,
    agent_id: int,
) -> Optional[AgentConfig]:
    """
    Get an agent configuration by its ID.

    Args:
        session: Database session
        agent_id: The agent's ID

    Returns:
        AgentConfig or None if not found
    """
    stmt = select(AgentConfig).where(AgentConfig.id == agent_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_user_id(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[AgentConfig]:
    """
    Get all active (non-deleted) agent configurations for a user.

    Args:
        session: Database session
        user_id: The user's identifier

    Returns:
        List of AgentConfig objects (excludes soft-deleted)
    """
    stmt = select(AgentConfig).where(
        AgentConfig.user_id == user_id,
        AgentConfig.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_agent_count(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """
    Get the count of active (non-deleted) agents for a user.

    Args:
        session: Database session
        user_id: The user's identifier

    Returns:
        Number of active agents the user has (excludes soft-deleted)
    """
    stmt = select(func.count()).select_from(AgentConfig).where(
        AgentConfig.user_id == user_id,
        AgentConfig.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    config: dict[str, Any],
    status: str = "inactive",
    phone: Optional[str] = None,
) -> AgentConfig:
    """
    Create a new agent configuration.

    Args:
        session: Database session
        user_id: The user's identifier
        config: The agent configuration data (JSONB)
        status: Agent status (default: inactive)
        phone: Optional phone number

    Returns:
        The created AgentConfig
    """
    agent = AgentConfig(
        user_id=user_id,
        config=config,
        status=status,
        phone=phone,
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


async def update(
    session: AsyncSession,
    agent: AgentConfig,
    config: Optional[dict[str, Any]] = None,
    status: Optional[str] = None,
    phone: Optional[str] = None,
) -> AgentConfig:
    """
    Update an existing agent configuration.

    Args:
        session: Database session
        agent: The agent to update
        config: New config data (replaces entire config if provided)
        status: New status (if provided)
        phone: New phone (if provided)

    Returns:
        The updated AgentConfig
    """
    if config is not None:
        agent.config = config
    if status is not None:
        agent.status = status
    if phone is not None:
        agent.phone = phone

    await session.commit()
    await session.refresh(agent)
    return agent


async def soft_delete(
    session: AsyncSession,
    agent: AgentConfig,
) -> AgentConfig:
    """
    Soft delete an agent by setting deleted_at timestamp.

    This preserves the agent record and associated call history.

    Args:
        session: Database session
        agent: The agent to soft delete

    Returns:
        The soft-deleted AgentConfig
    """
    agent.deleted_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(agent)
    return agent


async def delete(
    session: AsyncSession,
    agent: AgentConfig,
) -> None:
    """
    Hard delete an agent configuration.

    WARNING: This permanently deletes the agent and cascades to call_sessions.
    Use soft_delete() instead to preserve call history.

    Args:
        session: Database session
        agent: The agent to delete
    """
    await session.delete(agent)
    await session.commit()
