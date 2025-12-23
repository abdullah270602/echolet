import os
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

# Clerk Authentication
# Format: https://<your-clerk-frontend-api>.clerk.accounts.dev/.well-known/jwks.json
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Usage Limits
# Default: 3 minutes (180 seconds) per day
DAILY_TALK_LIMIT_SECONDS = int(os.getenv("DAILY_TALK_LIMIT_SECONDS", 600))
