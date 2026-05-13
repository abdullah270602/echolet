"""
Agent configuration API routes.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_with_db
from app.db.database import get_async_session
from app.schemas.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentConfigData,
    VoiceOption,
    SpeakingStyleOption,
    TicketField,
    AVAILABLE_VOICES,
    AVAILABLE_SPEAKING_STYLES,
    DEFAULT_TICKET_FIELDS,
    SUGGESTED_TAGS,
    get_default_config,
)
from app.services import agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# CONFIGURATION ENDPOINTS (No auth required)
# =============================================================================

@router.get("/defaults", response_model=AgentConfigData)
async def get_defaults() -> AgentConfigData:
    """
    Get default agent configuration template.

    Returns a complete AgentConfigData with all default values that can be
    used as a starting point for creating a new agent.
    """
    return get_default_config()


@router.get("/voices", response_model=list[VoiceOption])
async def list_voices(
    provider: Optional[str] = Query(None, description="Filter by TTS provider")
) -> list[VoiceOption]:
    """
    Get list of available voice options.

    Optionally filter by provider (inworld, deepgram).
    If no provider specified, returns all voices grouped by provider.
    """
    if provider:
        return AVAILABLE_VOICES.get(provider, [])

    # Return all voices flattened
    all_voices = []
    for voices in AVAILABLE_VOICES.values():
        all_voices.extend(voices)
    return all_voices


@router.get("/voices/{provider}", response_model=list[VoiceOption])
async def list_voices_by_provider(provider: str) -> list[VoiceOption]:
    """
    Get voice options for a specific TTS provider.
    """
    return AVAILABLE_VOICES.get(provider, [])


@router.get("/speaking-styles", response_model=list[SpeakingStyleOption])
async def list_speaking_styles() -> list[SpeakingStyleOption]:
    """
    Get list of available speaking style options.
    """
    return AVAILABLE_SPEAKING_STYLES


@router.get("/output-fields", response_model=list[TicketField])
async def list_output_fields() -> list[TicketField]:
    """
    Get list of default ticket/output fields.

    These are the standard fields that can be enabled/disabled
    in an agent's output configuration.
    """
    return DEFAULT_TICKET_FIELDS


@router.get("/suggested-tags", response_model=list[str])
async def list_suggested_tags() -> list[str]:
    """
    Get list of suggested custom tags for call categorization.
    """
    return SUGGESTED_TAGS


# =============================================================================
# AGENT CRUD ENDPOINTS (Auth required)
# =============================================================================

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

    # Transform ORM models to response schema
    # Handle legacy configs that may not match the new schema
    responses = []
    for agent in agents:
        try:
            config = AgentConfigData.model_validate(agent.config)
        except ValidationError as e:
            # Log and skip agents with invalid/legacy config
            logger.warning(f"Agent {agent.id} has invalid config, skipping: {e}")
            continue

        responses.append(AgentResponse(
            id=agent.id,
            user_id=agent.user_id,
            config=config,
            status=agent.status,
            phone=agent.phone,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        ))
    return responses


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    data: AgentCreateRequest,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> AgentResponse:
    """
    Create a new agent configuration.

    Users are limited to 3 agents. The request body should include
    the full agent configuration in the `config` field.
    """
    user_id = current_user["id"]
    agent = await agent_service.create_agent(session, user_id, data)

    return AgentResponse(
        id=agent.id,
        user_id=agent.user_id,
        config=AgentConfigData.model_validate(agent.config),
        status=agent.status,
        phone=agent.phone,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


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

    return AgentResponse(
        id=agent.id,
        user_id=agent.user_id,
        config=AgentConfigData.model_validate(agent.config),
        status=agent.status,
        phone=agent.phone,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    data: AgentUpdateRequest,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> AgentResponse:
    """
    Update an existing agent configuration.

    The entire config object must be provided if updating config.
    Status and phone can be updated independently.
    """
    user_id = current_user["id"]
    agent = await agent_service.update_agent(session, user_id, agent_id, data)

    return AgentResponse(
        id=agent.id,
        user_id=agent.user_id,
        config=AgentConfigData.model_validate(agent.config),
        status=agent.status,
        phone=agent.phone,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    current_user: dict = Depends(get_current_user_with_db),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Soft delete an agent configuration.

    The agent record is preserved for call history but will no longer
    appear in listings or be usable for new calls.
    """
    user_id = current_user["id"]
    await agent_service.delete_agent(session, user_id, agent_id)
