import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from './Button';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isLoading?: boolean;
  variant?: 'danger' | 'warning';
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isLoading = false,
  variant = 'danger',
}: ConfirmDialogProps) {
  const iconColors = {
    danger: 'text-red-400 bg-red-500/10',
    warning: 'text-amber-400 bg-amber-500/10',
  };

  const buttonColors = {
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    warning: 'bg-amber-500 hover:bg-amber-600 text-white',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div
              className="w-full max-w-md glass-strong rounded-2xl border border-white/10 p-6 pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-full ${iconColors[variant]}`}>
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white">{title}</h3>
                  <p className="mt-2 text-sm text-white/60">{message}</p>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5 text-white/50 hover:text-white" />
                </button>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 mt-6">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  {cancelLabel}
                </Button>
                <motion.button
                  whileHover={{ scale: isLoading ? 1 : 1.02 }}
                  whileTap={{ scale: isLoading ? 1 : 0.98 }}
                  onClick={onConfirm}
                  disabled={isLoading}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm
                    transition-colors cursor-pointer
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${buttonColors[variant]}
                  `}
                >
                  {isLoading ? 'Deleting...' : confirmLabel}
                </motion.button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
