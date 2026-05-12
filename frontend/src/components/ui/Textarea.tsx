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
            w-full px-4 py-2.5 resize-y
            bg-white border text-ink
            placeholder:text-muted/60
            transition-colors
            focus:outline-none focus:border-ink
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error
              ? 'border-red-600 focus:border-red-600'
              : 'border-rule hover:border-ink'
            }
            ${className}
          `}
          {...props}
        />
        {hint && !error && (
          <p className="text-xs text-muted mt-1">{hint}</p>
        )}
        {error && (
          <p className="text-xs text-red-700 mt-1">{error}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
