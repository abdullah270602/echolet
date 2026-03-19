"""
Service layer for agent configuration business logic.
"""
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_config import AgentConfig
from app.db.repos import agent_repo
from app.schemas.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
)


# Maximum agents per user
MAX_AGENTS_PER_USER = 3


async def list_agents(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[AgentConfig]:
    """
    List all agents for a user.

    Args:
        session: Database session
        user_id: The user's identifier

    Returns:
        List of AgentConfig objects
    """
    return await agent_repo.get_by_user_id(session, user_id)


async def get_agent(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_id: int,
) -> AgentConfig:
    """
    Get a specific agent by ID.

    Args:
        session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID

    Returns:
        AgentConfig object

    Raises:
        HTTPException: If agent not found or user not authorized
    """
    agent = await agent_repo.get_by_id(session, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this agent")

    if agent.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


async def create_agent(
    session: AsyncSession,
    user_id: uuid.UUID,
    data: AgentCreateRequest,
) -> AgentConfig:
    """
    Create a new agent for a user.

    Args:
        session: Database session
        user_id: The user's identifier
        data: Agent creation data with nested config

    Returns:
        The created AgentConfig

    Raises:
        HTTPException: If user has reached agent limit
    """
    # Check if user has reached agent limit
    count = await agent_repo.get_user_agent_count(session, user_id)
    if count >= MAX_AGENTS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Agent limit reached. Maximum {MAX_AGENTS_PER_USER} agent(s) allowed.",
        )

    # Convert Pydantic model to dict for JSONB storage
    config_dict = data.config.model_dump()

    return await agent_repo.create(
        session=session,
        user_id=user_id,
        config=config_dict,
        status=data.status,
        phone=data.phone,
    )


async def update_agent(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_id: int,
    data: AgentUpdateRequest,
) -> AgentConfig:
    """
    Update an existing agent.

    Args:
        session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID
        data: Update data (partial - only provided fields are updated)

    Returns:
        The updated AgentConfig

    Raises:
        HTTPException: If agent not found or user not authorized
    """
    agent = await agent_repo.get_by_id(session, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this agent")

    if agent.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Convert config to dict if provided
    config_dict = data.config.model_dump() if data.config else None

    return await agent_repo.update(
        session=session,
        agent=agent,
        config=config_dict,
        status=data.status,
        phone=data.phone,
    )


async def delete_agent(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_id: int,
) -> None:
    """
    Soft delete an agent (preserves call history).

    Args:
        session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID

    Raises:
        HTTPException: If agent not found, already deleted, or user not authorized
    """
    agent = await agent_repo.get_by_id(session, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this agent")

    if agent.deleted_at is not None:
        raise HTTPException(status_code=400, detail="Agent already deleted")

    await agent_repo.soft_delete(session, agent)
