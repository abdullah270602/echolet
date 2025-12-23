import { motion } from 'framer-motion';
import { FileText, Settings, Zap, CheckCircle2 } from 'lucide-react';
import { useInView } from '../../hooks';

const steps = [
  {
    icon: FileText,
    title: 'Upload Your Brain',
    description: 'Drop in your pricing, FAQs, or policy docs. Our AI learns your business in seconds.',
    details: ['PDFs, Word docs, websites', 'Learns your pricing & policies', 'Understands your services'],
  },
  {
    icon: Settings,
    title: 'Define Your Rules',
    description: 'Tell the AI how to behave. "Be friendly, mark urgent calls as High Priority."',
    details: ['Custom greeting scripts', 'Priority rules & escalation', 'Personality & tone settings'],
  },
  {
    icon: Zap,
    title: 'Go Live',
    description: 'Forward missed calls to your Echolet number. Start getting tickets, not voicemails.',
    details: ['30-second phone setup', 'Works with any phone system', 'Instant ticket notifications'],
  },
];

export function SolutionSection() {
  const [sectionRef, isInView] = useInView({ threshold: 0.1 });

  return (
    <section
      ref={sectionRef}
      id="solution"
      className="py-20 md:py-32 relative overflow-hidden"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16 md:mb-24"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
            <Zap className="w-4 h-4 text-teal-400" />
            <span className="text-sm text-white/70">Quick Setup</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Setup in <span className="text-gradient">5 Minutes</span>. No Coding.
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            Three simple steps to never miss a call again
          </p>
        </motion.div>

        {/* Steps */}
        <div className="grid lg:grid-cols-3 gap-8 lg:gap-12">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 + index * 0.2, duration: 0.6 }}
              className="text-center"
            >
              {/* Step number & icon */}
              <div className="relative inline-flex flex-col items-center mb-6">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl glass border-2 border-teal-500/30 flex items-center justify-center mb-3 relative">
                  <step.icon className="w-8 h-8 sm:w-10 sm:h-10 text-teal-400" />
                  {/* Glow effect */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={isInView ? { opacity: [0, 0.5, 0] } : {}}
                    transition={{ delay: 0.5 + index * 0.3, duration: 2, repeat: Infinity }}
                    className="absolute inset-0 bg-teal-400/20 rounded-2xl blur-xl"
                  />
                </div>
                <div className="text-sm font-semibold text-teal-400">
                  Step {index + 1}
                </div>
              </div>

              {/* Content */}
              <h3 className="text-xl lg:text-2xl font-semibold mb-3 text-white">
                {step.title}
              </h3>
              <p className="text-white/60 mb-6 max-w-sm mx-auto">
                {step.description}
              </p>

              {/* Details */}
              <ul className="space-y-2">
                {step.details.map((detail, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-2 text-sm text-white/50 justify-center"
                  >
                    <CheckCircle2 className="w-4 h-4 text-teal-400/70 flex-shrink-0" />
                    {detail}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA hint */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 1, duration: 0.6 }}
          className="mt-16 text-center"
        >
          <p className="text-white/50 text-sm">
            Most businesses are up and running in under 5 minutes
          </p>
        </motion.div>
      </div>
    </section>
  );
}
