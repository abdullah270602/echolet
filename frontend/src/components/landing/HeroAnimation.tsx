import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone } from 'lucide-react';
import { GlowingOrb, TicketCard } from '../ui';

type Phase = 'ringing' | 'processing' | 'ticket' | 'reset';

export function HeroAnimation() {
  const [phase, setPhase] = useState<Phase>('ringing');

  useEffect(() => {
    const sequence = [
      { phase: 'ringing' as Phase, duration: 2500 },
      { phase: 'processing' as Phase, duration: 2000 },
      { phase: 'ticket' as Phase, duration: 3000 },
      { phase: 'reset' as Phase, duration: 500 },
    ];

    let timeoutId: number;
    let currentIndex = 0;

    const runSequence = () => {
      const { phase, duration } = sequence[currentIndex];
      setPhase(phase);

      timeoutId = window.setTimeout(() => {
        currentIndex = (currentIndex + 1) % sequence.length;
        runSequence();
      }, duration);
    };

    runSequence();
    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="relative w-full aspect-square max-w-[280px] sm:max-w-sm md:max-w-md mx-auto flex items-center justify-center">
      {/* Background glow */}
      <div className="absolute inset-0 bg-gradient-to-br from-teal-500/10 via-transparent to-purple-500/10 rounded-full blur-3xl" />

      {/* Chaotic waves - behind phone */}
      <AnimatePresence>
        {phase === 'ringing' && <ChaoticWaves />}
      </AnimatePresence>

      {/* Phone icon */}
      <AnimatePresence mode="wait">
        {(phase === 'ringing' || phase === 'reset') && (
          <motion.div
            key="phone"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{
              opacity: 1,
              scale: 1,
              rotate: phase === 'ringing' ? [0, -8, 8, -8, 8, 0] : 0,
            }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{
              rotate: { repeat: Infinity, duration: 0.5 },
              opacity: { duration: 0.3 },
              scale: { duration: 0.3 },
            }}
            className="absolute flex items-center justify-center"
          >
            <div className="relative">
              {/* Phone glow */}
              <motion.div
                animate={{ opacity: [0.3, 0.6, 0.3] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="absolute inset-0 bg-amber-400/30 rounded-full blur-2xl scale-150"
              />
              <div className="w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 rounded-2xl bg-gradient-to-br from-amber-400 to-red-500 flex items-center justify-center shadow-lg">
                <Phone className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-white" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Waves being sucked into orb */}
      <AnimatePresence>
        {phase === 'processing' && <AbsorbingWaves />}
      </AnimatePresence>

      {/* Processing orb */}
      <AnimatePresence mode="wait">
        {phase === 'processing' && (
          <motion.div
            key="orb"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.5 }}
            className="absolute flex items-center justify-center"
          >
            <GlowingOrb size="lg" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ticket card */}
      <AnimatePresence mode="wait">
        {phase === 'ticket' && (
          <motion.div
            key="ticket"
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -10 }}
            transition={{
              type: 'spring',
              stiffness: 200,
              damping: 20,
            }}
            className="absolute"
          >
            <motion.div
              animate={{
                boxShadow: [
                  '0 0 20px rgba(94, 234, 212, 0.3)',
                  '0 0 40px rgba(94, 234, 212, 0.5)',
                  '0 0 20px rgba(94, 234, 212, 0.3)',
                ]
              }}
              transition={{ duration: 2, repeat: Infinity }}
              className="rounded-2xl"
            >
              <TicketCard compact />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Chaotic waves emanating from phone
function ChaoticWaves() {
  const waveCount = 8;

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      {Array.from({ length: waveCount }).map((_, i) => {
        const angle = (i / waveCount) * 360;
        const delay = i * 0.1;
        const length = 60 + Math.random() * 40;

        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, scaleX: 0 }}
            animate={{
              opacity: [0, 0.8, 0],
              scaleX: [0, 1, 1.2],
              x: [0, Math.cos((angle * Math.PI) / 180) * length],
              y: [0, Math.sin((angle * Math.PI) / 180) * length],
            }}
            exit={{ opacity: 0, scaleX: 0 }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              delay,
              ease: 'easeOut',
            }}
            style={{
              position: 'absolute',
              width: '40px',
              height: '4px',
              background: `linear-gradient(90deg, transparent, ${
                i % 2 === 0 ? '#fbbf24' : '#f97316'
              })`,
              borderRadius: '2px',
              transformOrigin: 'left center',
              rotate: `${angle}deg`,
            }}
          />
        );
      })}
    </div>
  );
}

// Waves being absorbed into the orb
function AbsorbingWaves() {
  const waveCount = 6;

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      {Array.from({ length: waveCount }).map((_, i) => {
        const angle = (i / waveCount) * 360;
        const startDistance = 120;

        return (
          <motion.div
            key={i}
            initial={{
              opacity: 0.8,
              x: Math.cos((angle * Math.PI) / 180) * startDistance,
              y: Math.sin((angle * Math.PI) / 180) * startDistance,
              scale: 1,
            }}
            animate={{
              opacity: 0,
              x: 0,
              y: 0,
              scale: 0,
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: i * 0.2,
              ease: 'easeIn',
            }}
            style={{
              position: 'absolute',
              width: '12px',
              height: '12px',
              background: `linear-gradient(135deg, #14b8a6, #8b5cf6)`,
              borderRadius: '50%',
              boxShadow: '0 0 10px rgba(94, 234, 212, 0.5)',
            }}
          />
        );
      })}
    </div>
  );
}
