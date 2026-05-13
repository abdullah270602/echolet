"""Clerk webhook route - thin dispatcher."""

import logging

from fastapi import APIRouter, Request, HTTPException, Depends
from svix.webhooks import Webhook, WebhookVerificationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.config import CLERK_WEBHOOK_SIGNING_SECRET
from app.webhook_handlers import dispatch

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhooks")
async def clerk_webhook(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Clerk webhook endpoint.

    Verifies signature and dispatches to registered handlers.
    """
    # 1. Get headers and body
    payload = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id"),
        "svix-timestamp": request.headers.get("svix-timestamp"),
        "svix-signature": request.headers.get("svix-signature"),
    }

    # 2. Verify webhook signature
    if not CLERK_WEBHOOK_SIGNING_SECRET:
        logger.error("CLERK_WEBHOOK_SIGNING_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")

    try:
        wh = Webhook(CLERK_WEBHOOK_SIGNING_SECRET)
        event = wh.verify(payload, headers)
    except WebhookVerificationError as e:
        logger.warning(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # 3. Dispatch to handler
    event_type = event.get("type", "")
    data = event.get("data", {})

    logger.info(f"Received Clerk webhook: {event_type}")
    await dispatch(session, event_type, data)

    return {"status": "ok"}
