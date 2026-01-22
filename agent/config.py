import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Environment Variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# AWS SQS Configuration
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION")

# LLM Configuration
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "google/gemini-2.5-flash-lite"  

# STT (Speech-to-Text) Configuration
STT_MODEL = "nova-2"
STT_EAGER_EOT_THRESHOLD = 0.4

# TTS (Text-to-Speech) Configuration
TTS_MODEL = "inworld-tts-1.5-mini"
TTS_VOICE = "Hades"

