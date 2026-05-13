import { lazy, Suspense, useCallback, useState, type ReactNode } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { Phone } from 'lucide-react';
import { createDemoSession, DemoError, type DemoSession } from '../../services/demoApi';
import { CallReplay } from './CallReplay';
import { BARS } from './Logo';
import { Typing } from './Typing';

// Set VITE_LIVE_DEMO=false to build a landing page that only offers the scripted
// replay, e.g. when the backend/agent is not deployed.
const LIVE_DEMO = import.meta.env.VITE_LIVE_DEMO !== 'false';

const LiveDemoRoom = lazy(() => import('./LiveDemoRoom'));

type Phase =
  | { name: 'idle' }
  | { name: 'replay' }
  | { name: 'connecting'; step: 'mic' | 'server' }
  | { name: 'live'; session: DemoSession }
  | { name: 'ended' }
  | { name: 'error'; message: string };

const callBtn =
  'inline-flex items-center gap-2.5 rounded-full bg-[#3ddc97] font-bold text-[#0f1638] transition-[background-color,transform] duration-200 hover:bg-[#62e6ad] active:scale-[0.98]';
const ghostBtn =
  'inline-flex min-h-11 items-center rounded-full border-2 border-ink/70 px-5 font-semibold text-ink transition-colors hover:border-ink hover:bg-ink hover:text-paper';
const linkBtn =
  'min-h-11 font-medium text-ink underline decoration-ink/40 underline-offset-4 transition-colors hover:decoration-ink';
const h = 'font-display font-wide text-2xl font-extrabold tracking-[-0.02em] text-ink';

function IdleWave() {
  return (
    <svg viewBox="0 0 44 24" className="breathe h-14 w-auto text-slip" fill="currentColor" aria-hidden="true">
      {BARS.map((b, i) => {
        const height = 4 + b;
        return <rect key={i} x={i * 5.5} y={(24 - height) / 2} width="3.2" height={height} rx="1.6" />;
      })}
    </svg>
  );
}

/** A slip from the message pad, tucked behind the phone. Decorative. */
function PeekingSlip() {
  return (
    <div
      aria-hidden="true"
      className="absolute -right-2 -top-[4.5rem] w-52 rotate-[7deg] bg-slip px-4 pb-8 pt-3 shadow-[0_14px_30px_-18px_rgb(27_37_89/0.6)] sm:-right-6 sm:w-60"
    >
      <p className="font-narrow text-sm font-extrabold uppercase text-stamp">While you were out</p>
      <p className="font-scrawl mt-1 text-2xl leading-6 text-ink">Dana called, 11:42</p>
    </div>
  );
}

