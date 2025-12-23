import { User, Phone, Clock, Tag, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface TicketCardProps {
  caller?: string;
  phone?: string;
  time?: string;
  intent?: string;
  summary?: string;
  priority?: 'low' | 'medium' | 'high';
  compact?: boolean;
  className?: string;
}

export function TicketCard({
  caller = 'Sarah Johnson',
  phone = '(555) 123-4567',
  time = '2 min ago',
  intent = 'Quote Request',
  summary = 'Interested in website redesign package. Budget ~$5,000. Wants callback before 3pm.',
  priority = 'high',
  compact = false,
  className = '',
}: TicketCardProps) {
  const priorityConfig = {
    low: {
      bg: 'bg-green-500/20',
      text: 'text-green-400',
      border: 'border-green-500/30',
      label: 'Low',
    },
    medium: {
      bg: 'bg-amber-500/20',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      label: 'Medium',
    },
    high: {
      bg: 'bg-red-500/20',
      text: 'text-red-400',
      border: 'border-red-500/30',
      label: 'Urgent',
    },
  };

  const config = priorityConfig[priority];

  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`glass p-4 rounded-xl border-teal-500/30 ${className}`}
      >
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle2 className="w-4 h-4 text-teal-400" />
          <span className="text-sm font-medium text-white">New Lead</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${config.bg} ${config.text} ${config.border} border`}>
            {config.label}
          </span>
        </div>
        <p className="text-xs text-white/60 line-clamp-2">{summary}</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass p-4 sm:p-6 rounded-2xl border-teal-500/30 ${className}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-teal-500/20 flex items-center justify-center">
            <User className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <div className="font-semibold text-white">{caller}</div>
            <div className="text-sm text-white/50 flex items-center gap-1">
              <Phone className="w-3 h-3" /> {phone}
            </div>
          </div>
        </div>
        <div className="text-xs text-white/40 flex items-center gap-1">
          <Clock className="w-3 h-3" /> {time}
        </div>
      </div>

      {/* Tags */}
      <div className="flex gap-2 mb-3 flex-wrap">
        <span className="px-2 py-1 text-xs rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30 flex items-center gap-1">
          <Tag className="w-3 h-3" /> {intent}
        </span>
        <span className={`px-2 py-1 text-xs rounded-full border flex items-center gap-1 ${config.bg} ${config.text} ${config.border}`}>
          <AlertCircle className="w-3 h-3" /> {config.label}
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-white/70 leading-relaxed">{summary}</p>

      {/* AI Analysis */}
      <div className="mt-4 pt-3 border-t border-white/10">
        <div className="text-xs text-teal-400 font-medium mb-1">AI Analysis</div>
        <div className="flex flex-wrap gap-2 text-xs text-white/60">
          <span className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-green-400" />
            Sentiment: Interested
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-green-400" />
            Action: Callback
          </span>
        </div>
      </div>
    </motion.div>
  );
}
