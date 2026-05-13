import { ReactNode } from 'react';

interface ButtonProps {
  children: ReactNode;
  variant?: 'glow' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  type?: 'button' | 'submit' | 'reset';
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

export function Button({
  children,
  variant = 'glow',
  size = 'md',
  type = 'button',
  onClick,
  className = '',
  disabled = false,
}: ButtonProps) {
  const sizeClasses = {
    sm: 'min-h-9 px-3 py-1.5 text-sm',
    md: 'min-h-11 px-6 py-2.5 text-base',
    lg: 'min-h-12 px-8 py-3 text-lg',
  };

  const variantClasses = {
    glow: 'bg-accent text-white font-semibold hover:bg-accent-dark transition-colors',
    secondary: 'border-2 border-ink bg-white text-ink font-medium hover:bg-ink hover:text-paper transition-colors',
    ghost: 'bg-transparent border border-rule hover:border-ink hover:bg-paper text-ink font-medium transition-colors',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        cursor-pointer
        flex items-center justify-center
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    >
      {children}
    </button>
  );
}
