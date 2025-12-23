import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import { HeroAnimation } from './HeroAnimation';
import { Button } from '../ui';

export function HeroSection() {
  const scrollToWaitlist = () => {
    const element = document.getElementById('waitlist');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="min-h-screen relative overflow-hidden pt-20 md:pt-0 flex items-center">
      {/* Background gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          className="absolute -top-40 -right-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -50, 0],
            y: [0, 30, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
          className="absolute -bottom-40 -left-40 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl"
        />
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-electric-blue/10 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: Content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="text-center lg:text-left"
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6"
            >
              <span className="w-2 h-2 bg-teal-400 rounded-full animate-pulse" />
              <span className="text-sm text-white/70">AI-Powered Voice Agent</span>
            </motion.div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold mb-6 leading-tight">
              Stop Losing Revenue to{' '}
              <span className="text-gradient">Missed Calls.</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg sm:text-xl text-white/70 mb-8 max-w-xl mx-auto lg:mx-0">
              Your 24/7 AI receptionist that answers with <em>your</em> knowledge and turns chaotic voicemails into organized, actionable tickets. Zero integrations required.
            </p>

            {/* CTAs */}
            <div className="flex flex-col gap-4 justify-center lg:justify-start">
              <Button
                variant="glow"
                size="lg"
                onClick={scrollToWaitlist}
                className="group"
              >
                <span className="inline-flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
                  Join the Waitlist
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </span>
              </Button>

              {/* Early access banner */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 w-fit mx-auto lg:mx-0"
              >
                <span className="text-sm text-purple-300">
                  First <span className="font-semibold text-purple-200">500</span> get early access + exclusive launch discount
                </span>
              </motion.div>
            </div>
          </motion.div>

          {/* Right: Animation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.7 }}
            className="relative"
          >
            <HeroAnimation />
          </motion.div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 hidden md:flex flex-col items-center gap-2"
      >
        <span className="text-xs text-white/40 uppercase tracking-widest">Scroll</span>
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-1"
        >
          <motion.div className="w-1.5 h-1.5 bg-white/40 rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  );
}
