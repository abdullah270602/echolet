/**
 * Zod schemas for agent configuration form validation.
 *
 * Matches the nested structure of AgentConfigData.
 * Note: No .default() calls are used - all defaults come from getDefaultFormValues()
 * to ensure type consistency between zodResolver and form types.
 */

import { z } from 'zod';

// =============================================================================
// NESTED CONFIG SCHEMAS
// =============================================================================

export const agentIdentitySchema = z.object({
  name: z.string().min(1, 'Agent name is required'),
  business_name: z.string().min(1, 'Business name is required'),
  greeting_message: z.string().min(1, 'Greeting message is required'),
});

export const voiceConfigSchema = z.object({
  provider: z.enum(['inworld', 'deepgram']),
  voice_id: z.string().min(1, 'Voice is required'),
  language: z.string(),
  speaking_style: z.string(),
});

export const serviceSchema = z.object({
  name: z.string().min(1, 'Service name is required'),
  price: z.string().optional(),
  duration_minutes: z.number().positive().optional(),
});

export const knowledgeSourceSchema = z.object({
  type: z.enum(['text', 'website']),
  name: z.string().min(1, 'Source name is required'),
  content: z.string().optional(),
  url: z.string().url('Must be a valid URL').optional(),
}).refine(
  (data) => {
    if (data.type === 'text') return !!data.content;
    if (data.type === 'website') return !!data.url;
    return true;
  },
  { message: 'Content is required for text sources, URL is required for website sources' }
);

export const knowledgeBaseSchema = z.object({
  sources: z.array(knowledgeSourceSchema),
});

export const ticketFieldSchema = z.object({
  id: z.string(),
  label: z.string(),
  type: z.enum(['string', 'text', 'number', 'boolean', 'select', 'array', 'datetime']),
  options: z.array(z.string()).optional(),
  enabled: z.boolean(),
  required: z.boolean(),
});

export const outputConfigSchema = z.object({
  ticket_fields: z.array(ticketFieldSchema),
  custom_tags: z.array(z.string()),
});

export const complianceSchema = z.object({
  hipaa_mode: z.boolean(),
  gdpr_mode: z.boolean(),
  call_recording_disclaimer: z.boolean(),
});

export const guardrailsSchema = z.object({
  allowed_topics: z.array(z.string()),
  disallowed_topics: z.array(z.string()),
  compliance: complianceSchema,
});

export const endCallThresholdSchema = z.object({
  silence_seconds: z.number().min(5).max(60),
  max_retries: z.number().min(1).max(5),
});

export const businessHoursDaySchema = z.object({
  day: z.string(),
  open: z.string().nullable(),
  close: z.string().nullable(),
});

export const businessHoursSchema = z.object({
  enabled: z.boolean(),
  timezone: z.string(),
  schedule: z.array(businessHoursDaySchema),
  after_hours_behavior: z.string(),
});

export const conversationConfigSchema = z.object({
  end_call_threshold: endCallThresholdSchema,
  business_hours: businessHoursSchema,
});

// =============================================================================
// MAIN CONFIG SCHEMA
// =============================================================================

export const agentConfigSchema = z.object({
  agent: agentIdentitySchema,
  voice: voiceConfigSchema,
  services: z.array(serviceSchema),
  knowledge_base: knowledgeBaseSchema,
  guardrails: guardrailsSchema,
  conversation: conversationConfigSchema,
  output: outputConfigSchema,
  integrations: z.record(z.string(), z.unknown()),
  actions: z.array(z.unknown()),
  custom_instructions: z.string().optional(),
});

export type AgentConfigFormData = z.infer<typeof agentConfigSchema>;

// =============================================================================
// DEFAULT VALUES
// =============================================================================

export function getDefaultFormValues(): AgentConfigFormData {
  return {
    agent: {
      name: '',
      business_name: '',
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

// =============================================================================
// LEGACY EXPORTS (for backward compatibility during transition)
// =============================================================================

export const agentSchema = agentConfigSchema;
export type AgentFormData = AgentConfigFormData;
export const defaultFormValues = getDefaultFormValues();
