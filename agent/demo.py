"""
Landing-page demo calls.

The backend mints demo tokens for rooms named ``demo-<uuid>`` and puts the agent
config plus a hard time cap in the participant metadata. That metadata is part
of a JWT signed with our LiveKit API secret, so it is trusted the same way the
room name is. Demo calls are never persisted or analysed.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

DEMO_ROOM_PREFIX = "demo-"
# Hard ceiling even if a token somehow carries a larger value.
DEMO_MAX_SECONDS_CEILING = 300


def is_demo_room(room_name: str) -> bool:
    return room_name.startswith(DEMO_ROOM_PREFIX)


def parse_demo_metadata(metadata: str) -> Optional[tuple[dict[str, Any], int]]:
    """Return (config, max_seconds) from a demo participant's metadata, or None if invalid."""
    try:
        data = json.loads(metadata or "")
        config = data["config"]
        max_seconds = int(data["max_seconds"])
    except (ValueError, KeyError, TypeError, AttributeError):
        logger.warning("Demo participant has missing or malformed metadata")
        return None
    if not data.get("demo") or not isinstance(config, dict) or max_seconds <= 0:
        return None
    return config, min(max_seconds, DEMO_MAX_SECONDS_CEILING)


DEMO_VOICE = {"provider": "deepgram", "voice_id": "aura-2-thalia-en"}

DEMO_FAREWELL = (
    "That's the end of the demo call. Thanks for trying Echolet, have a great day!"
)


# Drop-in replacements for save_call_log / send_to_analysis_queue on demo calls.
async def skip_save_call_log(**_kwargs) -> bool:
    return True


async def skip_analysis_queue(_room_name: str) -> None:
    return None
