import { z } from 'zod';

export const agentSchema = z.object({
  name: z.string(),
  businessName: z.string().min(1, 'Business name is required'),
  greetingMessage: z.string(),
  voiceId: z.enum(['sarah', 'james', 'echo']),
  tone: z.enum(['professional', 'friendly', 'urgent']),
  customInstructions: z.string(),
  knowledgeText: z.string(),
});

export type AgentFormData = z.infer<typeof agentSchema>;

export const defaultFormValues: AgentFormData = {
  name: '',
  businessName: '',
  greetingMessage: '',
  voiceId: 'sarah',
  tone: 'professional',
  customInstructions: '',
  knowledgeText: '',
};
