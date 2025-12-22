import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/clerk-react';
import type { Agent } from '../types/agent';
import type { AgentFormData } from '../schemas/agentSchema';
import {
  fetchAgents,
  createAgent,
  updateAgent,
  deleteAgent,
  ApiError,
} from '../services/agentApi';

interface UseAgentsReturn {
  agents: Agent[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  saveAgent: (data: AgentFormData, agentId?: string) => Promise<Agent>;
  removeAgent: (agentId: string) => Promise<void>;
  isSaving: boolean;
}

export function useAgents(): UseAgentsReturn {
  const { getToken } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchAgents(getToken);
      setAgents(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch agents');
      }
      setAgents([]);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const saveAgent = useCallback(
    async (data: AgentFormData, agentId?: string): Promise<Agent> => {
      setIsSaving(true);
      try {
        // Map frontend form data to backend payload
        const payload = {
          name: data.name,
          business_name: data.businessName,
          voice_id: data.voiceId,
          greeting_message: data.greetingMessage,
          tone: data.tone,
          custom_instructions: data.customInstructions || null,
          knowledge_base_text: data.knowledgeText || null,
        };

        let savedAgent: Agent;

        if (agentId) {
          // Update existing agent
          savedAgent = await updateAgent(agentId, payload, getToken);
          setAgents((prev) =>
            prev.map((a) => (a.id === agentId ? savedAgent : a))
          );
        } else {
          // Create new agent
          savedAgent = await createAgent(payload, getToken);
          setAgents((prev) => [...prev, savedAgent]);
        }

        return savedAgent;
      } finally {
        setIsSaving(false);
      }
    },
    [getToken]
  );

  const removeAgent = useCallback(
    async (agentId: string): Promise<void> => {
      await deleteAgent(agentId, getToken);
      setAgents((prev) => prev.filter((a) => a.id !== agentId));
    },
    [getToken]
  );

  return {
    agents,
    isLoading,
    error,
    refetch: fetchData,
    saveAgent,
    removeAgent,
    isSaving,
  };
}
