import type { Agent } from '../types/agent';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Backend API response types
interface AgentApiResponse {
  id: number;
  user_id: string;
  name: string;
  business_name: string;
  voice_id: string;
  greeting_message: string;
  tone: string;
  custom_instructions: string | null;
  knowledge_base_text: string | null;
  max_duration_seconds: number;
  status: string;
  phone: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// Voice option from API
export interface VoiceOption {
  id: string;
  name: string;
  gender: string;
  description: string;
}

// Tone option from API
export interface ToneOption {
  id: string;
  name: string;
  description: string;
}

// Agent config from API
export interface AgentConfig {
  max_agents_per_user: number;
  default_voice_id: string;
  default_tone: string;
  default_greeting_message: string;
}

// Create request payload
interface CreateAgentPayload {
  name: string;
  business_name: string;
  voice_id?: string;
  greeting_message?: string;
  tone?: string;
  custom_instructions?: string | null;
  knowledge_base_text?: string | null;
  max_duration_seconds?: number;
}

// Update request payload (all optional)
interface UpdateAgentPayload {
  name?: string;
  business_name?: string;
  voice_id?: string;
  greeting_message?: string;
  tone?: string;
  custom_instructions?: string | null;
  knowledge_base_text?: string | null;
  max_duration_seconds?: number;
  status?: string;
}

// Map backend response to frontend Agent type
function mapApiResponseToAgent(response: AgentApiResponse): Agent {
  return {
    id: response.id.toString(),
    name: response.name,
    businessName: response.business_name,
    description: response.custom_instructions?.slice(0, 100) || undefined,
    greetingMessage: response.greeting_message,
    voiceId: response.voice_id,
    tone: response.tone,
    customInstructions: response.custom_instructions || undefined,
    knowledgeText: response.knowledge_base_text || undefined,
    status: response.status as 'active' | 'inactive' | 'paused',
    phone: response.phone || undefined,
    createdAt: response.created_at || undefined,
    updatedAt: response.updated_at || undefined,
  };
}

// Generic API error
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Helper to make authenticated API requests
async function apiRequest<T>(
  endpoint: string,
  getToken: () => Promise<string | null>,
  options: RequestInit = {}
): Promise<T> {
  const token = await getToken();
  if (!token) {
    throw new ApiError('Not authenticated', 401);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const errorData = await response.json();
      detail = errorData.detail;
    } catch {
      // Ignore JSON parse errors
    }

    if (response.status === 401) {
      throw new ApiError('Authentication failed', 401, detail);
    }
    if (response.status === 403) {
      throw new ApiError('Not authorized', 403, detail);
    }
    if (response.status === 404) {
      throw new ApiError('Not found', 404, detail);
    }
    if (response.status === 400) {
      throw new ApiError(detail || 'Bad request', 400, detail);
    }

    throw new ApiError(detail || 'Request failed', response.status, detail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Fetch agent configuration (no auth required)
export async function fetchAgentConfig(): Promise<AgentConfig> {
  const response = await fetch(`${API_BASE_URL}/config`);
  if (!response.ok) {
    throw new ApiError('Failed to fetch config', response.status);
  }
  return response.json();
}

// Fetch available voices (no auth required)
export async function fetchVoices(): Promise<VoiceOption[]> {
  const response = await fetch(`${API_BASE_URL}/voices`);
  if (!response.ok) {
    throw new ApiError('Failed to fetch voices', response.status);
  }
  return response.json();
}

// Fetch available tones (no auth required)
export async function fetchTones(): Promise<ToneOption[]> {
  const response = await fetch(`${API_BASE_URL}/tones`);
  if (!response.ok) {
    throw new ApiError('Failed to fetch tones', response.status);
  }
  return response.json();
}

// Fetch all agents for current user
export async function fetchAgents(
  getToken: () => Promise<string | null>
): Promise<Agent[]> {
  const data = await apiRequest<AgentApiResponse[]>(
    '/agents',
    getToken
  );
  return data.map(mapApiResponseToAgent);
}

// Fetch single agent by ID
export async function fetchAgent(
  agentId: string,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  const data = await apiRequest<AgentApiResponse>(
    `/agents/${agentId}`,
    getToken
  );
  return mapApiResponseToAgent(data);
}

// Create a new agent
export async function createAgent(
  payload: CreateAgentPayload,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  const data = await apiRequest<AgentApiResponse>(
    '/agents',
    getToken,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
  return mapApiResponseToAgent(data);
}

// Update an existing agent
export async function updateAgent(
  agentId: string,
  payload: UpdateAgentPayload,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  const data = await apiRequest<AgentApiResponse>(
    `/agents/${agentId}`,
    getToken,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );
  return mapApiResponseToAgent(data);
}

// Delete an agent
export async function deleteAgent(
  agentId: string,
  getToken: () => Promise<string | null>
): Promise<void> {
  await apiRequest<void>(
    `/agents/${agentId}`,
    getToken,
    {
      method: 'DELETE',
    }
  );
}
