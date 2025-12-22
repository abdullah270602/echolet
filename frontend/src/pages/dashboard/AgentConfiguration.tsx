import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { AgentCard } from '../../components/dashboard/AgentCard';
import { AgentFormModal } from '../../components/agent-form';
import type { Agent } from '../../types/agent';
import type { AgentFormData } from '../../schemas/agentSchema';

// Mock data for agents with full Agent type
const MOCK_AGENTS: Agent[] = [
  {
    id: '1',
    name: 'Primary Receptionist',
    businessName: 'Acme Corporation',
    status: 'active',
    phone: '+1-555-0100',
    description: 'Handles incoming calls and creates tickets for customer inquiries.',
    voiceId: 'sarah',
    tone: 'professional',
    greetingMessage: 'Hello! Thank you for calling Acme Corporation. How can I assist you today?',
    customInstructions: 'Always confirm the caller\'s name before proceeding. Offer to schedule a callback if wait time exceeds 5 minutes.',
  },
];

export function AgentConfiguration() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | undefined>(undefined);
  const [agents, setAgents] = useState<Agent[]>(MOCK_AGENTS);

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

  const handleSaveAgent = async (data: AgentFormData, files: File[]) => {
    // Mock save - in production this would call an API
    await new Promise((resolve) => setTimeout(resolve, 1000));

    if (editingAgent) {
      // Update existing agent
      setAgents((prev) =>
        prev.map((a) =>
          a.id === editingAgent.id
            ? { ...a, ...data }
            : a
        )
      );
    } else {
      // Create new agent
      const newAgent: Agent = {
        id: Date.now().toString(),
        ...data,
        status: 'inactive',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      setAgents((prev) => [...prev, newAgent]);
    }

    console.log('Saved agent data:', data);
    console.log('Uploaded files:', files);
  };

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
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-purple-500 text-white text-sm font-medium shadow-glow-sm hover:shadow-glow-md transition-shadow"
        >
          <Plus className="w-4 h-4" />
          Create New Agent
        </motion.button>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onEdit={handleEditAgent}
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
    </div>
  );
}
