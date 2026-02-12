/**
 * Agent configuration types matching backend Pydantic schemas.
 *
 * The config is stored as a single JSONB column with this nested structure.
 */

// =============================================================================
// STATUS TYPE
// =============================================================================

export type AgentStatus = 'active' | 'inactive' | 'paused';

// =============================================================================
// NESTED CONFIG TYPES
// =============================================================================

export interface AgentIdentity {
  name: string;
  business_name: string;
  greeting_message: string;
}

export type VoiceProvider = 'inworld' | 'deepgram';

export interface VoiceConfig {
  provider: VoiceProvider;
  voice_id: string;
  language: string;
  speaking_style: string;
}

export interface Service {
  name: string;
  price?: string;
  duration_minutes?: number;
}

export type KnowledgeSourceType = 'text' | 'website';

export interface KnowledgeSource {
  type: KnowledgeSourceType;
  name: string;
  content?: string; // For text type
  url?: string;     // For website type
}

export interface KnowledgeBase {
  sources: KnowledgeSource[];
}

export type TicketFieldType = 'string' | 'text' | 'number' | 'boolean' | 'select' | 'array' | 'datetime';

export interface TicketField {
  id: string;
  label: string;
  type: TicketFieldType;
  options?: string[]; // For select type
  enabled: boolean;
  required: boolean;
}

export interface OutputConfig {
  ticket_fields: TicketField[];
  custom_tags: string[];
}

export interface Compliance {
  hipaa_mode: boolean;
  gdpr_mode: boolean;
  call_recording_disclaimer: boolean;
}

export interface Guardrails {
  allowed_topics: string[];
  disallowed_topics: string[];
  compliance: Compliance;
}

export interface EndCallThreshold {
  silence_seconds: number;
  max_retries: number;
}

export interface BusinessHoursDay {
  day: string;
  open: string | null;
  close: string | null;
}

export interface BusinessHours {
  enabled: boolean;
  timezone: string;
  schedule: BusinessHoursDay[];
  after_hours_behavior: string;
}

export interface ConversationConfig {
  end_call_threshold: EndCallThreshold;
  business_hours: BusinessHours;
}

// =============================================================================
// MAIN CONFIG TYPE
// =============================================================================

export interface AgentConfigData {
  agent: AgentIdentity;
  voice: VoiceConfig;
  services: Service[];
  knowledge_base: KnowledgeBase;
  guardrails: Guardrails;
  conversation: ConversationConfig;
  output: OutputConfig;
  integrations: Record<string, unknown>; // STUB
  actions: unknown[];                     // STUB
  custom_instructions?: string;
}

// =============================================================================
// AGENT RESPONSE TYPE
// =============================================================================

export interface Agent {
  id: number;
  user_id: string;
  config: AgentConfigData;
  status: AgentStatus;
  phone?: string;
  created_at?: string;
  updated_at?: string;
}

// =============================================================================
// DROPDOWN OPTIONS (from backend)
// =============================================================================

export interface VoiceOption {
  id: string;
  name: string;
  gender: string;
  description: string;
  provider: VoiceProvider;
}

export interface SpeakingStyleOption {
  id: string;
  name: string;
  description: string;
}

// =============================================================================
// DEFAULT CONFIG HELPER
// =============================================================================

export function getDefaultConfig(): AgentConfigData {
  return {
    agent: {
      name: 'Assistant',
      business_name: 'My Business',
      greeting_message: 'Hello! How can I help you today?',
    },
    voice: {
      provider: 'inworld',
      voice_id: 'Ashley',
      language: 'en-US',
      speaking_style: 'calm_professional',
    },
    services: [],
    knowledge_base: {
      sources: [],
    },
    guardrails: {
      allowed_topics: [],
      disallowed_topics: [],
      compliance: {
        hipaa_mode: false,
        gdpr_mode: false,
        call_recording_disclaimer: true,
      },
    },
    conversation: {
      end_call_threshold: {
        silence_seconds: 20,
        max_retries: 2,
      },
      business_hours: {
        enabled: false,
        timezone: 'America/New_York',
        schedule: [],
        after_hours_behavior: 'offer_callback',
      },
    },
    output: {
      ticket_fields: [],
      custom_tags: [],
    },
    integrations: {},
    actions: [],
    custom_instructions: undefined,
  };
}
