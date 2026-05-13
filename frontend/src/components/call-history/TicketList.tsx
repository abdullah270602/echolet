/**
 * TicketList Component
 * Displays a list of call history items in a customer support ticket style
 */

import {
  Clock,
  Phone,
  Tag,
  AlertCircle,
  Loader2,
  RefreshCw,
  CheckCircle,
  CircleDot,
  Smile,
  Meh,
  Frown,
  Angry,
  Bell,
  BellOff,
  Bot,
} from 'lucide-react';
import type { CallHistoryItem, CallSentiment, CallCategory, CallUrgency } from '../../types/callHistory';
import {
  formatDuration,
  formatRelativeTime,
  formatAbsoluteTime,
  getCategoryClasses,
  getUrgencyClasses,
  getSentimentClasses,
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
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-300',
      icon: AlertCircle,
    },
    normal: {
      bg: 'bg-paper',
      text: 'text-accent',
      border: 'border-rule',
      icon: CheckCircle,
    },
    low: {
      bg: 'bg-paper',
      text: 'text-muted',
      border: 'border-rule',
      icon: CircleDot,
    },
  };

  const { bg, text, border, icon: Icon } = config[priority as keyof typeof config] || config.normal;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium ${bg} ${text} border ${border}`}>
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
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-paper text-accent border border-rule">
      <Tag className="w-3 h-3" />
      {label}
    </span>
  );
}

/**
 * Category Badge Component
 */
function CategoryBadge({ category }: { category: CallCategory | null }) {
  if (!category) return null;
  const classes = getCategoryClasses(category);
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium border ${classes}`}>
      <Tag className="w-3 h-3" />
      {category}
    </span>
  );
}

/**
 * Urgency Badge Component
 */
function UrgencyBadge({ urgency }: { urgency: CallUrgency | null }) {
  if (!urgency) return null;
  const classes = getUrgencyClasses(urgency);
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium border ${classes}`}>
      <AlertCircle className="w-3 h-3" />
      {urgency}
    </span>
  );
}

/**
 * Get sentiment icon based on sentiment value
 */
function getSentimentIcon(sentiment: CallSentiment | null) {
  switch (sentiment) {
    case 'Positive':
      return <Smile className="w-3.5 h-3.5 text-accent" />;
    case 'Neutral':
      return <Meh className="w-3.5 h-3.5 text-muted" />;
    case 'Frustrated':
      return <Frown className="w-3.5 h-3.5 text-amber-700" />;
    case 'Angry':
      return <Angry className="w-3.5 h-3.5 text-red-700" />;
    default:
      return <Meh className="w-3.5 h-3.5 text-muted" />;
  }
}

/**
 * Single Ticket Card Component
 */
function TicketCard({
  call,
  onClick,
}: {
  call: CallHistoryItem;
  onClick: () => void;
  index: number;
}) {
  const description = getCallDescription(call);

  return (
    <article
      onClick={onClick}
      className="group p-5 bg-white border-2 border-ink hover:bg-paper/40 transition-colors cursor-pointer"
    >
      {/* Header: Agent Info + Timestamp */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-paper flex items-center justify-center border border-rule">
            <Bot className="w-5 h-5 text-accent" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="font-display font-semibold text-ink">
                {call.agent_name || 'Unknown Agent'}
              </p>
              {call.is_agent_deleted && (
                <span className="px-1.5 py-0.5 text-xs bg-paper text-muted border border-rule">
                  Deleted
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 text-muted text-sm">
              <Phone className="w-3 h-3" />
              <span>Session {call.id}</span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <p className="text-ink text-sm font-medium">
            {formatAbsoluteTime(call.created_at)}
          </p>
          <p className="text-muted text-xs">
            {formatRelativeTime(call.created_at)}
          </p>
        </div>
      </div>

      {/* Tags Row */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        {call.category ? (
          <CategoryBadge category={call.category} />
        ) : (
          <ServiceTag label={call.status === 'completed' ? 'Completed Call' : call.status} />
        )}
        {call.urgency ? (
          <UrgencyBadge urgency={call.urgency} />
        ) : (
          <PriorityBadge priority={call.priority} />
        )}
        {call.duration_seconds && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs text-muted">
            <Clock className="w-3 h-3" />
            {formatDuration(call.duration_seconds)}
          </span>
        )}
      </div>

      {/* Description */}
      <p className="text-muted text-sm mb-3 line-clamp-2">
        {description}
      </p>

      {/* AI Analysis Section */}
      <div className="pt-3 border-t border-rule">
        <p className="text-accent text-xs font-semibold mb-1.5">AI Analysis</p>
        <div className="flex items-center gap-4 text-sm flex-wrap">
          <div className="flex items-center gap-1.5">
            {getSentimentIcon(call.sentiment)}
            <span className="text-muted">Sentiment:</span>
            <span className={`font-medium ${getSentimentClasses(call.sentiment).split(' ')[1] || 'text-ink'}`}>
              {call.sentiment || 'Pending'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            {call.action_required ? (
              <Bell className="w-3.5 h-3.5 text-amber-700" />
            ) : (
              <BellOff className="w-3.5 h-3.5 text-accent" />
            )}
            <span className="text-muted">Action:</span>
            <span className={`font-medium ${call.action_required ? 'text-amber-700' : 'text-accent'}`}>
              {call.action_required === null
                ? 'Pending'
                : call.action_required
                  ? 'Required'
                  : 'None Required'}
            </span>
          </div>
          {call.action_items && call.action_items.length > 0 && (
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-accent" />
              <span className="text-muted">Tasks:</span>
              <span className="font-medium text-ink">{call.action_items.length}</span>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

/**
 * Loading State Component
 */
function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="w-8 h-8 text-accent animate-spin mb-4" />
      <p className="text-muted text-sm">Loading call history...</p>
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
    <div className="flex flex-col items-center justify-center py-16 border-2 border-ink bg-white p-8 text-center">
      <div className="p-3 bg-red-50 border border-red-200 mb-4">
        <AlertCircle className="w-8 h-8 text-red-700" />
      </div>
      <p className="font-display text-lg font-semibold text-ink mb-1">Failed to load call history</p>
      <p className="text-muted text-sm mb-4">{error}</p>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 min-h-11 px-5 border-2 border-ink bg-white
                   text-ink text-sm font-medium
                   hover:bg-ink hover:text-paper transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Try Again
      </button>
    </div>
  );
}

/**
 * Empty State Component
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 border-2 border-ink bg-white p-8 text-center">
      <div className="p-3 bg-paper border border-rule mb-4">
        <Phone className="w-8 h-8 text-muted" />
      </div>
      <p className="font-display text-lg font-semibold text-ink mb-1">No calls yet</p>
      <p className="text-muted text-sm">
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
    <div className="space-y-4">
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
