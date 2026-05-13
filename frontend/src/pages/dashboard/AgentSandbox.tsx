import { useState, useEffect } from 'react';
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
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
          <p className="text-muted text-sm">Loading agents...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
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

  // No agents state
  if (agents.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
        <div className="flex flex-col items-center gap-4 max-w-md text-center border-2 border-ink bg-white p-8">
          <div className="p-3 bg-paper border border-rule">
            <AlertCircle className="w-8 h-8 text-accent" />
          </div>
          <div>
            <p className="font-display text-lg font-semibold text-ink mb-1">No agents configured</p>
            <p className="text-muted text-sm">
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
        <label className="block text-sm font-semibold text-ink mb-2">
          Select Agent
        </label>
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between px-4 py-3 bg-white border-2 border-ink text-ink hover:bg-paper/50 transition-colors"
          >
            <div className="text-left">
              <span className="block font-medium">{selectedAgent?.config.agent.name || 'Select an agent'}</span>
              {selectedAgent && (
                <span className="block text-sm text-muted">{selectedAgent.config.agent.business_name}</span>
              )}
            </div>
            <ChevronDown
              className={`w-5 h-5 text-muted transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {isDropdownOpen && (
            <div
              className="absolute z-10 w-full mt-2 py-1 bg-white border-2 border-ink max-h-60 overflow-y-auto"
            >
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => {
                    setSelectedAgent(agent);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-paper transition-colors ${
                    selectedAgent?.id === agent.id ? 'bg-paper' : ''
                  }`}
                >
                  <div className="font-semibold text-ink">{agent.config.agent.name}</div>
                  <div className="text-sm text-muted">{agent.config.agent.business_name}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Voice Room */}
      {selectedAgent && <VoiceRoom agentId={selectedAgent.id} />}
    </div>
  );
}
