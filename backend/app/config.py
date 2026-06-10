import os
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

# Clerk Authentication
# Format: https://<your-clerk-frontend-api>.clerk.accounts.dev/.well-known/jwks.json
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
# Clerk Webhook signing secret (from Clerk Dashboard -> Webhooks)
CLERK_WEBHOOK_SIGNING_SECRET = os.getenv("CLERK_WEBHOOK_SIGNING_SECRET")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Usage Limits
# Default: 1 hour (3600 seconds) per day
DAILY_TALK_LIMIT_SECONDS = int(os.getenv("DAILY_TALK_LIMIT_SECONDS", "3600"))

# CORS: comma-separated list of browser origins allowed to call the API
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

