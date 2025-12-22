import { useState, useCallback, useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { agentSchema, AgentFormData, getDefaultFormValues } from '../schemas/agentSchema';
import type { Agent } from '../types/agent';
import type { AgentConfig } from '../services/agentApi';

const TOKEN_LIMIT = 20000;

function mapAgentToFormData(agent: Agent): AgentFormData {
  return {
    name: agent.name || '',
    businessName: agent.businessName,
    greetingMessage: agent.greetingMessage || '',
    voiceId: agent.voiceId,
    tone: agent.tone,
    customInstructions: agent.customInstructions || '',
    knowledgeText: agent.knowledgeText || '',
  };
}

export function useAgentForm(agent?: Agent, config?: AgentConfig | null) {
  // Memoize default values to prevent unnecessary re-renders
  const defaultValues = useMemo(
    () => getDefaultFormValues(config ?? null),
    [config]
  );

  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: agent ? mapAgentToFormData(agent) : defaultValues,
    mode: 'onChange',
  });

  const [files, setFiles] = useState<File[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  // Watch form values reactively using useWatch
  const watchedValues = useWatch({ control: form.control });

  // Calculate token count (rough estimate: 4 chars = 1 token)
  const tokenCount = useMemo(() => {
    const textContent = [
      watchedValues.name || '',
      watchedValues.businessName || '',
      watchedValues.greetingMessage || '',
      watchedValues.customInstructions || '',
      watchedValues.knowledgeText || '',
    ].join(' ');

    const textTokens = Math.ceil(textContent.length / 4);
    const fileTokens = files.reduce((acc, file) => acc + Math.ceil(file.size / 4), 0);

    return textTokens + fileTokens;
  }, [watchedValues, files]);

  const handleFilesChange = useCallback((newFiles: File[]) => {
    setFiles(newFiles);
  }, []);

  const resetForm = useCallback(() => {
    form.reset(agent ? mapAgentToFormData(agent) : defaultValues);
    setFiles([]);
  }, [form, agent, defaultValues]);

  return {
    form,
    files,
    setFiles: handleFilesChange,
    tokenCount,
    tokenLimit: TOKEN_LIMIT,
    isSaving,
    setIsSaving,
    resetForm,
    isEditing: !!agent,
  };
}
