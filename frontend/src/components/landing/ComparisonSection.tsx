import { motion } from 'framer-motion';
import { X, Check, Phone, Clock, Brain, Zap, FileText, Users } from 'lucide-react';
import { useInView } from '../../hooks';

const oldWayItems = [
  {
    icon: Phone,
    title: 'Voicemail Black Hole',
    description: '85% of callers hang up and call your competitor instead.',
  },
  {
    icon: Clock,
    title: 'Delayed Response',
    description: 'Hours or days before you even hear the message.',
  },
  {
    icon: FileText,
    title: 'Manual Transcription',
    description: 'Listening to rambling messages, taking notes by hand.',
  },
  {
    icon: Users,
    title: 'Expensive Answering Services',
    description: '$400+/month just to take a name and number.',
  },
];

const newWayItems = [
  {
    icon: Brain,
    title: 'Intelligent Triage',
    description: 'AI understands context and routes calls appropriately.',
  },
  {
    icon: Zap,
    title: 'Instant Response',
    description: 'Every call answered on the first ring, 24/7.',
  },
  {
    icon: FileText,
    title: 'Auto-Generated Tickets',
    description: 'Structured summaries with action items, zero effort.',
  },
  {
    icon: Users,
    title: 'Scales Infinitely',
    description: 'Handle 1 or 1,000 calls simultaneously. Same cost.',
  },
];

export function ComparisonSection() {
  const [ref, isInView] = useInView({ threshold: 0.1 });

  return (
    <section
      ref={ref}
      id="comparison"
      className="py-20 md:py-32 relative overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-midnight-800/50 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Stop Playing Phone Tag.{' '}
            <span className="text-gradient">Start Closing Deals.</span>
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            See how Echolet transforms your call handling from a liability into a competitive advantage.
          </p>
        </motion.div>

        {/* Comparison Grid */}
        <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Old Way Column */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="relative"
          >
            {/* Column Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <X className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white/60">The Old Way</h3>
                <p className="text-sm text-white/40">Voicemail & Answering Services</p>
              </div>
            </div>

            {/* Old Way Cards */}
            <div className="space-y-4">
              {oldWayItems.map((item, index) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.3 + index * 0.1, duration: 0.5 }}
                  className="group relative p-5 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-red-500/20 transition-all duration-300"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-red-500/5 border border-red-500/10 flex items-center justify-center">
                      <item.icon className="w-5 h-5 text-red-400/60" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-white/50">{item.title}</h4>
                        <X className="w-4 h-4 text-red-400/40" />
                      </div>
                      <p className="text-sm text-white/30">{item.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* New Way Column */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="relative"
          >
            {/* Glow Effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-teal-500/10 via-purple-500/10 to-teal-500/10 rounded-3xl blur-2xl opacity-50" />

            {/* Column Header */}
            <div className="relative flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500/20 to-purple-500/20 border border-teal-500/30 flex items-center justify-center">
                <Check className="w-5 h-5 text-teal-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">The Echolet Way</h3>
                <p className="text-sm text-teal-400/70">AI-Powered Intelligence</p>
              </div>
            </div>

            {/* New Way Cards */}
            <div className="relative space-y-4">
              {newWayItems.map((item, index) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.4 + index * 0.1, duration: 0.5 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  className="group relative p-5 rounded-2xl glass border border-white/10 hover:border-teal-500/30 transition-all duration-300 cursor-default"
                >
                  {/* Card Glow on Hover */}
                  <motion.div
                    className="absolute inset-0 rounded-2xl bg-gradient-to-r from-teal-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  />

                  <div className="relative flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500/20 to-purple-500/20 border border-teal-500/20 flex items-center justify-center group-hover:border-teal-500/40 transition-colors">
                      <item.icon className="w-5 h-5 text-teal-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-white">{item.title}</h4>
                        <Check className="w-4 h-4 text-teal-400" />
                      </div>
                      <p className="text-sm text-white/60">{item.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.9, duration: 0.6 }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-3 px-6 py-4 rounded-2xl glass border border-teal-500/20">
            <div className="w-3 h-3 bg-teal-400 rounded-full animate-pulse" />
            <span className="text-white/80">
              Join <span className="font-semibold text-teal-400">500+</span> businesses already on the waitlist
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
