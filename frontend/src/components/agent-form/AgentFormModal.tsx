import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button, Tabs, TabsList, TabsTrigger, TabsContent } from '../ui';
import { IdentityForm } from './IdentityForm';
import { BehaviorForm } from './BehaviorForm';
import { KnowledgeForm } from './KnowledgeForm';
import { useAgentForm } from '../../hooks/useAgentForm';
import { useAgentConfig } from '../../hooks/useAgentConfig';
import type { Agent } from '../../types/agent';
import type { AgentFormData } from '../../schemas/agentSchema';

interface AgentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent?: Agent;
  onSave: (data: AgentFormData, files: File[]) => Promise<void>;
}

export function AgentFormModal({
  isOpen,
  onClose,
  agent,
  onSave,
}: AgentFormModalProps) {
  const { config, voices, tones, isLoading: isConfigLoading } = useAgentConfig();

  const {
    form,
    files,
    setFiles,
    tokenCount,
    tokenLimit,
    isSaving,
    setIsSaving,
    resetForm,
    isEditing,
  } = useAgentForm(agent, config);

  const {
    control,
    handleSubmit,
    formState: { errors, isDirty },
  } = form;

  // Reset form when modal opens/closes or agent changes
  useEffect(() => {
    if (isOpen) {
      resetForm();
    }
  }, [isOpen, agent, resetForm]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Prevent body scroll when modal is open
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

  const handleClose = () => {
    if (isDirty && !window.confirm('You have unsaved changes. Are you sure you want to close?')) {
      return;
    }
    onClose();
  };

  const onSubmit = async (data: AgentFormData) => {
    setIsSaving(true);
    try {
      await onSave(data, files);
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
              className="w-full max-w-2xl max-h-[90vh] glass-strong rounded-2xl border border-white/10 flex flex-col pointer-events-auto"
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
              {isConfigLoading ? (
                <div className="flex-1 flex items-center justify-center py-12">
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-6 h-6 text-teal-400 animate-spin" />
                    <p className="text-white/50 text-sm">Loading configuration...</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col flex-1 overflow-hidden">
                  <div className="flex-1 overflow-y-auto px-6 py-6">
                    <Tabs defaultValue="identity">
                      <TabsList className="mb-6 w-full justify-center">
                        <TabsTrigger value="identity">Identity</TabsTrigger>
                        <TabsTrigger value="behavior">Behavior</TabsTrigger>
                        <TabsTrigger value="knowledge">Knowledge</TabsTrigger>
                      </TabsList>

                      <TabsContent value="identity">
                        <IdentityForm control={control} errors={errors} voices={voices} />
                      </TabsContent>

                      <TabsContent value="behavior">
                        <BehaviorForm control={control} errors={errors} tones={tones} />
                      </TabsContent>

                      <TabsContent value="knowledge">
                        <KnowledgeForm
                          control={control}
                          errors={errors}
                          files={files}
                          onFilesChange={setFiles}
                          tokenCount={tokenCount}
                          tokenLimit={tokenLimit}
                        />
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
