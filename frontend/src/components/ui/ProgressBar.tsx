import { motion } from 'framer-motion';

interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  showText?: boolean;
  size?: 'sm' | 'md';
  className?: string;
  formatValue?: (value: number, max: number) => string;
}

export function ProgressBar({
  value,
  max,
  label,
  showText = true,
  size = 'md',
  className = '',
  formatValue,
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  const getBarColor = () => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-amber-500';
    return 'bg-gradient-to-r from-teal-500 to-purple-500';
  };

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
  };

  const defaultFormatValue = (val: number, maxVal: number) => {
    return `${val.toLocaleString()} / ${maxVal.toLocaleString()}`;
  };

  const displayValue = formatValue
    ? formatValue(value, max)
    : defaultFormatValue(value, max);

  return (
    <div className={className}>
      {(label || showText) && (
        <div className="flex items-center justify-between text-xs mb-1.5">
          {label && <span className="text-white/50">{label}</span>}
          {showText && (
            <span
              className={`
                tabular-nums
                ${percentage >= 90 ? 'text-red-400' : percentage >= 70 ? 'text-amber-400' : 'text-white/70'}
              `}
            >
              {displayValue}
            </span>
          )}
        </div>
      )}

      <div className={`w-full bg-white/10 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={`h-full rounded-full ${getBarColor()}`}
        />
      </div>
    </div>
  );
}
