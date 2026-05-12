import { forwardRef } from 'react';

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ children, required, className = '', ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={`block text-sm font-semibold text-ink mb-1.5 ${className}`}
        {...props}
      >
        {children}
        {required && <span className="text-red-700 ml-1">*</span>}
      </label>
    );
  }
);

Label.displayName = 'Label';
