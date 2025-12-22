import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

interface VoicePreviewButtonProps {
  voiceId: string;
  disabled?: boolean;
}

export function VoicePreviewButton({ voiceId, disabled }: VoicePreviewButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handlePreview = async () => {
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }

    setIsLoading(true);

    // Mock preview functionality
    await new Promise((resolve) => setTimeout(resolve, 500));

    setIsLoading(false);
    setIsPlaying(true);

    toast.success(`Playing ${voiceId} voice sample...`, {
      duration: 2000,
      icon: '🔊',
    });

    // Simulate audio playback duration
    setTimeout(() => {
      setIsPlaying(false);
    }, 2000);
  };

  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={handlePreview}
      disabled={disabled || isLoading}
      className={`
        p-3 rounded-lg transition-all duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        ${isPlaying
          ? 'bg-teal-500/20 border-teal-500/50 text-teal-400'
          : 'bg-white/5 border-white/10 text-white/50 hover:text-white hover:bg-white/10'
        }
        border
      `}
      title={isPlaying ? 'Stop preview' : 'Preview voice'}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : isPlaying ? (
        <Pause className="w-4 h-4" />
      ) : (
        <Play className="w-4 h-4" />
      )}
    </motion.button>
  );
}
