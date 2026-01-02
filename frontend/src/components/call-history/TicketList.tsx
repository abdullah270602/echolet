/**
 * TicketList Component
 * Displays a list of call history items in a customer support ticket style
 */

import { motion } from 'framer-motion';
import {
  Clock,
  Phone,
  Tag,
  AlertCircle,
  Loader2,
  RefreshCw,
  User,
  CheckCircle,
  CircleDot,
} from 'lucide-react';
import type { CallHistoryItem } from '../../types/callHistory';
import {
  formatDuration,
  formatRelativeTime,
} from '../../types/callHistory';

interface TicketListProps {
  calls: CallHistoryItem[];
  isLoading: boolean;
  error: string | null;
  onSelectCall: (call: CallHistoryItem) => void;
  onRefresh: () => void;
}

/**
 * Get the first meaningful user message from transcript as description
 */
function getCallDescription(call: CallHistoryItem): string {
  if (call.summary && call.summary !== 'Pending') {
    return call.summary;
  }

  // Get first user message from transcript
  const userMessage = call.transcript?.find(msg => msg.role === 'user');
  if (userMessage?.content) {
    return userMessage.content.length > 150
      ? userMessage.content.slice(0, 150) + '...'
      : userMessage.content;
  }

  return 'No transcript available';
}

/**
 * Priority Badge Component
 */
function PriorityBadge({ priority }: { priority: string }) {
  const config = {
    urgent: {
      bg: 'bg-red-500/20',
      text: 'text-red-400',
      border: 'border-red-500/30',
      icon: AlertCircle,
    },
    normal: {
      bg: 'bg-teal-500/20',
      text: 'text-teal-400',
      border: 'border-teal-500/30',
      icon: CheckCircle,
    },
    low: {
      bg: 'bg-gray-500/20',
      text: 'text-gray-400',
      border: 'border-gray-500/30',
      icon: CircleDot,
    },
  };

  const { bg, text, border, icon: Icon } = config[priority as keyof typeof config] || config.normal;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${bg} ${text} border ${border}`}>
      <Icon className="w-3 h-3" />
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </span>
  );
}

/**
 * Service Tag Badge Component
 */
function ServiceTag({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-teal-500/20 text-teal-400 border border-teal-500/30">
      <Tag className="w-3 h-3" />
      {label}
    </span>
  );
}

/**
 * Single Ticket Card Component
 */
function TicketCard({
  call,
  onClick,
  index,
}: {
  call: CallHistoryItem;
  onClick: () => void;
  index: number;
}) {
  const description = getCallDescription(call);

  // Extract caller info placeholder (in real app, would come from user data)
  const callerId = call.room_name.slice(0, 8);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      onClick={onClick}
      className="group p-4 rounded-xl bg-white/5 border border-white/10
                 hover:bg-white/10 hover:border-teal-500/30
                 transition-all duration-200 cursor-pointer"
    >
      {/* Header: User Info + Timestamp */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500/30 to-purple-500/30 flex items-center justify-center border border-white/10">
            <User className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <p className="text-white font-medium">Caller #{callerId}</p>
            <div className="flex items-center gap-1 text-white/50 text-sm">
              <Phone className="w-3 h-3" />
              <span>Session {call.id}</span>
            </div>
          </div>
        </div>
        <span className="text-white/40 text-xs">
          {formatRelativeTime(call.created_at)}
        </span>
      </div>

      {/* Tags Row */}
      <div className="flex items-center gap-2 mb-3">
        <ServiceTag label={call.status === 'completed' ? 'Completed Call' : call.status} />
        <PriorityBadge priority={call.priority} />
        {call.duration_seconds && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs text-white/50">
            <Clock className="w-3 h-3" />
            {formatDuration(call.duration_seconds)}
          </span>
        )}
      </div>

      {/* Description */}
      <p className="text-white/70 text-sm mb-3 line-clamp-2">
        {description}
      </p>

      {/* AI Analysis Section */}
      <div className="pt-3 border-t border-white/5">
        <p className="text-teal-400 text-xs font-medium mb-1.5">AI Analysis</p>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-green-400" />
            <span className="text-white/50">Sentiment:</span>
            <span className="text-white/70">
              {call.priority === 'urgent' ? 'Concerned' : 'Neutral'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <CircleDot className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-white/50">Action:</span>
            <span className="text-white/70">
              {call.priority === 'urgent' ? 'Callback' : 'None Required'}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/**
 * Loading State Component
 */
function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="w-8 h-8 text-teal-400 animate-spin mb-4" />
      <p className="text-white/50 text-sm">Loading call history...</p>
    </div>
  );
}

/**
 * Error State Component
 */
function ErrorState({
  error,
  onRetry,
}: {
  error: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="p-3 rounded-full bg-red-500/10 mb-4">
        <AlertCircle className="w-8 h-8 text-red-400" />
      </div>
      <p className="text-white font-medium mb-1">Failed to load call history</p>
      <p className="text-white/50 text-sm mb-4">{error}</p>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5
                   text-white/70 text-sm font-medium border border-white/10
                   hover:bg-white/10 transition-all"
      >
        <RefreshCw className="w-4 h-4" />
        Try Again
      </motion.button>
    </div>
  );
}

/**
 * Empty State Component
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="p-3 rounded-full bg-white/5 mb-4">
        <Phone className="w-8 h-8 text-white/30" />
      </div>
      <p className="text-white font-medium mb-1">No calls yet</p>
      <p className="text-white/50 text-sm">
        Your call history will appear here after your first call.
      </p>
    </div>
  );
}

/**
 * Main TicketList Component
 */
export function TicketList({
  calls,
  isLoading,
  error,
  onSelectCall,
  onRefresh,
}: TicketListProps) {
  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={onRefresh} />;
  }

  if (calls.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-3">
      {calls.map((call, index) => (
        <TicketCard
          key={call.id}
          call={call}
          onClick={() => onSelectCall(call)}
          index={index}
        />
      ))}
    </div>
  );
}
