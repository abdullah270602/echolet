"""Handlers for Clerk user events."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repos import user_repo, agent_repo
from app.agent_templates.default import DEFAULT_AGENT_CONFIG

logger = logging.getLogger(__name__)


async def handle_user_created(session: AsyncSession, data: dict[str, Any]) -> None:
    """
    Handle user.created event.

    1. Upsert user to database
    2. Seed default agent (if user has no agents)

    Args:
        session: Database session
        data: Clerk user data payload
    """
    clerk_id = data.get("id")
    if not clerk_id:
        logger.warning("user.created event missing clerk_id")
        return

    # Extract primary email
    email = _extract_primary_email(data)

    # 1. Upsert user to database and get internal ID
    user = await user_repo.upsert_user(session, clerk_id, email)
    logger.info(f"User synced: {clerk_id} -> internal ID: {user.id}")

    # 2. Check if user already has agents (idempotency)
    agent_count = await agent_repo.get_user_agent_count(session, user.id)
    if agent_count > 0:
        logger.info(f"User {clerk_id} already has {agent_count} agent(s), skipping seed")
        return

    # 3. Seed default agent with internal user ID
    agent = await agent_repo.create(
        session,
        user_id=user.id,
        config=DEFAULT_AGENT_CONFIG.model_dump(),
        status="active",
    )
    logger.info(f"Default agent seeded for {clerk_id}: agent_id={agent.id}")


async def handle_user_deleted(session: AsyncSession, data: dict[str, Any]) -> None:
    """
    Handle user.deleted event - permanently delete user and all associated data.

    With FK CASCADE constraints, deleting the user automatically deletes:
    - All agent_configs
    - All call_sessions
    - All user_daily_usage records

    Args:
        session: Database session
        data: Clerk user data payload
    """
    clerk_id = data.get("id")
    if not clerk_id:
        logger.warning("user.deleted event missing clerk_id")
        return

    # Look up user by clerk_id
    user = await user_repo.get_by_clerk_id(session, clerk_id)
    if not user:
        logger.info(f"User {clerk_id} not found in database (may already be deleted)")
        return

    # Delete user - CASCADE handles all related data
    await session.delete(user)
    await session.commit()

    logger.info(f"Permanently deleted user and all associated data for Clerk ID: {clerk_id}")


def _extract_primary_email(data: dict[str, Any]) -> str:
    """
    Extract primary email from Clerk user data.

    Args:
        data: Clerk user data payload

    Returns:
        Primary email address, or empty string if not found
    """
    email_addresses = data.get("email_addresses", [])
    primary_id = data.get("primary_email_address_id")

    # Find primary email
    for addr in email_addresses:
        if addr.get("id") == primary_id:
            return addr.get("email_address", "")

    # Fallback to first email
    if email_addresses:
        return email_addresses[0].get("email_address", "")

    return ""
