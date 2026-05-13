"""
Agent configuration schemas.

Defines the nested configuration structure stored as JSONB in agent_configs.config
"""
from datetime import datetime
from typing import Optional, Literal, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# DROPDOWN OPTIONS (for frontend forms)
# =============================================================================

class VoiceOption(BaseModel):
    """Voice option for dropdown selection."""
    id: str
    name: str
    gender: str
    description: str
    provider: str  # Which TTS provider this voice belongs to


class SpeakingStyleOption(BaseModel):
    """Speaking style option for dropdown."""
    id: str
    name: str
    description: str


# =============================================================================
# NESTED CONFIG MODELS
# =============================================================================

class AgentIdentity(BaseModel):
    """Agent identity configuration."""
    name: str
    business_name: str
    greeting_message: str = "Hello! How can I help you today?"


class VoiceConfig(BaseModel):
    """Voice/TTS configuration."""
    provider: Literal["inworld", "deepgram"] = "inworld"
    voice_id: str = "Ashley"
    language: str = "en-US"
    speaking_style: str = "calm_professional"


class Service(BaseModel):
    """Service that can be booked or discussed."""
    name: str
    price: Optional[str] = None
    duration_minutes: Optional[int] = None


class KnowledgeSource(BaseModel):
    """Knowledge base source (text or website)."""
    type: Literal["text", "website"]
    name: str
    content: Optional[str] = None  # For text type
    url: Optional[str] = None      # For website type


class KnowledgeBase(BaseModel):
    """Knowledge base configuration."""
    sources: list[KnowledgeSource] = Field(default_factory=list)


class TicketField(BaseModel):
    """Output ticket field configuration."""
    id: str
    label: str
    type: Literal["string", "text", "number", "boolean", "select", "array", "datetime"]
    options: Optional[list[str]] = None  # For select type
    enabled: bool = True
    required: bool = False


class OutputConfig(BaseModel):
    """Output/ticket configuration."""
    ticket_fields: list[TicketField] = Field(default_factory=list)
    custom_tags: list[str] = Field(default_factory=list)


class Compliance(BaseModel):
    """Compliance settings."""
    hipaa_mode: bool = False
    gdpr_mode: bool = False
    call_recording_disclaimer: bool = True


class Guardrails(BaseModel):
    """Guardrails configuration."""
    allowed_topics: list[str] = Field(default_factory=list)
    disallowed_topics: list[str] = Field(default_factory=list)
    compliance: Compliance = Field(default_factory=Compliance)


class EndCallThreshold(BaseModel):
    """End call threshold settings."""
    silence_seconds: int = 20
    max_retries: int = 2


class BusinessHoursDay(BaseModel):
    """Business hours for a single day."""
    day: str
    open: Optional[str] = None  # "09:00"
    close: Optional[str] = None  # "17:00"


class BusinessHours(BaseModel):
    """Business hours configuration."""
    enabled: bool = False
    timezone: str = "America/New_York"
    schedule: list[BusinessHoursDay] = Field(default_factory=list)
    after_hours_behavior: str = "offer_callback"


class ConversationConfig(BaseModel):
    """Conversation behavior configuration."""
    end_call_threshold: EndCallThreshold = Field(default_factory=EndCallThreshold)
    business_hours: BusinessHours = Field(default_factory=BusinessHours)


# =============================================================================
# MAIN CONFIG MODEL
# =============================================================================

class AgentConfigData(BaseModel):
    """
    The complete agent configuration stored as JSONB.

    This is the structure stored in agent_configs.config column.
    """
    agent: AgentIdentity
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    services: list[Service] = Field(default_factory=list)
    knowledge_base: KnowledgeBase = Field(default_factory=KnowledgeBase)
    guardrails: Guardrails = Field(default_factory=Guardrails)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    integrations: dict[str, Any] = Field(default_factory=dict)  # STUB
    actions: list[dict[str, Any]] = Field(default_factory=list)  # STUB
    custom_instructions: Optional[str] = None


# =============================================================================
# API REQUEST/RESPONSE SCHEMAS
# =============================================================================

class AgentCreateRequest(BaseModel):
    """Request to create a new agent."""
    config: AgentConfigData
    status: Literal["active", "inactive", "paused"] = "inactive"
    phone: Optional[str] = None


