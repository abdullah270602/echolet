import { motion } from 'framer-motion';
import { ArrowRight, Zap, Shield, Clock } from 'lucide-react';
import { useInView } from '../../hooks';
import { Button } from '../ui';

export function CTAFooter() {
  const [ref, isInView] = useInView({ threshold: 0.2 });

  const features = [
    { icon: Zap, text: '5-minute setup' },
    { icon: Shield, text: 'No credit card required' },
    { icon: Clock, text: 'Free tier available' },
  ];

  return (
    <section ref={ref} className="py-20 md:py-32 relative overflow-hidden">
      {/* Animated background orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            x: [0, 100, 0],
            y: [0, -50, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -100, 0],
            y: [0, 50, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br from-teal-500/10 to-purple-500/10 rounded-full blur-3xl"
        />
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        {/* Heading */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6"
        >
          Ready to Stop Missing Business?
        </motion.h2>

        {/* Subheading */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.1, duration: 0.6 }}
          className="text-lg sm:text-xl text-white/60 mb-8 max-w-2xl mx-auto"
        >
          Join hundreds of businesses already converting missed calls into revenue.
          Start your free tier today.
        </motion.p>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="flex flex-wrap justify-center gap-6 mb-10"
        >
          {features.map((feature, index) => (
            <div
              key={index}
              className="flex items-center gap-2 text-white/60"
            >
              <feature.icon className="w-5 h-5 text-teal-400" />
              <span>{feature.text}</span>
            </div>
          ))}
        </motion.div>

        {/* CTA Button */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={isInView ? { opacity: 1, scale: 1 } : {}}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          <Button
            variant="glow"
            size="lg"
            className="text-lg px-10 py-5 animate-[pulse-glow_2s_ease-in-out_infinite] group"
          >
            Create My Agent Now
            <ArrowRight className="inline-block ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </motion.div>

        {/* Trust badge */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-8 text-sm text-white/40"
        >
          Trusted by 500+ small businesses across the US
        </motion.p>
      </div>

      {/* Footer */}
      <footer className="mt-24 md:mt-32 border-t border-white/10 pt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            {/* Logo */}
            <div className="text-white/50 text-sm">
              &copy; {new Date().getFullYear()} Echolet. All rights reserved.
            </div>

            {/* Links */}
            <div className="flex flex-wrap justify-center gap-6 text-sm text-white/60">
              <a href="#" className="hover:text-white transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Terms of Service
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Contact
              </a>
            </div>

            {/* Social/Contact */}
            <div className="text-sm text-white/50">
              hello@echolet.ai
            </div>
          </div>
        </div>
      </footer>
    </section>
  );
}
