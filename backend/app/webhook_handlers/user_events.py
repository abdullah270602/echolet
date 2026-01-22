"""Handlers for Clerk user events."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repos import user_repo, agent_repo
from app.agent_templates.default import DEFAULT_AGENT_TEMPLATE
from app.schemas.agent import AgentCreateRequest

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

    # 1. Upsert user to database
    await user_repo.upsert_user(session, clerk_id, email)
    logger.info(f"User synced: {clerk_id}")

    # 2. Check if user already has agents (idempotency)
    agent_count = await agent_repo.get_user_agent_count(session, clerk_id)
    if agent_count > 0:
        logger.info(f"User {clerk_id} already has {agent_count} agent(s), skipping seed")
        return

    # 3. Seed default agent
    agent_data = AgentCreateRequest(**DEFAULT_AGENT_TEMPLATE)
    agent = await agent_repo.create(session, user_id=clerk_id, data=agent_data)
    logger.info(f"Default agent seeded for {clerk_id}: agent_id={agent.id}")


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
