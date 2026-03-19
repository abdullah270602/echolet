/**
 * Agent Form Modal - 8-tab configuration form
 *
 * Tabs:
 * 1. Agent Setup - Identity and custom instructions
 * 2. Voice - Provider, voice, and speaking style
 * 3. Services - Services list
 * 4. Knowledge - Knowledge base sources
 * 5. Integrations - STUB
 * 6. Actions - STUB
 * 7. Output - Ticket fields and tags
 * 8. Guardrails - Topics, compliance, hours
 */

import { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { Button, Tabs, TabsList, TabsTrigger, TabsContent } from '../ui';
import { AgentSetupForm } from './AgentSetupForm';
import { VoiceForm } from './VoiceForm';
import { ServicesForm } from './ServicesForm';
import { KnowledgeBaseForm } from './KnowledgeBaseForm';
import { IntegrationsForm } from './IntegrationsForm';
import { ActionsForm } from './ActionsForm';
import { TicketOutputForm } from './TicketOutputForm';
import { GuardrailsForm } from './GuardrailsForm';
import { agentConfigSchema, getDefaultFormValues, type AgentConfigFormData } from '../../schemas/agentSchema';
import type { Agent, VoiceOption, SpeakingStyleOption, TicketField } from '../../types/agent';
import {
  fetchVoices,
  fetchSpeakingStyles,
  fetchOutputFields,
  fetchSuggestedTags,
} from '../../services/agentApi';

interface AgentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent?: Agent;
  onSave: (config: AgentConfigFormData) => Promise<void>;
}

export function AgentFormModal({
  isOpen,
  onClose,
  agent,
  onSave,
}: AgentFormModalProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [speakingStyles, setSpeakingStyles] = useState<SpeakingStyleOption[]>([]);
  const [defaultOutputFields, setDefaultOutputFields] = useState<TicketField[]>([]);
  const [suggestedTags, setSuggestedTags] = useState<string[]>([]);

  const isEditing = !!agent;

  const form = useForm<AgentConfigFormData>({
    resolver: zodResolver(agentConfigSchema),
    defaultValues: agent?.config || getDefaultFormValues(),
  });

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = form;

  // Load configuration options
  useEffect(() => {
    async function loadConfig() {
      setIsLoadingConfig(true);
      try {
        const [voicesData, stylesData, fieldsData, tagsData] = await Promise.all([
          fetchVoices(),
          fetchSpeakingStyles(),
          fetchOutputFields(),
          fetchSuggestedTags(),
        ]);
        setVoices(voicesData);
        setSpeakingStyles(stylesData);
        setDefaultOutputFields(fieldsData);
        setSuggestedTags(tagsData);
      } catch (error) {
        console.error('Failed to load config:', error);
        toast.error('Failed to load configuration options');
      } finally {
        setIsLoadingConfig(false);
      }
    }
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  // Reset form when modal opens or agent changes
  useEffect(() => {
    if (isOpen) {
      reset(agent?.config || getDefaultFormValues());
    }
  }, [isOpen, agent, reset]);

  const handleClose = useCallback(() => {
    if (isDirty && !window.confirm('You have unsaved changes. Are you sure you want to close?')) {
      return;
    }
    onClose();
  }, [isDirty, onClose]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, handleClose]);

  // Prevent body scroll
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const onSubmit = async (data: AgentConfigFormData) => {
    setIsSaving(true);
    try {
      await onSave(data);
      toast.success(isEditing ? 'Agent updated successfully!' : 'Agent created successfully!');
      onClose();
    } catch (error) {
      toast.error('Failed to save agent. Please try again.');
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={handleClose}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div
              className="w-full max-w-3xl max-h-[90vh] glass-strong rounded-2xl border border-white/10 flex flex-col pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
                <h2 className="text-xl font-semibold text-white">
                  {isEditing ? 'Edit Agent' : 'Create Agent'}
                </h2>
                <button
                  type="button"
                  onClick={handleClose}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5 text-white/50 hover:text-white" />
                </button>
              </div>

              {/* Content */}
              {isLoadingConfig ? (
                <div className="flex-1 flex items-center justify-center py-12">
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-6 h-6 text-teal-400 animate-spin" />
                    <p className="text-white/50 text-sm">Loading configuration...</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col flex-1 overflow-hidden">
                  <div className="flex-1 overflow-y-auto px-6 py-6">
                    <Tabs defaultValue="setup">
                      <TabsList className="mb-6 w-full flex-wrap justify-center gap-1">
                        <TabsTrigger value="setup">Setup</TabsTrigger>
                        <TabsTrigger value="voice">Voice</TabsTrigger>
                        <TabsTrigger value="services">Services</TabsTrigger>
                        <TabsTrigger value="knowledge">Knowledge</TabsTrigger>
                        <TabsTrigger value="integrations">Integrations</TabsTrigger>
                        <TabsTrigger value="actions">Actions</TabsTrigger>
                        <TabsTrigger value="output">Output</TabsTrigger>
                        <TabsTrigger value="guardrails">Guardrails</TabsTrigger>
                      </TabsList>

                      <TabsContent value="setup">
                        <AgentSetupForm control={control} errors={errors} />
                      </TabsContent>

                      <TabsContent value="voice">
                        <VoiceForm
                          control={control}
                          errors={errors}
                          voices={voices}
                          speakingStyles={speakingStyles}
                        />
                      </TabsContent>

                      <TabsContent value="services">
                        <ServicesForm control={control} errors={errors} />
                      </TabsContent>

                      <TabsContent value="knowledge">
                        <KnowledgeBaseForm control={control} errors={errors} />
                      </TabsContent>

                      <TabsContent value="integrations">
                        <IntegrationsForm />
                      </TabsContent>

                      <TabsContent value="actions">
                        <ActionsForm />
                      </TabsContent>

                      <TabsContent value="output">
                        <TicketOutputForm
                          control={control}
                          errors={errors}
                          defaultFields={defaultOutputFields}
                          suggestedTags={suggestedTags}
                        />
                      </TabsContent>

                      <TabsContent value="guardrails">
                        <GuardrailsForm control={control} errors={errors} />
                      </TabsContent>
                    </Tabs>
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/10">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={handleClose}
                      disabled={isSaving}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="glow"
                      disabled={isSaving}
                      className="min-w-[140px]"
                    >
                      {isSaving ? (
                        <span className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Saving...
                        </span>
                      ) : (
                        'Save Changes'
                      )}
                    </Button>
                  </div>
                </form>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
