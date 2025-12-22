// Agent types - voice and tone are now dynamic from backend
export type AgentStatus = 'active' | 'inactive' | 'paused';

export interface Agent {
  id: string;
  name: string;
  businessName: string;
  description?: string;
  greetingMessage?: string;
  voiceId: string;  // Dynamic from backend
  tone: string;     // Dynamic from backend
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
