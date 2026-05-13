import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
}

export function Card({
  children,
  className = '',
  hover = false,
  glow = false,
}: CardProps) {
  return (
    <div
      className={`
        glass rounded-2xl
        ${hover ? 'transition-all duration-300 hover:border-white/20 hover:bg-white/8' : ''}
        ${glow ? 'shadow-glow-sm hover:shadow-glow-md' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
