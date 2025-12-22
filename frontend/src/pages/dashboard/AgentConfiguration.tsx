import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { AgentCard } from '../../components/dashboard/AgentCard';

// Mock data for agents
const MOCK_AGENTS = [
  {
    id: '1',
    name: 'Primary Receptionist',
    status: 'active' as const,
    phone: '+1-555-0100',
    description: 'Handles incoming calls and creates tickets for customer inquiries.',
  },
];

export function AgentConfiguration() {
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
          disabled
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 text-white/40 text-sm font-medium cursor-not-allowed border border-white/10"
          title="Coming Soon"
        >
          <Plus className="w-4 h-4" />
          Create New Agent
        </motion.button>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MOCK_AGENTS.map((agent) => (
          <AgentCard
            key={agent.id}
            name={agent.name}
            status={agent.status}
            phone={agent.phone}
            description={agent.description}
          />
        ))}
      </div>

      {/* Empty State Info */}
      {MOCK_AGENTS.length === 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 p-6 rounded-xl border border-dashed border-white/20 text-center"
        >
          <p className="text-white/40 text-sm">
            Agent configuration management is coming soon.
            <br />
            You'll be able to create and customize multiple agents.
          </p>
        </motion.div>
      )}
    </div>
  );
}
