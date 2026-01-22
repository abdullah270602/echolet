"""Clerk webhook handler registry."""

import logging
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from app.webhook_handlers import user_events

logger = logging.getLogger(__name__)

# Type alias for handler functions
HandlerType = Callable[[AsyncSession, dict[str, Any]], Coroutine[Any, Any, None]]

# Registry: event_type -> handler function
HANDLERS: dict[str, HandlerType] = {
    "user.created": user_events.handle_user_created,
    # Add more handlers here:
    # "user.deleted": user_events.handle_user_deleted,
}


async def dispatch(session: AsyncSession, event_type: str, data: dict[str, Any]) -> None:
    """
    Dispatch event to appropriate handler.

    Args:
        session: Database session
        event_type: Clerk event type (e.g., "user.created")
        data: Event payload data
    """
    handler = HANDLERS.get(event_type)

    if handler is None:
        logger.debug(f"No handler registered for event: {event_type}")
        return

    try:
        await handler(session, data)
        logger.info(f"Successfully handled {event_type}")
    except Exception as e:
        # Log but don't raise - return 200 to Clerk
        logger.error(f"Handler error for {event_type}: {e}", exc_info=True)
