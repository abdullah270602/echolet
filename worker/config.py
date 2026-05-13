"""
Worker Configuration

Loads environment variables for SQS, database, and LLM connections.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# AWS SQS Configuration
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "google/gemini-2.5-flash-lite"

# Worker Settings
POLL_INTERVAL_SECONDS = 1
MAX_MESSAGES_PER_POLL = 10
VISIBILITY_TIMEOUT_SECONDS = 60
