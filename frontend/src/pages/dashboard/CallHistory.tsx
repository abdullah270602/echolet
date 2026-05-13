/**
 * Call History Page
 * Displays user's call history with ticket list and detail modal
 */

import { RefreshCw, History } from 'lucide-react';
import { useCallHistory } from '../../hooks/useCallHistory';
import { TicketList, CallDetailModal } from '../../components/call-history';

export function CallHistory() {
  const {
    calls,
    isLoading,
    error,
    refetch,
    selectedCall,
    isModalOpen,
    openModal,
    closeModal,
  } = useCallHistory();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white border border-rule">
            <History className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold text-ink">Call History</h1>
            <p className="text-sm text-muted">
              {calls.length > 0
                ? `${calls.length} call${calls.length === 1 ? '' : 's'} recorded`
                : 'View your past conversations and transcripts'}
            </p>
          </div>
        </div>

        {/* Refresh Button */}
        <button
          onClick={refetch}
          disabled={isLoading}
          className="flex items-center gap-2 min-h-11 px-4 border-2 border-ink bg-white
                     text-ink text-sm font-medium
                     hover:bg-ink hover:text-paper
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
        >
          <RefreshCw
            className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
          />
          Refresh
        </button>
      </div>

      {/* Ticket List */}
      <div>
        <TicketList
          calls={calls}
          isLoading={isLoading}
          error={error}
          onSelectCall={openModal}
          onRefresh={refetch}
        />
      </div>

      {/* Call Detail Modal */}
      <CallDetailModal
        call={selectedCall}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </div>
  );
}
