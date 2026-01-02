/**
 * CallDetailModal Component
 * Modal to display call details with transcript chat view
 */

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Clock, Phone, User, Bot, Calendar } from 'lucide-react';
import type { CallHistoryItem, TranscriptMessage } from '../../types/callHistory';
import {
  formatDuration,
  formatMessageTime,
  getPriorityClasses,
  getStatusClasses,
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
      className={`px-2 py-0.5 text-xs font-medium rounded-full border ${classes}`}
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
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${classes}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
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
            className={`w-6 h-6 rounded-full flex items-center justify-center ${
              isUser ? 'bg-white/10' : 'bg-teal-500/20'
            }`}
          >
            {isUser ? (
              <User className="w-3.5 h-3.5 text-white/70" />
            ) : (
              <Bot className="w-3.5 h-3.5 text-teal-400" />
            )}
          </div>
          <span className="text-xs text-white/40">
            {isUser ? 'User' : 'Agent'}
          </span>
          <span className="text-xs text-white/30">
            {formatMessageTime(message.timestamp)}
          </span>
        </div>

        {/* Message Bubble */}
        <div
          className={`px-4 py-2.5 rounded-2xl ${
            isUser
              ? 'bg-white/10 text-white/90 rounded-tl-sm'
              : 'bg-teal-500/20 text-white/90 rounded-tr-sm'
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
      <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
        <Phone className="w-6 h-6 text-white/30" />
      </div>
      <p className="text-white/50 text-sm">No transcript available</p>
      <p className="text-white/30 text-xs mt-1">
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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2
                       md:w-full md:max-w-2xl md:max-h-[85vh]
                       bg-midnight-800 rounded-2xl border border-white/10
                       shadow-2xl overflow-hidden z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-white">Call Details</h2>
                <StatusBadge status={call.status} />
                <PriorityBadge priority={call.priority} />
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5 text-white/70" />
              </button>
            </div>

            {/* Metadata Bar */}
            <div className="flex items-center gap-6 px-4 py-3 bg-white/5 border-b border-white/10">
              <div className="flex items-center gap-2 text-sm text-white/60">
                <Clock className="w-4 h-4" />
                <span>Duration: {formatDuration(call.duration_seconds)}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-white/60">
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

            {/* Summary Footer */}
            {call.summary && call.summary !== 'Pending' && (
              <div className="p-4 border-t border-white/10 bg-white/5">
                <h3 className="text-sm font-medium text-white/70 mb-2">
                  Summary
                </h3>
                <p className="text-sm text-white/80 leading-relaxed">
                  {call.summary}
                </p>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
