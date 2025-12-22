import { useState, useCallback, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { agentSchema, AgentFormData, defaultFormValues } from '../schemas/agentSchema';
import type { Agent } from '../types/agent';

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

export function useAgentForm(agent?: Agent) {
  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: agent ? mapAgentToFormData(agent) : defaultFormValues,
    mode: 'onChange',
  });

  const [files, setFiles] = useState<File[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  // Calculate token count (rough estimate: 4 chars = 1 token)
  const tokenCount = useMemo(() => {
    const values = form.watch();
    const textContent = [
      values.name || '',
      values.businessName || '',
      values.greetingMessage || '',
      values.customInstructions || '',
      values.knowledgeText || '',
    ].join(' ');

    const textTokens = Math.ceil(textContent.length / 4);
    const fileTokens = files.reduce((acc, file) => acc + Math.ceil(file.size / 4), 0);

    return textTokens + fileTokens;
  }, [form.watch(), files]);

  const handleFilesChange = useCallback((newFiles: File[]) => {
    setFiles(newFiles);
  }, []);

  const resetForm = useCallback(() => {
    form.reset(agent ? mapAgentToFormData(agent) : defaultFormValues);
    setFiles([]);
  }, [form, agent]);

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
