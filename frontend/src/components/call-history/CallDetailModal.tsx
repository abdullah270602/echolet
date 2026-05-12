/**
 * CallDetailModal Component
 * Modal to display call details with transcript chat view
 */

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Clock,
  Phone,
  User,
  Bot,
  Calendar,
  Tag,
  AlertCircle,
  Smile,
  Meh,
  Frown,
  Angry,
  Bell,
  BellOff,
  CheckSquare,
  Square,
} from 'lucide-react';
import type { CallHistoryItem, TranscriptMessage, CallSentiment, CallCategory, CallUrgency } from '../../types/callHistory';
import {
  formatDuration,
  formatMessageTime,
  getPriorityClasses,
  getStatusClasses,
  getCategoryClasses,
  getUrgencyClasses,
  getSentimentClasses,
} from '../../types/callHistory';

interface CallDetailModalProps {
  call: CallHistoryItem | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Priority Badge Component
 */
function PriorityBadge({ priority }: { priority: string }) {
  const classes = getPriorityClasses(priority as 'urgent' | 'normal' | 'low');
  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium border ${classes}`}
    >
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </span>
  );
}

/**
 * Status Badge Component
 */
function StatusBadge({ status }: { status: string }) {
  const classes = getStatusClasses(status as 'completed' | 'failed' | 'pending' | 'active');
  return (
    <span className={`px-2 py-0.5 text-xs font-medium ${classes}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
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
      {urgency} Priority
    </span>
  );
}

/**
 * Get sentiment icon
 */
function getSentimentIcon(sentiment: CallSentiment | null) {
  switch (sentiment) {
    case 'Positive':
      return <Smile className="w-4 h-4 text-accent" />;
    case 'Neutral':
      return <Meh className="w-4 h-4 text-muted" />;
    case 'Frustrated':
      return <Frown className="w-4 h-4 text-amber-700" />;
    case 'Angry':
      return <Angry className="w-4 h-4 text-red-700" />;
    default:
      return <Meh className="w-4 h-4 text-muted" />;
  }
}

/**
 * Chat Message Bubble Component
 */
function MessageBubble({ message }: { message: TranscriptMessage }) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-start' : 'justify-end'} mb-4`}
    >
      <div
        className={`max-w-[80%] ${
          isUser ? 'order-2' : 'order-1'
        }`}
      >
        {/* Avatar and Role */}
        <div
          className={`flex items-center gap-2 mb-1 ${
            isUser ? 'flex-row' : 'flex-row-reverse'
          }`}
        >
          <div
            className={`w-6 h-6 flex items-center justify-center border ${
              isUser ? 'bg-paper border-rule' : 'bg-accent border-accent'
            }`}
          >
            {isUser ? (
              <User className="w-3.5 h-3.5 text-ink" />
            ) : (
              <Bot className="w-3.5 h-3.5 text-white" />
            )}
          </div>
          <span className="text-xs font-semibold text-ink">
            {isUser ? 'User' : 'Agent'}
          </span>
          <span className="text-xs text-muted">
            {formatMessageTime(message.timestamp)}
          </span>
        </div>

        {/* Message Bubble */}
        <div
          className={`px-4 py-2.5 border ${
            isUser
              ? 'bg-paper border-rule text-ink'
              : 'bg-white border-ink text-ink'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Transcript Empty State
 */
function TranscriptEmpty() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-12 h-12 bg-paper border border-rule flex items-center justify-center mb-3">
        <Phone className="w-6 h-6 text-muted" />
      </div>
      <p className="text-ink font-medium text-sm">No transcript available</p>
      <p className="text-muted text-xs mt-1">
        The conversation transcript was not recorded.
      </p>
    </div>
  );
}

/**
 * Main CallDetailModal Component
 */
export function CallDetailModal({
  call,
  isOpen,
  onClose,
}: CallDetailModalProps) {
  const transcriptRef = useRef<HTMLDivElement>(null);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Scroll to bottom when transcript loads
  useEffect(() => {
    if (transcriptRef.current && call?.transcript) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [call?.transcript]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <AnimatePresence>
      {isOpen && call && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-ink/40 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2
                       md:w-full md:max-w-2xl md:max-h-[85vh]
                       bg-white border-2 border-ink font-body text-ink
                       overflow-hidden z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-rule">
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="font-display text-lg font-bold text-ink">Call Details</h2>
                <StatusBadge status={call.status} />
                {call.category ? (
                  <CategoryBadge category={call.category} />
                ) : (
                  <PriorityBadge priority={call.priority} />
                )}
                {call.urgency && <UrgencyBadge urgency={call.urgency} />}
              </div>
              <button
                onClick={onClose}
                className="p-2 text-muted hover:text-ink hover:bg-paper transition-colors"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metadata Bar */}
            <div className="flex items-center gap-6 px-4 py-3 bg-paper border-b border-rule">
              <div className="flex items-center gap-2 text-sm text-muted">
                <Clock className="w-4 h-4" />
                <span>Duration: {formatDuration(call.duration_seconds)}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted">
                <Calendar className="w-4 h-4" />
                <span>{formatDate(call.created_at)}</span>
              </div>
            </div>

            {/* Transcript Area */}
            <div
              ref={transcriptRef}
              className="flex-1 overflow-y-auto p-4 min-h-0"
            >
              {call.transcript && call.transcript.length > 0 ? (
                <div className="space-y-2">
                  {call.transcript.map((message, index) => (
                    <MessageBubble key={index} message={message} />
                  ))}
                </div>
              ) : (
                <TranscriptEmpty />
              )}
            </div>

            {/* Analysis Panel */}
            {(call.sentiment || call.action_required !== null || (call.action_items && call.action_items.length > 0) || (call.summary && call.summary !== 'Pending')) && (
              <div className="p-4 border-t border-rule bg-paper/50 space-y-4">
                {/* Summary */}
                {call.summary && call.summary !== 'Pending' && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink mb-1">
                      Summary
                    </h3>
                    <p className="text-sm text-muted leading-relaxed">
                      {call.summary}
                    </p>
                  </div>
                )}

                {/* Analysis Metrics Row */}
                {(call.sentiment || call.action_required !== null) && (
                  <div className="flex items-center gap-6 flex-wrap">
                    {/* Sentiment */}
                    {call.sentiment && (
                      <div className="flex items-center gap-2">
                        {getSentimentIcon(call.sentiment)}
                        <span className="text-muted text-sm">Sentiment:</span>
                        <span className={`text-sm font-semibold ${getSentimentClasses(call.sentiment).split(' ')[1]}`}>
                          {call.sentiment}
                        </span>
                      </div>
                    )}

                    {/* Action Required */}
                    {call.action_required !== null && (
                      <div className="flex items-center gap-2">
                        {call.action_required ? (
                          <Bell className="w-4 h-4 text-amber-700" />
                        ) : (
                          <BellOff className="w-4 h-4 text-accent" />
                        )}
                        <span className="text-muted text-sm">Action Required:</span>
                        <span className={`text-sm font-semibold ${call.action_required ? 'text-amber-700' : 'text-accent'}`}>
                          {call.action_required ? 'Yes' : 'No'}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Action Items */}
                {call.action_items && call.action_items.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink mb-2 flex items-center gap-2">
                      <CheckSquare className="w-4 h-4 text-accent" />
                      Action Items ({call.action_items.length})
                    </h3>
                    <ul className="space-y-1.5">
                      {call.action_items.map((item, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-muted">
                          <Square className="w-3.5 h-3.5 mt-0.5 text-accent flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
