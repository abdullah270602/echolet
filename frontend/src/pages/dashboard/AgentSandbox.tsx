import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, AlertCircle, ChevronDown } from 'lucide-react';
import { VoiceRoom } from '../../components/VoiceRoom';
import { useAgents } from '../../hooks/useAgents';
import type { Agent } from '../../types/agent';

export function AgentSandbox() {
  const { agents, isLoading, error, refetch } = useAgents();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Auto-select first agent when loaded
  useEffect(() => {
    if (agents.length > 0 && !selectedAgent) {
      setSelectedAgent(agents[0]);
    }
  }, [agents, selectedAgent]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
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
      <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
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

  // No agents state
  if (agents.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <div className="p-3 rounded-full bg-amber-500/10">
            <AlertCircle className="w-8 h-8 text-amber-400" />
          </div>
          <div>
            <p className="text-white font-medium mb-1">No agents configured</p>
            <p className="text-white/50 text-sm">
              Create an agent in the Agent Configuration page first to start testing.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-6 min-h-[calc(100vh-8rem)] py-8">
      {/* Agent Selector */}
      <div className="w-full max-w-lg">
        <label className="block text-sm font-medium text-white/70 mb-2">
          Select Agent
        </label>
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all"
          >
            <div className="text-left">
              <span className="block">{selectedAgent?.name || 'Select an agent'}</span>
              {selectedAgent && (
                <span className="block text-sm text-white/50">{selectedAgent.businessName}</span>
              )}
            </div>
            <ChevronDown
              className={`w-5 h-5 text-white/50 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {isDropdownOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute z-10 w-full mt-2 py-2 rounded-xl bg-gray-900 border border-white/10 shadow-xl max-h-60 overflow-y-auto"
            >
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => {
                    setSelectedAgent(agent);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-white/5 transition-all ${
                    selectedAgent?.id === agent.id ? 'bg-white/10' : ''
                  }`}
                >
                  <div className="font-medium text-white">{agent.name}</div>
                  <div className="text-sm text-white/50">{agent.businessName}</div>
                </button>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      {/* Voice Room */}
      {selectedAgent && <VoiceRoom agentId={parseInt(selectedAgent.id)} />}
    </div>
  );
}
