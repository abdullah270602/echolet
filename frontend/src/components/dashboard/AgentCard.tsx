import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, Settings, MoreVertical, Pencil, Trash2 } from 'lucide-react';
import type { Agent } from '../../types/agent';

interface AgentCardProps {
  agent: Agent;
  onEdit?: (agent: Agent) => void;
  onDelete?: (agent: Agent) => void;
}

export function AgentCard({ agent, onEdit, onDelete }: AgentCardProps) {
  const { name, status, phone, description } = agent;
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const statusColors = {
    active: 'bg-green-500',
    inactive: 'bg-gray-500',
    paused: 'bg-amber-500',
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
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="glass rounded-xl p-5 border border-white/10 hover:border-teal-500/30 transition-all duration-300 hover:shadow-glow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-500/20 to-purple-500/20 flex items-center justify-center">
            <Settings className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{name || 'Unnamed Agent'}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${statusColors[status]} animate-pulse`} />
              <span className="text-xs text-white/50">{statusLabels[status]}</span>
            </div>
          </div>
        </div>

        {/* Dropdown Menu */}
        <div ref={menuRef} className="relative">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-1.5 text-white/40 hover:text-white/70 hover:bg-white/5 rounded-lg transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          <AnimatePresence>
            {isMenuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-1 w-36 py-1 rounded-lg glass-strong border border-white/10 shadow-xl z-10"
              >
                <button
                  onClick={handleEdit}
                  className="w-full px-3 py-2 text-left text-sm text-white/70 hover:text-white hover:bg-white/5 flex items-center gap-2 transition-colors"
                >
                  <Pencil className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  className="w-full px-3 py-2 text-left text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 flex items-center gap-2 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Description */}
      {description && (
        <p className="text-sm text-white/60 mb-4 line-clamp-2">{description}</p>
      )}

      {/* Phone */}
      {phone && (
        <div className="flex items-center gap-2 text-sm text-white/50 mb-4">
          <Phone className="w-4 h-4" />
          <span>{phone}</span>
        </div>
      )}

      {/* Action Button */}
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={() => onEdit?.(agent)}
        className="w-full py-2 px-4 rounded-lg bg-white/5 text-white/70 text-sm font-medium border border-white/10 hover:bg-white/10 hover:border-teal-500/30 transition-all"
      >
        Edit Configuration
      </motion.button>
    </motion.div>
  );
}
