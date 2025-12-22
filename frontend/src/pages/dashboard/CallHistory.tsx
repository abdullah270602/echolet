import { motion } from 'framer-motion';
import { History, Clock } from 'lucide-react';

export function CallHistory() {
  return (
    <div className="max-w-4xl mx-auto flex items-center justify-center min-h-[calc(100vh-12rem)]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-teal-500/10 to-purple-500/10 flex items-center justify-center border border-white/10">
          <History className="w-10 h-10 text-teal-400/60" />
        </div>
        <h2 className="text-2xl font-semibold text-white mb-2">Call History</h2>
        <p className="text-white/50 mb-6 max-w-md">
          View your past conversations, transcripts, and tickets created from voice interactions.
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-white/40 text-sm">
          <Clock className="w-4 h-4" />
          Coming Soon
        </div>
      </motion.div>
    </div>
  );
}
