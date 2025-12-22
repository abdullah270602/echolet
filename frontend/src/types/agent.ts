export type VoiceId = 'sarah' | 'james' | 'echo';
export type Tone = 'professional' | 'friendly' | 'urgent';
export type AgentStatus = 'active' | 'inactive' | 'paused';

export interface Agent {
  id: string;
  name: string;
  businessName: string;
  description?: string;
  greetingMessage?: string;
  voiceId: VoiceId;
  tone: Tone;
  customInstructions?: string;
  knowledgeText?: string;
  knowledgeFiles?: KnowledgeFile[];
  tokenCount?: number;
  status: AgentStatus;
  phone?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface KnowledgeFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt?: string;
}

export const VOICE_OPTIONS: { value: VoiceId; label: string }[] = [
  { value: 'sarah', label: 'Sarah (American)' },
  { value: 'james', label: 'James (British)' },
  { value: 'echo', label: 'Echo (Neutral)' },
];

export const TONE_OPTIONS: { value: Tone; label: string; description: string }[] = [
  { value: 'professional', label: 'Professional', description: 'Formal and business-like' },
  { value: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
  { value: 'urgent', label: 'Urgent', description: 'Direct and action-oriented' },
];
