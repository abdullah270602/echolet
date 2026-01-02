/**
 * Call History Page
 * Displays user's call history with ticket list and detail modal
 */

import { motion } from 'framer-motion';
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
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-6"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-teal-500/10">
            <History className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">Call History</h1>
            <p className="text-sm text-white/50">
              {calls.length > 0
                ? `${calls.length} call${calls.length === 1 ? '' : 's'} recorded`
                : 'View your past conversations and transcripts'}
            </p>
          </div>
        </div>

        {/* Refresh Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={refetch}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg
                     bg-white/5 border border-white/10
                     text-white/70 text-sm font-medium
                     hover:bg-white/10 hover:text-white
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all"
        >
          <RefreshCw
            className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
          />
          Refresh
        </motion.button>
      </motion.div>

      {/* Ticket List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <TicketList
          calls={calls}
          isLoading={isLoading}
          error={error}
          onSelectCall={openModal}
          onRefresh={refetch}
        />
      </motion.div>

      {/* Call Detail Modal */}
      <CallDetailModal
        call={selectedCall}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </div>
  );
}
