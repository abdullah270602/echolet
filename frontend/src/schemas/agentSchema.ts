import { z } from 'zod';
import type { AgentConfig } from '../services/agentApi';

// Schema uses strings since voice and tone options come from backend
export const agentSchema = z.object({
  name: z.string(),
  businessName: z.string().min(1, 'Business name is required'),
  greetingMessage: z.string(),
  voiceId: z.string().min(1, 'Voice is required'),
  tone: z.string().min(1, 'Tone is required'),
  customInstructions: z.string(),
  knowledgeText: z.string(),
});

export type AgentFormData = z.infer<typeof agentSchema>;

// Generate default form values from backend config
export function getDefaultFormValues(config: AgentConfig | null): AgentFormData {
  return {
    name: '',
    businessName: '',
    greetingMessage: config?.default_greeting_message || 'Hello! How can I help you today?',
    voiceId: config?.default_voice_id || '',
    tone: config?.default_tone || '',
    customInstructions: '',
    knowledgeText: '',
  };
}

// Fallback defaults for when config is not yet loaded
export const defaultFormValues: AgentFormData = {
  name: '',
  businessName: '',
  greetingMessage: 'Hello! How can I help you today?',
  voiceId: '',
  tone: '',
  customInstructions: '',
  knowledgeText: '',
};