class AgentUpdateRequest(BaseModel):
    """Request to update an agent (partial update)."""
    config: Optional[AgentConfigData] = None
    status: Optional[Literal["active", "inactive", "paused"]] = None
    phone: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent response returned by API."""
    id: int
    user_id: UUID
    config: AgentConfigData
    status: str
    phone: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# STATIC DATA FOR DROPDOWNS
# =============================================================================

# Voice options by provider
AVAILABLE_VOICES: dict[str, list[VoiceOption]] = {
    "inworld": [
        VoiceOption(id="Ashley", name="Ashley", gender="Female",
                    description="American accent, professional tone", provider="inworld"),
        VoiceOption(id="Mark", name="Mark", gender="Male",
                    description="Call center style, clear pronunciation", provider="inworld"),
        VoiceOption(id="Dennis", name="Dennis", gender="Male",
                    description="Supportive and warm tone", provider="inworld"),
        VoiceOption(id="Clive", name="Clive", gender="Male",
                    description="British accent, calm and cordial", provider="inworld"),
        VoiceOption(id="Olivia", name="Olivia", gender="Female",
                    description="British accent, upbeat and friendly", provider="inworld"),
        VoiceOption(id="Timothy", name="Timothy", gender="Male",
                    description="American accent, lively and upbeat", provider="inworld"),
    ],
    "deepgram": [
        VoiceOption(id="aura-asteria-en", name="Asteria", gender="Female",
                    description="Clear and professional", provider="deepgram"),
        VoiceOption(id="aura-luna-en", name="Luna", gender="Female",
                    description="Warm and friendly", provider="deepgram"),
        VoiceOption(id="aura-orion-en", name="Orion", gender="Male",
                    description="Confident and clear", provider="deepgram"),
    ],
}

# Speaking style options
AVAILABLE_SPEAKING_STYLES: list[SpeakingStyleOption] = [
    SpeakingStyleOption(id="calm_professional", name="Calm & Professional",
                        description="Measured pace, business-appropriate"),
    SpeakingStyleOption(id="friendly_casual", name="Friendly & Casual",
                        description="Warm and approachable"),
    SpeakingStyleOption(id="energetic", name="Energetic",
                        description="Upbeat and enthusiastic"),
    SpeakingStyleOption(id="empathetic", name="Empathetic",
                        description="Caring and understanding"),
]

# Default ticket fields
DEFAULT_TICKET_FIELDS: list[TicketField] = [
    TicketField(id="customer_name", label="Customer Name", type="string", enabled=True, required=True),
    TicketField(id="phone_number", label="Phone Number", type="string", enabled=True, required=True),
    TicketField(id="call_summary", label="Call Summary", type="text", enabled=True, required=True),
    TicketField(id="timestamp", label="Timestamp", type="datetime", enabled=True, required=True),
    TicketField(id="priority", label="Priority", type="select",
                options=["low", "medium", "high", "urgent"], enabled=True, required=False),
    TicketField(id="sentiment", label="Sentiment", type="select",
                options=["positive", "neutral", "negative"], enabled=True, required=False),
    TicketField(id="intent", label="Intent", type="select",
                options=["appointment", "inquiry", "complaint", "support", "other"], enabled=True, required=False),
    TicketField(id="action_items", label="Action Items", type="array", enabled=True, required=False),
    TicketField(id="follow_up_required", label="Follow-up Required", type="boolean", enabled=True, required=False),
    TicketField(id="call_duration", label="Call Duration", type="number", enabled=True, required=False),
]

# Suggested custom tags
SUGGESTED_TAGS: list[str] = [
    "new_patient", "insurance_question", "emergency", "callback_requested",
    "vip_customer", "billing_issue", "cancellation", "referral"
]


def get_default_config() -> AgentConfigData:
    """Return a default agent configuration."""
    return AgentConfigData(
        agent=AgentIdentity(
            name="Assistant",
            business_name="My Business",
            greeting_message="Hello! How can I help you today?"
        ),
        voice=VoiceConfig(),
        services=[],
        knowledge_base=KnowledgeBase(),
        guardrails=Guardrails(),
        conversation=ConversationConfig(),
        output=OutputConfig(
            ticket_fields=DEFAULT_TICKET_FIELDS,
            custom_tags=[]
        ),
        integrations={},
        actions=[],
        custom_instructions=None
    )
