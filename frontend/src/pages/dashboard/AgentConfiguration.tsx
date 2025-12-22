import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Loader2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { AgentCard } from '../../components/dashboard/AgentCard';
import { AgentFormModal } from '../../components/agent-form';
import { ConfirmDialog } from '../../components/ui';
import { useAgents } from '../../hooks/useAgents';
import { useAgentConfig } from '../../hooks/useAgentConfig';
import { ApiError } from '../../services/agentApi';
import type { Agent } from '../../types/agent';
import type { AgentFormData } from '../../schemas/agentSchema';

export function AgentConfiguration() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | undefined>(undefined);
  const [deletingAgent, setDeletingAgent] = useState<Agent | undefined>(undefined);
  const [isDeleting, setIsDeleting] = useState(false);
  const { agents, isLoading, error, saveAgent, removeAgent, refetch } = useAgents();
  const { config } = useAgentConfig();

  // Get agent limit from config (default to 3 if not loaded yet)
  const maxAgents = config?.max_agents_per_user ?? 3;

  const handleCreateNew = () => {
    setEditingAgent(undefined);
    setIsModalOpen(true);
  };

  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingAgent(undefined);
  };

  const handleSaveAgent = async (data: AgentFormData, _files: File[]) => {
    try {
      await saveAgent(data, editingAgent?.id);
      // Toast is handled in AgentFormModal
    } catch (err) {
      if (err instanceof ApiError) {
        throw new Error(err.detail || err.message);
      }
      throw err;
    }
  };

  const handleDeleteAgent = (agent: Agent) => {
    setDeletingAgent(agent);
  };

  const handleConfirmDelete = async () => {
    if (!deletingAgent) return;

    setIsDeleting(true);
    try {
      await removeAgent(deletingAgent.id);
      toast.success('Agent deleted successfully');
      setDeletingAgent(undefined);
    } catch (err) {
      const message = err instanceof ApiError
        ? (err.detail || err.message)
        : 'Failed to delete agent';
      toast.error(message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setDeletingAgent(undefined);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-teal-400 animate-spin" />
          <p className="text-white/50 text-sm">Loading agents...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <div className="p-3 rounded-full bg-red-500/10">
            <AlertCircle className="w-8 h-8 text-red-400" />
          </div>
          <div>
            <p className="text-white font-medium mb-1">Failed to load agents</p>
            <p className="text-white/50 text-sm mb-4">{error}</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => refetch()}
            className="px-4 py-2 rounded-lg bg-white/5 text-white/70 text-sm font-medium border border-white/10 hover:bg-white/10 transition-all"
          >
            Try Again
          </motion.button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="text-white/60 text-sm">
            Manage your voice agents and their configurations.
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCreateNew}
          disabled={agents.length >= maxAgents}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-purple-500 text-white text-sm font-medium shadow-glow-sm hover:shadow-glow-md transition-shadow disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-glow-sm"
        >
          <Plus className="w-4 h-4" />
          Create New Agent
        </motion.button>
      </div>

      {/* Agent limit notice */}
      {agents.length >= maxAgents && (
        <div className="mb-6 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <p className="text-amber-400 text-sm">
            You have reached the maximum limit of {maxAgents} agent{maxAgents !== 1 ? 's' : ''}. Edit your existing agents or contact support for more.
          </p>
        </div>
      )}

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onEdit={handleEditAgent}
            onDelete={handleDeleteAgent}
          />
        ))}
      </div>

      {/* Empty State */}
      {agents.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 p-8 rounded-xl border border-dashed border-white/20 text-center"
        >
          <p className="text-white/40 text-sm mb-4">
            No agents configured yet.
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleCreateNew}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 text-white/70 text-sm font-medium border border-white/10 hover:bg-white/10 transition-all"
          >
            <Plus className="w-4 h-4" />
            Create your first agent
          </motion.button>
        </motion.div>
      )}

      {/* Agent Form Modal */}
      <AgentFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        agent={editingAgent}
        onSave={handleSaveAgent}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!deletingAgent}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Agent"
        message={`Are you sure you want to delete "${deletingAgent?.name || 'this agent'}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        isLoading={isDeleting}
        variant="danger"
      />
    </div>
  );
}
