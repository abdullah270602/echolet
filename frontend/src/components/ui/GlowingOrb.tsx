import { motion } from 'framer-motion';

interface GlowingOrbProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function GlowingOrb({ size = 'md', className = '' }: GlowingOrbProps) {
  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  };

  return (
    <motion.div
      animate={{ scale: [1, 1.1, 1] }}
      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      className={`${sizeClasses[size]} relative ${className}`}
    >
      {/* Outer glow */}
      <div className="absolute inset-0 bg-gradient-to-br from-teal-400 to-purple-500 rounded-full blur-xl opacity-60" />
      {/* Inner orb */}
      <div className="absolute inset-2 bg-gradient-to-br from-teal-400 to-purple-500 rounded-full" />
      {/* Highlight */}
      <div className="absolute top-3 left-3 w-4 h-4 bg-white/40 rounded-full blur-sm" />
      {/* Center glow */}
      <motion.div
        animate={{ opacity: [0.5, 0.8, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute inset-4 bg-white/20 rounded-full blur-md"
      />
    </motion.div>
  );
}
