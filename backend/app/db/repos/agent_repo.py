from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_config import AgentConfig
from app.schemas.agent import AgentCreateRequest, AgentUpdateRequest


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
    user_id: str,
) -> list[AgentConfig]:
    """
    Get all agent configurations for a user.

    Args:
        session: Database session
        user_id: The user's identifier

    Returns:
        List of AgentConfig objects
    """
    stmt = select(AgentConfig).where(AgentConfig.user_id == user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_agent_count(
    session: AsyncSession,
    user_id: str,
) -> int:
    """
    Get the count of agents for a user.

    Args:
        session: Database session
        user_id: The user's identifier

    Returns:
        Number of agents the user has
    """
    stmt = select(func.count()).select_from(AgentConfig).where(
        AgentConfig.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def create(
    session: AsyncSession,
    user_id: str,
    data: AgentCreateRequest,
) -> AgentConfig:
    """
    Create a new agent configuration.

    Args:
        session: Database session
        user_id: The user's identifier
        data: Agent creation data

    Returns:
        The created AgentConfig
    """
    agent = AgentConfig(
        user_id=user_id,
        name=data.name,
        business_name=data.business_name,
        voice_id=data.voice_id,
        greeting_message=data.greeting_message,
        tone=data.tone,
        custom_instructions=data.custom_instructions,
        knowledge_base_text=data.knowledge_base_text,
        max_duration_seconds=data.max_duration_seconds,
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


async def update(
    session: AsyncSession,
    agent: AgentConfig,
    data: AgentUpdateRequest,
) -> AgentConfig:
    """
    Update an existing agent configuration.

    Args:
        session: Database session
        agent: The agent to update
        data: Update data (only non-None fields are updated)

    Returns:
        The updated AgentConfig
    """
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(agent, field, value)

    await session.commit()
    await session.refresh(agent)
    return agent


async def delete(
    session: AsyncSession,
    agent: AgentConfig,
) -> None:
    """
    Delete an agent configuration.

    Args:
        session: Database session
        agent: The agent to delete
    """
    await session.delete(agent)
    await session.commit()
