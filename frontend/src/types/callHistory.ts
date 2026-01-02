/**
 * Call History Types
 * Types for the Call History Dashboard feature
 */

export type CallPriority = 'urgent' | 'normal' | 'low';
export type CallStatus = 'pending' | 'active' | 'completed' | 'failed';

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
