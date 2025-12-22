from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_config import AgentConfig
from app.db.repos import agent_repo
from app.schemas.agent import AgentCreateRequest, AgentUpdateRequest, DEFAULT_CONFIG


async def list_agents(
    session: AsyncSession,
    user_id: str,
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
    user_id: str,
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

    return agent


async def create_agent(
    session: AsyncSession,
    user_id: str,
    data: AgentCreateRequest,
) -> AgentConfig:
    """
    Create a new agent for a user.

    Args:
        session: Database session
        user_id: The user's identifier
        data: Agent creation data

    Returns:
        The created AgentConfig

    Raises:
        HTTPException: If user has reached agent limit
    """
    # Check if user has reached agent limit
    count = await agent_repo.get_user_agent_count(session, user_id)
    max_agents = DEFAULT_CONFIG.max_agents_per_user
    if count >= max_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Agent limit reached. Maximum {max_agents} agent(s) allowed.",
        )

    return await agent_repo.create(session, user_id, data)


async def update_agent(
    session: AsyncSession,
    user_id: str,
    agent_id: int,
    data: AgentUpdateRequest,
) -> AgentConfig:
    """
    Update an existing agent.

    Args:
        session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID
        data: Update data

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

    return await agent_repo.update(session, agent, data)


async def delete_agent(
    session: AsyncSession,
    user_id: str,
    agent_id: int,
) -> None:
    """
    Delete an agent.

    Args:
        session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID

    Raises:
        HTTPException: If agent not found or user not authorized
    """
    agent = await agent_repo.get_by_id(session, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this agent")

    await agent_repo.delete(session, agent)
