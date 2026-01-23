from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_with_db
from app.db.database import get_async_session
from app.schemas.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    VoiceOption,
    ToneOption,
    AgentConfigLimits,
    AVAILABLE_VOICES,
    AVAILABLE_TONES,
    DEFAULT_CONFIG,
)
from app.services import agent_service

router = APIRouter()


@router.get("/config", response_model=AgentConfigLimits)
async def get_config() -> AgentConfigLimits:
    """
    Get agent configuration limits and defaults.
    This endpoint does not require authentication.
    """
    return DEFAULT_CONFIG


@router.get("/voices", response_model=list[VoiceOption])
async def list_voices() -> list[VoiceOption]:
    """
    Get list of available voice options for agents.
    This endpoint does not require authentication.
    """
    return AVAILABLE_VOICES


@router.get("/tones", response_model=list[ToneOption])
async def list_tones() -> list[ToneOption]:
    """
    Get list of available tone options for agents.
    This endpoint does not require authentication.
    """
    return AVAILABLE_TONES


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> list[AgentResponse]:
    """
    List all agents for the current user.
    """
    user_id = current_user["id"]
    agents = await agent_service.list_agents(session, user_id)
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    data: AgentCreateRequest,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> AgentResponse:
    """
    Create a new agent configuration.
    Users are limited to 1 agent.
    """
    user_id = current_user["id"]
    agent = await agent_service.create_agent(session, user_id, data)
    return AgentResponse.model_validate(agent)


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> AgentResponse:
    """
    Get a specific agent by ID.
    """
    user_id = current_user["id"]
    agent = await agent_service.get_agent(session, user_id, agent_id)
    return AgentResponse.model_validate(agent)


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    data: AgentUpdateRequest,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> AgentResponse:
    """
    Update an existing agent configuration.
    Only non-null fields in the request will be updated.
    """
    user_id = current_user["id"]
    agent = await agent_service.update_agent(session, user_id, agent_id, data)
    return AgentResponse.model_validate(agent)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete an agent configuration.
    """
    user_id = current_user["id"]
    await agent_service.delete_agent(session, user_id, agent_id)
