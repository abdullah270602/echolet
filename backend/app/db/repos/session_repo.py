import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.call_session import CallSession
from app.db.models.agent_config import AgentConfig


async def get_by_id(
    session: AsyncSession,
    session_id: int,
) -> Optional[CallSession]:
    """
    Get a call session by its ID.

    Args:
        session: Database session
        session_id: The session's ID

    Returns:
        CallSession or None if not found
    """
    stmt = select(CallSession).where(CallSession.id == session_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_room_name(
    session: AsyncSession,
    room_name: str,
) -> Optional[CallSession]:
    """
    Get a call session by its room name (UUID).

    Args:
        session: Database session
        room_name: The UUID room name

    Returns:
        CallSession or None if not found
    """
    stmt = select(CallSession).where(CallSession.room_name == room_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_room_name_with_agent(
    session: AsyncSession,
    room_name: str,
) -> Optional[tuple[CallSession, AgentConfig]]:
    """
    Get a call session with its associated agent config.

    Args:
        session: Database session
        room_name: The UUID room name

    Returns:
        Tuple of (CallSession, AgentConfig) or None if not found
    """
    stmt = (
        select(CallSession, AgentConfig)
        .join(AgentConfig, CallSession.agent_id == AgentConfig.id)
        .where(CallSession.room_name == room_name)
    )
    result = await session.execute(stmt)
    row = result.first()
    if row:
        return (row[0], row[1])
    return None


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_id: int,
) -> CallSession:
    """
    Create a new call session with auto-generated room_name UUID.

    Args:
        session: Database session
        user_id: The user's identifier
        agent_id: The agent's ID

    Returns:
        The created CallSession
    """
    call_session = CallSession(
        user_id=user_id,
        agent_id=agent_id,
        status="pending",
    )
    session.add(call_session)
    await session.commit()
    await session.refresh(call_session)
    return call_session


async def update_status(
    session: AsyncSession,
    call_session: CallSession,
    status: str,
) -> CallSession:
    """
    Update the status of a call session.

    Args:
        session: Database session
        call_session: The session to update
        status: New status value

    Returns:
        The updated CallSession
    """
    call_session.status = status
    await session.commit()
    await session.refresh(call_session)
    return call_session


async def update_call_log(
    session: AsyncSession,
    room_name: str,
    transcript: list[dict[str, Any]],
    duration_seconds: int,
    status: str = "completed",
    summary: Optional[str] = "Pending",
    priority: str = "normal",
) -> Optional[CallSession]:
    """
    Update a call session with transcript and completion data.

    Args:
        session: Database session
        room_name: The UUID room name
        transcript: List of message dicts with role, content, timestamp
        duration_seconds: Total call duration in seconds
        status: Session status (default: "completed")
        summary: AI-generated summary (default: "Pending")
        priority: Call priority level (default: "normal")

    Returns:
        The updated CallSession or None if not found
    """
    call_session = await get_by_room_name(session, room_name)
    if not call_session:
        return None

    call_session.transcript = transcript
    call_session.duration_seconds = duration_seconds
    call_session.status = status
    call_session.summary = summary
    call_session.priority = priority
    call_session.ended_at = datetime.utcnow()

    await session.commit()
    await session.refresh(call_session)
    return call_session


async def get_user_call_history(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Get recent call history for a user with agent info, ordered by created_at descending.

    Args:
        session: Database session
        user_id: The user's identifier
        limit: Maximum number of records to return (default: 50)

    Returns:
        List of dicts with CallSession data plus agent_name and is_agent_deleted
    """
    # Extract agent name from JSONB config column: config['agent']['name']
    stmt = (
        select(
            CallSession,
            AgentConfig.config['agent']['name'].astext.label('agent_name'),
            AgentConfig.deleted_at.label('agent_deleted_at'),
        )
        .outerjoin(AgentConfig, CallSession.agent_id == AgentConfig.id)
        .where(CallSession.user_id == user_id)
        .where(CallSession.status.in_(["completed", "failed"]))
        .order_by(desc(CallSession.created_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()

    call_history = []
    for call_session, agent_name, agent_deleted_at in rows:
        # Convert CallSession to dict and add agent info
        call_dict = {
            "id": call_session.id,
            "room_name": call_session.room_name,
            "user_id": call_session.user_id,
            "agent_id": call_session.agent_id,
            "status": call_session.status,
            "duration_seconds": call_session.duration_seconds,
            "transcript": call_session.transcript,
            "summary": call_session.summary,
            "priority": call_session.priority,
            "sentiment": call_session.sentiment,
            "action_items": call_session.action_items,
            "category": call_session.category,
            "urgency": call_session.urgency,
            "action_required": call_session.action_required,
            "created_at": call_session.created_at,
            "ended_at": call_session.ended_at,
            "agent_name": agent_name,
            "is_agent_deleted": agent_deleted_at is not None,
        }
        call_history.append(call_dict)

    return call_history