export function LiveDemo() {
  const reduce = useReducedMotion();
  const [phase, setPhase] = useState<Phase>(LIVE_DEMO ? { name: 'idle' } : { name: 'replay' });
  const replay = useCallback(() => setPhase({ name: 'replay' }), []);
  const back = useCallback(() => setPhase({ name: 'idle' }), []);

  const start = useCallback(async () => {
    setPhase({ name: 'connecting', step: 'mic' });
    try {
      // Ask for the mic first so a denial is reported before a demo session is used.
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
    } catch {
      setPhase({
        name: 'error',
        message:
          'Microphone access was blocked or no microphone was found. Allow the microphone for this site in your browser settings, then try again.',
      });
      return;
    }
    setPhase({ name: 'connecting', step: 'server' });
    try {
      setPhase({ name: 'live', session: await createDemoSession() });
    } catch (e) {
      setPhase({
        name: 'error',
        message: e instanceof DemoError ? e.message : 'The demo could not start.',
      });
    }
  }, []);

  const end = useCallback(() => setPhase((p) => (p.name === 'live' ? { name: 'ended' } : p)), []);
  const fail = useCallback(
    () => setPhase({ name: 'error', message: 'The connection dropped. Try the call again.' }),
    []
  );

  const status =
    phase.name === 'live' ? 'On a call' : phase.name === 'replay' ? 'Example call' : 'Demo line';

  let body: ReactNode;
  switch (phase.name) {
    case 'idle':
      body = (
        <div className="flex h-full flex-col">
          <IdleWave />
          <h2 className={h + ' mt-6'}>Call the front desk</h2>
          <p className="mt-3 max-w-[44ch] leading-relaxed text-muted">
            Ask what a cleaning costs, whether they're open Saturday, or ask for an appointment.
            Uses your microphone, up to two minutes, nothing is saved.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <button onClick={start} className={callBtn + ' min-h-16 px-8 text-lg'}>
              <Phone aria-hidden="true" className="ringing h-5 w-5" strokeWidth={2.25} />
              Start a call
            </button>
            <button onClick={replay} className={linkBtn}>
              Watch an example call
            </button>
          </div>
        </div>
      );
      break;
    case 'replay':
      body = <CallReplay onClose={LIVE_DEMO ? back : undefined} />;
      break;
    case 'connecting':
      body = (
        <div role="status" className="py-6">
          <p className={h}>
            {phase.step === 'mic' ? 'Waiting for your microphone' : 'Ringing the front desk'}
          </p>
          <p className="mt-2 text-muted">
            {phase.step === 'mic' ? 'Choose Allow in the browser prompt.' : 'This takes a few seconds.'}
          </p>
          <Typing className="mt-6" />
        </div>
      );
      break;
    case 'live':
      body = (
        <Suspense fallback={<p role="status" className="py-6 text-muted">Loading the call</p>}>
          <LiveDemoRoom session={phase.session} onEnd={end} onError={fail} />
        </Suspense>
      );
      break;
    case 'ended':
      body = (
        <div>
          <h2 className={h}>Call ended</h2>
          <p className="mt-3 max-w-[44ch] leading-relaxed text-muted">
            For a real business, this call would be saved with its transcript, and a ticket would
            land in the call history.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
            <button onClick={start} className={callBtn + ' min-h-12 px-6'}>
              <Phone aria-hidden="true" className="h-4 w-4" strokeWidth={2.25} />
              Call again
            </button>
            <a href="#waitlist" className={linkBtn + ' inline-flex items-center'}>
              Join the waitlist
            </a>
          </div>
        </div>
      );
      break;
    case 'error':
      body = (
        <div role="alert">
          <h2 className={h}>The call didn't connect</h2>
          <p className="mt-3 max-w-[44ch] leading-relaxed text-ink">{phase.message}</p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
            <button onClick={start} className={ghostBtn}>
              Try again
            </button>
            <button onClick={replay} className={linkBtn}>
              Watch an example call instead
            </button>
          </div>
        </div>
      );
      break;
  }

  return (
    <div className="relative mt-10 md:mt-0">
      <PeekingSlip />
      <div
        id="live-demo"
        className="line-panel relative flex min-h-[420px] flex-col rounded-[28px] p-6 shadow-[0_28px_60px_-28px_rgb(27_37_89/0.65)] sm:p-8"
      >
        <div className="mb-6 flex items-center justify-between gap-4 border-b border-rule pb-4">
          <p className="font-display font-wide font-bold tracking-[-0.01em]">
            Brightside Dental
            <span className="block text-sm font-normal text-muted [font-stretch:100%] sm:ml-2 sm:inline">made-up clinic</span>
          </p>
          <p className="flex shrink-0 items-center gap-2 text-sm text-muted">
            {phase.name === 'live' && (
              <span aria-hidden="true" className="h-2 w-2 animate-pulse rounded-full bg-[#3ddc97]" />
            )}
            {status}
          </p>
        </div>

        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={phase.name === 'connecting' ? `connecting-${phase.step}` : phase.name}
            className="flex-1"
            initial={reduce ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduce ? undefined : { opacity: 0, y: -6 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
          >
            {body}
          </motion.div>
        </AnimatePresence>

        <p className="mt-6 border-t border-rule pt-4 text-sm text-muted">
          {LIVE_DEMO
            ? 'Answers for a made-up dental clinic. Runs in your browser, no account needed.'
            : 'An example call with a made-up dental clinic.'}
        </p>
      </div>
    </div>
  );
}
