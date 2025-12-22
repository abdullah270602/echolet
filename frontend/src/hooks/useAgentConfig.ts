import { useState, useEffect } from 'react';
import {
  fetchAgentConfig,
  fetchVoices,
  fetchTones,
  type VoiceOption,
  type ToneOption,
  type AgentConfig,
} from '../services/agentApi';

interface UseAgentConfigReturn {
  config: AgentConfig | null;
  voices: VoiceOption[];
  tones: ToneOption[];
  isLoading: boolean;
  error: string | null;
}

// Default fallback values in case API fails
const DEFAULT_CONFIG: AgentConfig = {
  max_agents_per_user: 3,
  default_voice_id: 'Ashely',
  default_tone: 'professional',
  default_greeting_message: 'Hello! How can I help you today?',
};

const DEFAULT_VOICES: VoiceOption[] = [];
const DEFAULT_TONES: ToneOption[] = [];

export function useAgentConfig(): UseAgentConfigReturn {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [voices, setVoices] = useState<VoiceOption[]>(DEFAULT_VOICES);
  const [tones, setTones] = useState<ToneOption[]>(DEFAULT_TONES);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadConfig() {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch all config in parallel
        const [configData, voicesData, tonesData] = await Promise.all([
          fetchAgentConfig(),
          fetchVoices(),
          fetchTones(),
        ]);

        setConfig(configData);
        setVoices(voicesData);
        setTones(tonesData);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load configuration';
        setError(message);
        // Use defaults on error
        setConfig(DEFAULT_CONFIG);
      } finally {
        setIsLoading(false);
      }
    }

    loadConfig();
  }, []);

  return {
    config,
    voices,
    tones,
    isLoading,
    error,
  };
}
