import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Sparkles, VolumeX, CheckCircle2, XCircle } from 'lucide-react';
import { TicketCard } from '../ui';
import { useInView } from '../../hooks';

export function FeatureSpotlight() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sectionRef, isInView] = useInView({ threshold: 0.2 });

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start end', 'end start'],
  });

  const leftScale = useTransform(scrollYProgress, [0.2, 0.5], [1, 0.9]);
  const leftOpacity = useTransform(scrollYProgress, [0.2, 0.5], [1, 0.3]);
  const rightScale = useTransform(scrollYProgress, [0.2, 0.5], [0.95, 1.02]);

  return (
    <section
      ref={sectionRef}
      id="feature-spotlight"
      className="py-20 md:py-32 relative overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-midnight-800/30 to-transparent" />

      <div ref={containerRef} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-white/70">The Ticket Engine</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            From Chaos to <span className="text-gradient">Clarity</span>
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            See the difference between drowning in voicemails and having AI-structured tickets
          </p>
        </motion.div>

        {/* Comparison */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-stretch">
          {/* Old Way */}
          <motion.div
            style={{ scale: leftScale, opacity: leftOpacity }}
            className="relative"
          >
            <div className="h-full glass rounded-2xl border border-red-500/20 overflow-hidden">
              {/* Header */}
              <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3">
                <XCircle className="w-5 h-5 text-red-400" />
                <span className="text-sm font-semibold text-red-400">The Old Way</span>
              </div>

              <div className="p-4 sm:p-6 lg:p-8">
                {/* Voicemail UI mock */}
                <div className="bg-midnight-900/50 rounded-xl p-3 sm:p-4 mb-4">
                  <div className="flex items-center gap-3 mb-3">
                    <VolumeX className="w-5 h-5 text-white/30" />
                    <div>
                      <div className="text-sm font-medium text-white/50">Unknown Caller</div>
                      <div className="text-xs text-white/30">2:43 long</div>
                    </div>
                  </div>

                  {/* Blurry waveform */}
                  <div className="h-16 flex items-center justify-center gap-0.5 sm:gap-1 blur-[1px] opacity-60 overflow-hidden">
                    {Array.from({ length: 30 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-0.5 sm:w-1 bg-gray-500 rounded-full flex-shrink-0"
                        style={{ height: `${Math.random() * 50 + 10}px` }}
                      />
                    ))}
                  </div>
                </div>

                {/* Garbled transcript */}
                <div className="space-y-2 sm:space-y-3 text-xs sm:text-sm text-white/40 italic">
                  <p>"Hi, uh... this is... *static* ...call me back..."</p>
                  <p>"...my number is five-five... *beep* ...Thursday..."</p>
                  <p>"...really urgent so... *muffled* ...thanks, bye."</p>
                </div>

                {/* Pain points */}
                <div className="mt-4 sm:mt-6 pt-4 border-t border-white/10 space-y-2">
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-red-400/70">
                    <XCircle className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                    <span>No caller name or context</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-red-400/70">
                    <XCircle className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                    <span>Can't tell if it's urgent</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-red-400/70">
                    <XCircle className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                    <span>Have to listen to entire message</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Echolet Way */}
          <motion.div
            style={{ scale: rightScale }}
            className="relative"
          >
            <motion.div
              animate={isInView ? {
                boxShadow: [
                  '0 0 0px rgba(94, 234, 212, 0)',
                  '0 0 30px rgba(94, 234, 212, 0.3)',
                  '0 0 0px rgba(94, 234, 212, 0)',
                ]
              } : {}}
              transition={{ duration: 3, repeat: Infinity }}
              className="h-full glass rounded-2xl border border-teal-500/30 overflow-hidden"
            >
              {/* Header */}
              <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-teal-400" />
                <span className="text-sm font-semibold text-teal-400">The Echolet Way</span>
              </div>

              <div className="p-4 sm:p-6 lg:p-8">
                {/* Ticket Card */}
                <TicketCard
                  caller="Sarah Johnson"
                  phone="(555) 123-4567"
                  time="Just now"
                  intent="Emergency Service"
                  summary="Kitchen sink leaking badly, water spreading. Needs emergency plumber dispatch ASAP. Available all day for service call."
                  priority="high"
                  className="border-0 bg-transparent p-0"
                />

                {/* Benefits */}
                <div className="mt-4 sm:mt-6 pt-4 border-t border-white/10 space-y-2">
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-teal-400/80">
                    <CheckCircle2 className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                    <span>Instant caller identification</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-teal-400/80">
                    <CheckCircle2 className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                    <span>AI-analyzed priority level</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-teal-400/80">
                    <CheckCircle2 className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                    <span>Actionable summary in seconds</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="mt-16 grid sm:grid-cols-3 gap-6"
        >
          {[
            { value: '90%', label: 'Less time managing calls' },
            { value: '3x', label: 'Faster response to urgent leads' },
            { value: '100%', label: 'Calls answered 24/7' },
          ].map((stat, index) => (
            <div
              key={index}
              className="text-center p-6 rounded-xl glass"
            >
              <div className="text-3xl lg:text-4xl font-bold text-gradient mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-white/60">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
