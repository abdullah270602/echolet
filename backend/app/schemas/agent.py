from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


# Voice options for dropdown
class VoiceOption(BaseModel):
    id: str
    name: str
    gender: str
    description: str


# Tone options for dropdown
class ToneOption(BaseModel):
    id: str
    name: str
    description: str


# Agent configuration limits
class AgentConfigLimits(BaseModel):
    max_agents_per_user: int
    default_voice_id: str
    default_tone: str
    default_greeting_message: str


# Create request
class AgentCreateRequest(BaseModel):
    name: str
    business_name: str
    voice_id: str = "Ashely"
    greeting_message: str = "Hello! How can I help you today?"
    tone: Literal["professional", "friendly", "urgent"] = "professional"
    custom_instructions: Optional[str] = None
    knowledge_base_text: Optional[str] = None
    max_duration_seconds: int = 600


# Update request (all optional for PATCH)
class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    voice_id: Optional[str] = None
    greeting_message: Optional[str] = None
    tone: Optional[Literal["professional", "friendly", "urgent"]] = None
    custom_instructions: Optional[str] = None
    knowledge_base_text: Optional[str] = None
    max_duration_seconds: Optional[int] = None
    status: Optional[Literal["active", "inactive", "paused"]] = None


# Response
class AgentResponse(BaseModel):
    id: int
    user_id: str
    name: str
    business_name: str
    voice_id: str
    greeting_message: str
    tone: str
    custom_instructions: Optional[str]
    knowledge_base_text: Optional[str]
    max_duration_seconds: int
    status: str
    phone: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# List of available voices (static data)
AVAILABLE_VOICES: list[VoiceOption] = [
    VoiceOption(
        id="Ashely",
        name="Ashely",
        gender="Female",
        description="American accent, professional tone",
    ),
    VoiceOption(
        id="Mark",
        name="Mark",
        gender="Male",
        description="Call center style, clear pronunciation",
    ),
    VoiceOption(
        id="Denis",
        name="Denis",
        gender="Male",
        description="Supportive and warm tone",
    ),
]

# List of available tones
AVAILABLE_TONES: list[ToneOption] = [
    ToneOption(
        id="professional",
        name="Professional",
        description="Formal and business-like",
    ),
    ToneOption(
        id="friendly",
        name="Friendly",
        description="Warm and approachable",
    ),
    ToneOption(
        id="urgent",
        name="Urgent",
        description="Direct and action-oriented",
    ),
]

# Default configuration
DEFAULT_CONFIG = AgentConfigLimits(
    max_agents_per_user=3,
    default_voice_id="Ashely",
    default_tone="professional",
    default_greeting_message="Hello! How can I help you today?",
)
