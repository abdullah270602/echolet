import { useState, useRef, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Phone, Settings, MoreVertical, Pencil, Trash2 } from 'lucide-react';
import type { Agent } from '../../types/agent';

interface AgentCardProps {
  agent: Agent;
  onEdit?: (agent: Agent) => void;
  onDelete?: (agent: Agent) => void;
}

export function AgentCard({ agent, onEdit, onDelete }: AgentCardProps) {
  const { status, phone, config } = agent;
  const name = config.agent.name;
  const businessName = config.agent.business_name;
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const statusColors = {
    active: 'bg-accent',
    inactive: 'bg-muted',
    paused: 'bg-amber-600',
  };

  const statusLabels = {
    active: 'Active',
    inactive: 'Inactive',
    paused: 'Paused',
  };

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleEdit = () => {
    setIsMenuOpen(false);
    onEdit?.(agent);
  };

  const handleDelete = () => {
    setIsMenuOpen(false);
    onDelete?.(agent);
  };

  return (
    <div className="border-2 border-ink bg-white p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-paper border border-rule flex items-center justify-center">
            <Settings className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-display text-lg font-semibold text-ink">{name || 'Unnamed Agent'}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
              <span className="text-xs text-muted">{statusLabels[status]}</span>
            </div>
          </div>
        </div>

        {/* Dropdown Menu */}
        <div ref={menuRef} className="relative">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-1.5 text-muted hover:text-ink hover:bg-paper transition-colors"
            aria-label="Agent actions"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          <AnimatePresence>
            {isMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-1 w-36 py-1 bg-white border-2 border-ink z-10"
              >
                <button
                  onClick={handleEdit}
                  className="w-full px-3 py-2 text-left text-sm text-ink hover:bg-paper flex items-center gap-2 transition-colors"
                >
                  <Pencil className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  className="w-full px-3 py-2 text-left text-sm text-red-700 hover:bg-red-50 flex items-center gap-2 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Business Name */}
      {businessName && (
        <p className="text-sm text-muted mb-4 line-clamp-2">{businessName}</p>
      )}

      {/* Phone */}
      {phone && (
        <div className="flex items-center gap-2 text-sm text-muted mb-4">
          <Phone className="w-4 h-4" />
          <span>{phone}</span>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={() => onEdit?.(agent)}
        className="w-full min-h-11 py-2 px-4 border-2 border-ink bg-white text-ink text-sm font-medium hover:bg-ink hover:text-paper transition-colors"
      >
        Edit Configuration
      </button>
    </div>
  );
}
