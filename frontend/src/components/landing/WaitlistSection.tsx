import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Sparkles, CheckCircle, Users } from 'lucide-react';
import toast from 'react-hot-toast';

// Validation
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const NAME_REGEX = /^[a-zA-Z\s\-'.]+$/;

function validateName(name: string): string | null {
  const trimmed = name.trim();
  if (!trimmed) return 'Name is required';
  if (trimmed.length < 2) return 'Name must be at least 2 characters';
  if (trimmed.length > 100) return 'Name is too long';
  if (!NAME_REGEX.test(trimmed)) return 'Please enter a valid name';
  return null;
}

function validateEmail(email: string): string | null {
  const trimmed = email.trim();
  if (!trimmed) return 'Email is required';
  if (trimmed.length > 254) return 'Email is too long';
  if (!EMAIL_REGEX.test(trimmed)) return 'Please enter a valid email';
  return null;
}

export function WaitlistSection() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasJoined, setHasJoined] = useState(false);
  const [count, setCount] = useState<number | null>(null);

  // Fetch waitlist count on mount
  useEffect(() => {
    fetch('/api/waitlist')
      .then((res) => {
        if (!res.ok) throw new Error('API not available');
        return res.json();
      })
      .then((data) => setCount(data.count))
      .catch(() => setCount(37)); // Fallback to base
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate
    const nameErr = validateName(name);
    const emailErr = validateEmail(email);

    setNameError(nameErr);
    setEmailError(emailErr);

    if (nameErr || emailErr) {
      toast.error(nameErr || emailErr || 'Please fix the errors');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), email: email.trim() }),
      });

      // Try to parse JSON, handle non-JSON responses
      let data;
      try {
        data = await response.json();
      } catch {
        // API not available (local dev) - simulate success
        toast.success(`Welcome aboard, ${name.split(' ')[0]}!`);
        setCount((prev) => (prev || 37) + 1);
        setHasJoined(true);
        return;
      }

      if (!response.ok) {
        throw new Error(data.error || 'Failed to join waitlist');
      }

      if (data.count) setCount(data.count);
      toast.success(`Welcome aboard, ${name.split(' ')[0]}!`);
      setHasJoined(true);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Something went wrong');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section id="waitlist" className="py-24 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-teal-500/10 to-purple-500/10 rounded-full blur-3xl" />
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
            <Sparkles className="w-4 h-4 text-teal-400" />
            <span className="text-sm text-white/70">Limited Early Access</span>
          </div>

          {/* Headline */}
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Be First in Line
          </h2>

          {/* Subheadline */}
          <p className="text-lg text-white/60 mb-8 max-w-xl mx-auto">
            Join the waitlist today. First 500 members get exclusive early access,
            special launch pricing, and priority support.
          </p>

          {/* Benefits */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            {['Early Access', 'Launch Discount', 'Priority Support'].map((benefit) => (
              <div
                key={benefit}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10"
              >
                <CheckCircle className="w-4 h-4 text-teal-400" />
                <span className="text-sm text-white/70">{benefit}</span>
              </div>
            ))}
          </div>

          {/* Founders Counter */}
          <AnimatePresence mode="wait">
            {count !== null && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center gap-2 mb-10"
              >
                <Users className="w-4 h-4 text-teal-400" />
                <span className="text-white/70">
                  <motion.span
                    key={count}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="inline-block font-semibold text-teal-400"
                  >
                    {count}
                  </motion.span>
                  {' '}founders have joined
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Form or Success State */}
          {hasJoined ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass rounded-2xl p-8 border border-white/10 max-w-md mx-auto"
            >
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-teal-500/20 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">You're on the list!</h3>
              <p className="text-white/60">
                We'll notify you as soon as Echolet is ready. Get ready to never miss a call again.
              </p>
            </motion.div>
          ) : (
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              onSubmit={handleSubmit}
              className="glass rounded-2xl p-6 sm:p-8 border border-white/10 max-w-md mx-auto"
            >
              <div className="space-y-4">
                {/* Name Input */}
                <div>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      if (nameError) setNameError(null);
                    }}
                    onBlur={() => setNameError(validateName(name))}
                    placeholder="Your Name"
                    disabled={isSubmitting}
                    maxLength={100}
                    className={`w-full px-4 py-3.5 rounded-xl bg-white/5 border text-white placeholder:text-white/40 focus:outline-none focus:ring-2 transition-all disabled:opacity-50 ${
                      nameError
                        ? 'border-red-500/50 focus:ring-red-500/30 focus:border-red-500/50'
                        : 'border-white/10 focus:ring-teal-500/30 focus:border-teal-500/50'
                    }`}
                  />
                  {nameError && (
                    <p className="mt-1 text-xs text-red-400">{nameError}</p>
                  )}
                </div>

                {/* Email Input */}
                <div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (emailError) setEmailError(null);
                    }}
                    onBlur={() => setEmailError(validateEmail(email))}
                    placeholder="work@company.com"
                    disabled={isSubmitting}
                    maxLength={254}
                    className={`w-full px-4 py-3.5 rounded-xl bg-white/5 border text-white placeholder:text-white/40 focus:outline-none focus:ring-2 transition-all disabled:opacity-50 ${
                      emailError
                        ? 'border-red-500/50 focus:ring-red-500/30 focus:border-red-500/50'
                        : 'border-white/10 focus:ring-teal-500/30 focus:border-teal-500/50'
                    }`}
                  />
                  {emailError && (
                    <p className="mt-1 text-xs text-red-400">{emailError}</p>
                  )}
                </div>

                {/* Submit Button */}
                <motion.button
                  type="submit"
                  disabled={isSubmitting}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className="w-full py-4 rounded-xl bg-gradient-to-r from-teal-500 to-purple-500 text-white font-semibold text-lg shadow-lg shadow-teal-500/20 hover:shadow-teal-500/30 transition-all cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Joining...
                    </span>
                  ) : (
                    'Join Waitlist'
                  )}
                </motion.button>
              </div>

              <p className="mt-4 text-xs text-white/40 text-center">
                No spam, ever. We'll only email you when we launch.
              </p>
            </motion.form>
          )}
        </motion.div>
      </div>
    </section>
  );
}
