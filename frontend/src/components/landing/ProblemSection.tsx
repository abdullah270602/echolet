import { motion } from 'framer-motion';
import { PhoneOff, DollarSign, RefreshCcw, TrendingDown } from 'lucide-react';
import { useInView } from '../../hooks';
import { Card } from '../ui';

const problems = [
  {
    icon: PhoneOff,
    title: 'Lost Leads',
    stat: '85%',
    description: 'of callers hang up on voicemail and call your competitor instead.',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
  },
  {
    icon: DollarSign,
    title: 'Expensive Humans',
    stat: '$400+',
    description: 'per month for answering services that just take a name and number.',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
  },
  {
    icon: RefreshCcw,
    title: 'Phone Tag',
    stat: '3.2 hrs',
    description: 'wasted weekly listening to rambling voicemails and playing callback.',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
  },
];

export function ProblemSection() {
  const [ref, isInView] = useInView({ threshold: 0.2 });

  return (
    <section
      ref={ref}
      id="problem"
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
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <span className="text-sm text-white/70">The Hidden Cost</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            The Hidden Cost of{' '}
            <span className="text-red-400">"Please Leave a Message"</span>
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            Every missed call is revenue walking out the door. Here's what "we'll call you back" really costs.
          </p>
        </motion.div>

        {/* Problem Cards */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {problems.map((problem, index) => (
            <motion.div
              key={problem.title}
              initial={{ opacity: 0, y: 40 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.2 + index * 0.15, duration: 0.6 }}
            >
              <Card
                hover
                className={`h-full p-6 lg:p-8 text-center ${problem.borderColor} border`}
              >
                {/* Icon */}
                <div
                  className={`w-16 h-16 mx-auto mb-6 rounded-2xl ${problem.bgColor} flex items-center justify-center`}
                >
                  <problem.icon className={`w-8 h-8 ${problem.color}`} />
                </div>

                {/* Stat */}
                <div className={`text-4xl lg:text-5xl font-bold mb-2 ${problem.color}`}>
                  {problem.stat}
                </div>

                {/* Title */}
                <h3 className="text-xl font-semibold mb-3 text-white">
                  {problem.title}
                </h3>

                {/* Description */}
                <p className="text-white/60 leading-relaxed">
                  {problem.description}
                </p>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Bottom stat */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-4 px-6 py-4 rounded-2xl glass">
            <div className="text-left">
              <div className="text-2xl font-bold text-white">
                $5,000 - $50,000+
              </div>
              <div className="text-sm text-white/60">
                Average annual revenue lost per small business to missed calls
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
