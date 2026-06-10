"""
Call Analysis Worker

Polls SQS for call sessions to analyze, fetches transcripts from DB,
runs LLM analysis, and updates the database with results.

Run with:
    uv run worker.py

Retry / DLQ policy:
    A message is deleted only when its outcome is final (analysis stored, or the
    message/call can never be analysed). Transient failures (LLM error, bad JSON,
    DB write failure) leave the message on the queue, so SQS redelivers it after
    the visibility timeout and the database keeps its "Pending" placeholder rather
    than a failure summary. Configure the source queue's redrive policy with a
    dead-letter queue and maxReceiveCount (e.g. 5) so a message that keeps failing
    is parked in the DLQ instead of retrying forever.
"""

import asyncio
import json
import logging
import signal
import sys

import boto3
from botocore.exceptions import ClientError

from config import (
    SQS_QUEUE_URL,
    AWS_REGION,
    POLL_INTERVAL_SECONDS,
    MAX_MESSAGES_PER_POLL,
    VISIBILITY_TIMEOUT_SECONDS,
)
from database import fetch_call_data, update_analysis
from analyzer import analyze_transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Attempts per call before a failed analysis is stored as a placeholder and the message dropped.
MAX_ANALYSIS_ATTEMPTS = 3


# Graceful shutdown flag
shutdown_requested = False


def get_sqs_client():
    """Get SQS client with configured region."""
    return boto3.client("sqs", region_name=AWS_REGION)


def poll_sqs(client) -> list[dict]:
    """
    Poll SQS for messages.

    Returns:
        List of message dicts with 'body' and 'receipt_handle'
    """
    try:
        response = client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=MAX_MESSAGES_PER_POLL,
            WaitTimeSeconds=20,  # Long polling
            VisibilityTimeout=VISIBILITY_TIMEOUT_SECONDS,
            AttributeNames=["ApproximateReceiveCount"],
        )

        messages = response.get("Messages", [])
        result = []

        for msg in messages:
            try:
                body = json.loads(msg["Body"])
                result.append({
                    "body": body,
                    "receipt_handle": msg["ReceiptHandle"],
                    "receive_count": int(msg.get("Attributes", {}).get("ApproximateReceiveCount", 1)),
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in message: {msg['Body']}")
                # Delete invalid message
                delete_message(client, msg["ReceiptHandle"])

        return result

    except ClientError as e:
        logger.error(f"SQS poll error: {e}")
        return []


def delete_message(client, receipt_handle: str) -> bool:
    """Delete a message from SQS after processing."""
    try:
        client.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle,
        )
        return True
    except ClientError as e:
        logger.error(f"Failed to delete SQS message: {e}")
        return False


async def process_message(message: dict) -> bool:
    """
    Process a single message from the queue.

    Args:
        message: Dict with 'body' containing room_name

    Returns:
        True if the message is finished and may be deleted; False to leave it for redelivery
    """
    body = message["body"]
    room_name = body.get("room_name")

    if not room_name:
        logger.warning(f"Message missing room_name: {body}")
        return True  # Return True to delete invalid message

    logger.info(f"Processing call: {room_name}")

    # Fetch transcript and output config
    call_data = await fetch_call_data(room_name)

    if call_data is None:
        logger.warning(f"No call data found for {room_name}")
        return True  # Delete message even if no data (avoid infinite retries)

    transcript = call_data.get("transcript")
    output_config = call_data.get("output_config")

    if not transcript:
        logger.warning(f"No transcript found for {room_name}")
        return True

    # Analyze with LLM using configured output fields
    analysis = await analyze_transcript(transcript, output_config, call_data=call_data.get("call_data"))

    # analyze_transcript flags placeholder results (LLM error, bad JSON, no API key).
    # Retry a few times (SQS redelivers after the visibility timeout); after that, store
    # the placeholder so the call shows "please review the transcript" and stop retrying.
    # This bound holds even if the queue has no dead-letter redrive configured.
    if analysis.get("failed") and message.get("receive_count", 1) >= MAX_ANALYSIS_ATTEMPTS:
        logger.error(f"Analysis failed {MAX_ANALYSIS_ATTEMPTS} times for {room_name}; storing placeholder")
    elif analysis.get("failed"):
        logger.error(f"Analysis failed for {room_name}; leaving message on the queue for redelivery")
        return False  # not deleted, DB untouched

    # Log available fields
    log_parts = [f"Analysis complete for {room_name}:"]
    if "category" in analysis:
        log_parts.append(f"category={analysis['category']}")
    if "urgency" in analysis:
        log_parts.append(f"urgency={analysis['urgency']}")
    if "sentiment" in analysis:
        log_parts.append(f"sentiment={analysis['sentiment']}")
    if "action_required" in analysis:
        log_parts.append(f"action_required={analysis['action_required']}")
    if "action_items" in analysis:
        log_parts.append(f"actions={len(analysis['action_items'])}")

    logger.info(", ".join(log_parts))

    # Update database with available fields
    success = await update_analysis(
        room_name=room_name,
        summary=analysis.get("summary", "No summary"),
        category=analysis.get("category", "Other"),
        urgency=analysis.get("urgency", "Medium"),
        sentiment=analysis.get("sentiment", "Neutral"),
        action_required=analysis.get("action_required", False),
        action_items=analysis.get("action_items", []),
        ticket={"fields": analysis.get("fields", {}), "tags": analysis.get("tags", [])},
    )

    if not success and message.get("receive_count", 1) >= MAX_ANALYSIS_ATTEMPTS:
        logger.error(f"Saving analysis failed {MAX_ANALYSIS_ATTEMPTS} times for {room_name}; dropping the message")
        return True
    return success


async def main():
    """Main worker loop."""
    global shutdown_requested

    if not SQS_QUEUE_URL:
        logger.error("SQS_QUEUE_URL not configured")
        sys.exit(1)

    logger.info(f"Worker starting - polling {SQS_QUEUE_URL}")

    client = get_sqs_client()

    while not shutdown_requested:
        try:
            # Poll for messages
            messages = await asyncio.to_thread(poll_sqs, client)

            if not messages:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            logger.info(f"Received {len(messages)} message(s)")

            # Process each message
            for msg in messages:
                if shutdown_requested:
                    break

                try:
                    success = await process_message(msg)
                    if success:
                        await asyncio.to_thread(delete_message, client, msg["receipt_handle"])
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Don't delete - let it retry after visibility timeout

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    logger.info("Worker shutdown complete")


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_requested = True


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Run the worker
    asyncio.run(main())
