/**
 * Call History Types
 * Types for the Call History Dashboard feature
 */

export type CallPriority = 'urgent' | 'normal' | 'low';
export type CallStatus = 'pending' | 'active' | 'completed' | 'failed';
export type CallCategory = 'Appointment' | 'Inquiry' | 'Complaint' | 'Spam' | 'Urgent Service' | 'Other';
export type CallUrgency = 'High' | 'Medium' | 'Low';
export type CallSentiment = 'Positive' | 'Neutral' | 'Frustrated' | 'Angry';

/**
 * A single message in a call transcript
 */
export interface TranscriptMessage {
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  language?: string;
}

/**
 * A call history item from the API
 */
export interface CallHistoryItem {
  id: number;
  room_name: string;
  agent_id: number;
  status: CallStatus;
  duration_seconds: number | null;
  transcript: TranscriptMessage[] | null;
  summary: string | null;
  priority: CallPriority;
  created_at: string | null;
  ended_at: string | null;
  // Analysis fields
  category: CallCategory | null;
  urgency: CallUrgency | null;
  sentiment: CallSentiment | null;
  action_required: boolean | null;
  action_items: string[] | null;
  // Agent info
  agent_name: string | null;
  is_agent_deleted: boolean;
}

/**
 * Helper function to format duration in seconds to "Xm Ys" format
 */
export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === 0) return '0s';

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return remainingSeconds > 0
      ? `${minutes}m ${remainingSeconds}s`
      : `${minutes}m`;
  }
  return `${remainingSeconds}s`;
}

/**
 * Helper function to format timestamp to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Unknown';

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

/**
 * Helper function to format timestamp to absolute time in user's local timezone
 * (e.g., "Jan 21, 14:30")
 */
export function formatAbsoluteTime(dateString: string | null): string {
  if (!dateString) return '';

  const date = new Date(dateString);
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Helper function to format timestamp to time string (e.g., "12:34 PM")
 */
export function formatMessageTime(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Get priority badge color classes
 */
export function getPriorityClasses(priority: CallPriority): string {
  switch (priority) {
    case 'urgent':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'normal':
      return 'bg-teal-500/20 text-teal-400 border-teal-500/30';
    case 'low':
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}

/**
 * Get status badge color classes
 */
export function getStatusClasses(status: CallStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-green-500/20 text-green-400';
    case 'active':
      return 'bg-teal-500/20 text-teal-400';
    case 'pending':
      return 'bg-amber-500/20 text-amber-400';
    case 'failed':
      return 'bg-red-500/20 text-red-400';
    default:
      return 'bg-gray-500/20 text-gray-400';
  }
}

/**
 * Get category badge color classes
 */
export function getCategoryClasses(category: CallCategory | null): string {
  switch (category) {
    case 'Appointment':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'Inquiry':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    case 'Complaint':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'Spam':
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    case 'Urgent Service':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'Other':
    default:
      return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  }
}

/**
 * Get urgency badge color classes
 */
export function getUrgencyClasses(urgency: CallUrgency | null): string {
  switch (urgency) {
    case 'High':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'Medium':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    case 'Low':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}

/**
 * Get sentiment badge color classes and icon
 */
export function getSentimentClasses(sentiment: CallSentiment | null): string {
  switch (sentiment) {
    case 'Positive':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'Neutral':
      return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    case 'Frustrated':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'Angry':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}
