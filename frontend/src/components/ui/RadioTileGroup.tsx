import { motion } from 'framer-motion';
import { Label } from './Label';

interface RadioTileOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
}

interface RadioTileGroupProps {
  options: RadioTileOption[];
  value: string;
  onChange: (value: string) => void;
  name: string;
  label?: string;
  required?: boolean;
  error?: string;
  columns?: 2 | 3 | 4;
  className?: string;
}

export function RadioTileGroup({
  options,
  value,
  onChange,
  name,
  label,
  required,
  error,
  columns = 3,
  className = '',
}: RadioTileGroupProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };

  return (
    <div className={className}>
      {label && (
        <Label required={required} className="mb-3">
          {label}
        </Label>
      )}
      <div className={`grid ${gridCols[columns]} gap-3`}>
        {options.map((option) => {
          const isSelected = value === option.value;

          return (
            <motion.label
              key={option.value}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={`
                relative flex flex-col items-center p-4 rounded-xl cursor-pointer
                glass border transition-all duration-200
                ${isSelected
                  ? 'border-teal-500 bg-teal-500/10'
                  : 'border-white/10 hover:border-white/20'
                }
              `}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={isSelected}
                onChange={() => onChange(option.value)}
                className="sr-only"
              />

              {option.icon && (
                <div
                  className={`
                    mb-2 transition-colors duration-200
                    ${isSelected ? 'text-teal-400' : 'text-white/50'}
                  `}
                >
                  {option.icon}
                </div>
              )}

              <span
                className={`
                  text-sm font-medium text-center transition-colors duration-200
                  ${isSelected ? 'text-teal-400' : 'text-white/70'}
                `}
              >
                {option.label}
              </span>

              {option.description && (
                <span className="text-xs text-white/40 text-center mt-1">
                  {option.description}
                </span>
              )}

              {isSelected && (
                <motion.div
                  layoutId={`radio-indicator-${name}`}
                  className="absolute inset-0 border-2 border-teal-500 rounded-xl pointer-events-none"
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                />
              )}
            </motion.label>
          );
        })}
      </div>
      {error && (
        <p className="text-xs text-red-400 mt-2">{error}</p>
      )}
    </div>
  );
}
