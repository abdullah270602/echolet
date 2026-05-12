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
    danger: 'text-red-700 bg-red-50 border border-red-200',
    warning: 'text-amber-700 bg-amber-50 border border-amber-200',
  };

  const buttonColors = {
    danger: 'bg-red-700 hover:bg-red-800 text-white',
    warning: 'bg-amber-700 hover:bg-amber-800 text-white',
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
            className="fixed inset-0 z-50 bg-ink/40"
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div
              className="w-full max-w-md bg-white border-2 border-ink font-body text-ink p-6 pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-start gap-4">
                <div className={`p-3 ${iconColors[variant]}`}>
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h3 className="font-display text-lg font-bold text-ink">{title}</h3>
                  <p className="mt-2 text-sm text-muted">{message}</p>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="p-1.5 text-muted hover:text-ink hover:bg-paper transition-colors"
                  aria-label="Close dialog"
                >
                  <X className="w-5 h-5" />
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
                <button
                  onClick={onConfirm}
                  disabled={isLoading}
                  className={`
                    min-h-11 px-5 font-semibold text-sm
                    transition-colors cursor-pointer
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${buttonColors[variant]}
                  `}
                >
                  {isLoading ? 'Deleting...' : confirmLabel}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
