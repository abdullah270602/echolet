import { useState } from 'react';
import { Plus, Loader2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { AgentCard } from '../../components/dashboard/AgentCard';
import { AgentFormModal } from '../../components/agent-form';
import { ConfirmDialog } from '../../components/ui';
import { useAgents } from '../../hooks/useAgents';
import { ApiError } from '../../services/agentApi';
import type { Agent, AgentConfigData } from '../../types/agent';

// Max agents per user (could come from backend config in the future)
const MAX_AGENTS: number = 3;

export function AgentConfiguration() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | undefined>(undefined);
  const [deletingAgent, setDeletingAgent] = useState<Agent | undefined>(undefined);
  const [isDeleting, setIsDeleting] = useState(false);
  const { agents, isLoading, error, saveAgent, removeAgent, refetch } = useAgents();

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

  const handleSaveAgent = async (config: AgentConfigData) => {
    try {
      await saveAgent(config, editingAgent?.id);
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
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
          <p className="text-muted text-sm">Loading agents...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 max-w-md text-center border-2 border-ink bg-white p-8">
          <div className="p-3 bg-red-50 border border-red-200">
            <AlertCircle className="w-8 h-8 text-red-700" />
          </div>
          <div>
            <p className="font-display text-lg font-semibold text-ink mb-1">Failed to load agents</p>
            <p className="text-muted text-sm mb-4">{error}</p>
          </div>
          <button
            onClick={() => refetch()}
            className="min-h-11 px-6 border-2 border-ink bg-white text-ink text-sm font-medium hover:bg-ink hover:text-paper transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-muted text-sm">
            Manage your voice agents and their configurations.
          </p>
        </div>
        <button
          onClick={handleCreateNew}
          disabled={agents.length >= MAX_AGENTS}
          className="flex items-center gap-2 min-h-11 px-5 bg-accent text-white text-sm font-semibold hover:bg-accent-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-4 h-4" />
          Create New Agent
        </button>
      </div>

      {/* Agent limit notice */}
      {agents.length >= MAX_AGENTS && (
        <div className="mb-6 p-4 bg-white border-2 border-ink">
          <p className="text-ink text-sm">
            You have reached the maximum limit of {MAX_AGENTS} agent{MAX_AGENTS !== 1 ? 's' : ''}. Edit your existing agents or contact support for more.
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
        <div className="mt-8 p-8 border-2 border-ink bg-white text-center">
          <p className="text-muted text-sm mb-4">
            No agents configured yet.
          </p>
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center gap-2 min-h-11 px-5 bg-accent text-white text-sm font-semibold hover:bg-accent-dark transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create your first agent
          </button>
        </div>
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
        message={`Are you sure you want to delete "${deletingAgent?.config?.agent?.name || 'this agent'}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        isLoading={isDeleting}
        variant="danger"
      />
    </div>
  );
}
