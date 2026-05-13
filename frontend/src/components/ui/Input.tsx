import { forwardRef } from 'react';
import { Label } from './Label';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, required, className = '', id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <Label htmlFor={inputId} required={required}>
            {label}
          </Label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`
            w-full px-4 py-2.5
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

Input.displayName = 'Input';
