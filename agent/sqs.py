"""
SQS Integration for Call Analysis Queue

Sends call session IDs to SQS for async processing by the worker service.
"""

import json
import logging
import time

import boto3
from botocore.exceptions import ClientError

from config import SQS_QUEUE_URL, AWS_REGION

logger = logging.getLogger(__name__)


def get_sqs_client():
    """Get SQS client with configured region."""
    return boto3.client("sqs", region_name=AWS_REGION)


async def send_to_analysis_queue(room_name: str) -> bool:
    """
    Send a call session to the analysis queue for processing.

    Args:
        room_name: The UUID room name (used as session identifier)

    Returns:
        True if message was sent successfully, False otherwise
    """
    if not SQS_QUEUE_URL:
        logger.warning("SQS_QUEUE_URL not configured, skipping queue send")
        return False

    try:
        client = get_sqs_client()

        message_body = json.dumps({
            "room_name": room_name,
            "timestamp": time.time(),
        })

        response = client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body,
        )

        message_id = response.get("MessageId")
        logger.info(f"Sent to analysis queue: {room_name} (MessageId: {message_id})")
        return True

    except ClientError as e:
        logger.error(f"Failed to send to SQS: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to SQS: {e}")
        return False
