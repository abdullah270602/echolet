/**
 * Agent API Service
 *
 * Handles all API communication for agent configurations.
 * Updated to work with nested JSONB config structure.
 */

import type {
  Agent,
  AgentConfigData,
  AgentStatus,
  VoiceOption,
  SpeakingStyleOption,
  TicketField,
} from '../types/agent';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

interface AgentApiResponse {
  id: number;
  user_id: string;
  config: AgentConfigData;
  status: string;
  phone: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// =============================================================================
// REQUEST TYPES
// =============================================================================

interface CreateAgentRequest {
  config: AgentConfigData;
  status?: AgentStatus;
  phone?: string;
}

interface UpdateAgentRequest {
  config?: AgentConfigData;
  status?: AgentStatus;
  phone?: string;
}

// =============================================================================
// API ERROR CLASS
// =============================================================================

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

// =============================================================================
// API HELPERS
// =============================================================================

function mapApiResponseToAgent(response: AgentApiResponse): Agent {
  return {
    id: response.id,
    user_id: response.user_id,
    config: response.config,
    status: response.status as AgentStatus,
    phone: response.phone || undefined,
    created_at: response.created_at || undefined,
    updated_at: response.updated_at || undefined,
  };
}

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

async function publicApiRequest<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new ApiError('Request failed', response.status);
  }
  return response.json();
}

// =============================================================================
// CONFIGURATION ENDPOINTS (No auth required)
// =============================================================================

/**
 * Get default agent configuration template.
 */
export async function fetchDefaultConfig(): Promise<AgentConfigData> {
  return publicApiRequest<AgentConfigData>('/defaults');
}

/**
 * Get list of available voice options.
 * Optionally filter by provider.
 */
export async function fetchVoices(provider?: string): Promise<VoiceOption[]> {
  const endpoint = provider ? `/voices?provider=${provider}` : '/voices';
  return publicApiRequest<VoiceOption[]>(endpoint);
}

/**
 * Get voice options for a specific provider.
 */
export async function fetchVoicesByProvider(provider: string): Promise<VoiceOption[]> {
  return publicApiRequest<VoiceOption[]>(`/voices/${provider}`);
}

/**
 * Get list of available speaking styles.
 */
export async function fetchSpeakingStyles(): Promise<SpeakingStyleOption[]> {
  return publicApiRequest<SpeakingStyleOption[]>('/speaking-styles');
}

/**
 * Get list of default ticket/output fields.
 */
export async function fetchOutputFields(): Promise<TicketField[]> {
  return publicApiRequest<TicketField[]>('/output-fields');
}

/**
 * Get list of suggested custom tags.
 */
export async function fetchSuggestedTags(): Promise<string[]> {
  return publicApiRequest<string[]>('/suggested-tags');
}

// =============================================================================
// AGENT CRUD ENDPOINTS (Auth required)
// =============================================================================

/**
 * Fetch all agents for the current user.
 */
export async function fetchAgents(
  getToken: () => Promise<string | null>
): Promise<Agent[]> {
  const data = await apiRequest<AgentApiResponse[]>('/agents', getToken);
  return data.map(mapApiResponseToAgent);
}

/**
 * Fetch a single agent by ID.
 */
export async function fetchAgent(
  agentId: number,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  const data = await apiRequest<AgentApiResponse>(
    `/agents/${agentId}`,
    getToken
  );
  return mapApiResponseToAgent(data);
}

/**
 * Create a new agent.
 */
export async function createAgent(
  config: AgentConfigData,
  getToken: () => Promise<string | null>,
  options?: { status?: AgentStatus; phone?: string }
): Promise<Agent> {
  const payload: CreateAgentRequest = {
    config,
    status: options?.status || 'inactive',
    phone: options?.phone,
  };

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

/**
 * Update an existing agent.
 * Supports partial updates.
 */
export async function updateAgent(
  agentId: number,
  updates: UpdateAgentRequest,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  const data = await apiRequest<AgentApiResponse>(
    `/agents/${agentId}`,
    getToken,
    {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }
  );
  return mapApiResponseToAgent(data);
}

/**
 * Update only the agent configuration.
 */
export async function updateAgentConfig(
  agentId: number,
  config: AgentConfigData,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  return updateAgent(agentId, { config }, getToken);
}

/**
 * Update only the agent status.
 */
export async function updateAgentStatus(
  agentId: number,
  status: AgentStatus,
  getToken: () => Promise<string | null>
): Promise<Agent> {
  return updateAgent(agentId, { status }, getToken);
}

/**
 * Delete an agent (soft delete).
 */
export async function deleteAgent(
  agentId: number,
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
