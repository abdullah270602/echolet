import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/clerk-react';
import type { Agent, AgentConfigData } from '../types/agent';
import {
  fetchAgents,
  createAgent,
  updateAgentConfig,
  deleteAgent,
  ApiError,
} from '../services/agentApi';

interface UseAgentsReturn {
  agents: Agent[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  saveAgent: (config: AgentConfigData, agentId?: number) => Promise<Agent>;
  removeAgent: (agentId: number) => Promise<void>;
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
    async (config: AgentConfigData, agentId?: number): Promise<Agent> => {
      setIsSaving(true);
      try {
        let savedAgent: Agent;

        if (agentId) {
          // Update existing agent
          savedAgent = await updateAgentConfig(agentId, config, getToken);
          setAgents((prev) =>
            prev.map((a) => (a.id === agentId ? savedAgent : a))
          );
        } else {
          // Create new agent
          savedAgent = await createAgent(config, getToken);
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
    async (agentId: number): Promise<void> => {
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
