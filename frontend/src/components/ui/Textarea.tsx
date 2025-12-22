import { forwardRef } from 'react';
import { Label } from './Label';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  minHeight?: number;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, required, minHeight = 100, className = '', id, style, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <Label htmlFor={textareaId} required={required}>
            {label}
          </Label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          style={{ minHeight: `${minHeight}px`, ...style }}
          className={`
            w-full px-4 py-3 rounded-lg resize-y
            bg-white/5 border text-white
            placeholder:text-white/30
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-teal-500/20
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error
              ? 'border-red-500/50 focus:border-red-500/50'
              : 'border-white/10 focus:border-teal-500/50 hover:border-white/20'
            }
            ${className}
          `}
          {...props}
        />
        {hint && !error && (
          <p className="text-xs text-white/40 mt-1">{hint}</p>
        )}
        {error && (
          <p className="text-xs text-red-400 mt-1">{error}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
