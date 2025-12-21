import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, Pause, Volume2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

interface AudioModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AudioModal({ isOpen, onClose }: AudioModalProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Sample conversation transcript
  const transcript = [
    { speaker: 'AI', text: "Good afternoon, thank you for calling Johnson's Plumbing. How can I help you today?" },
    { speaker: 'Caller', text: "Hi, I have a pretty urgent issue. My kitchen sink is leaking badly and water is going everywhere!" },
    { speaker: 'AI', text: "I understand this is urgent. I'm marking this as a high-priority call. Can I get your name and address so we can dispatch someone right away?" },
    { speaker: 'Caller', text: "Yes, I'm Sarah Johnson at 142 Oak Street." },
    { speaker: 'AI', text: "Perfect, Sarah. I've created an urgent ticket for you. A technician will call you back within 15 minutes to schedule an emergency visit. Is there anything else I can help with?" },
    { speaker: 'Caller', text: "No, that's great. Thank you so much!" },
  ];

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg mx-4"
          >
            <div className="glass-strong rounded-2xl p-6 shadow-2xl border border-white/10">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-white">Example AI Call</h3>
                  <p className="text-sm text-white/50">Listen to how Echolet handles a real call</p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5 text-white/70" />
                </button>
              </div>

              {/* Audio Player */}
              <div className="bg-midnight-900/50 rounded-xl p-4 mb-6">
                <div className="flex items-center gap-4">
                  <button
                    onClick={togglePlay}
                    className="w-12 h-12 rounded-full bg-gradient-to-r from-teal-500 to-purple-500 flex items-center justify-center hover:shadow-glow-md transition-shadow"
                  >
                    {isPlaying ? (
                      <Pause className="w-5 h-5 text-white" />
                    ) : (
                      <Play className="w-5 h-5 text-white ml-0.5" />
                    )}
                  </button>

                  <div className="flex-1">
                    <input
                      type="range"
                      min={0}
                      max={duration || 100}
                      value={currentTime}
                      onChange={handleSeek}
                      className="w-full h-1 bg-white/20 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none
                        [&::-webkit-slider-thumb]:w-3
                        [&::-webkit-slider-thumb]:h-3
                        [&::-webkit-slider-thumb]:bg-teal-400
                        [&::-webkit-slider-thumb]:rounded-full
                        [&::-webkit-slider-thumb]:shadow-glow-sm"
                    />
                    <div className="flex justify-between text-xs text-white/50 mt-1">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration || 45)}</span>
                    </div>
                  </div>

                  <Volume2 className="w-5 h-5 text-white/50" />
                </div>

                {/* Placeholder audio - in production, you'd use a real audio file */}
                <audio ref={audioRef} src="/demo-call.mp3" />
              </div>

              {/* Transcript */}
              <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                <div className="text-xs text-white/50 uppercase tracking-wider mb-2">Transcript</div>
                {transcript.map((line, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${line.speaker === 'Caller' ? 'flex-row-reverse' : ''}`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium ${
                        line.speaker === 'AI'
                          ? 'bg-teal-500/20 text-teal-400'
                          : 'bg-purple-500/20 text-purple-400'
                      }`}
                    >
                      {line.speaker === 'AI' ? 'AI' : 'C'}
                    </div>
                    <div
                      className={`flex-1 p-3 rounded-xl text-sm ${
                        line.speaker === 'AI'
                          ? 'bg-teal-500/10 text-white/80'
                          : 'bg-purple-500/10 text-white/80'
                      }`}
                    >
                      {line.text}
                    </div>
                  </div>
                ))}
              </div>

              {/* Note */}
              <p className="text-xs text-white/40 mt-4 text-center">
                This is a simulated example. Real calls sound even better!
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
