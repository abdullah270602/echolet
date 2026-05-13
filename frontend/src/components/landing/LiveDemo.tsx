import { lazy, Suspense, useCallback, useState } from 'react';
import { Phone } from 'lucide-react';
import { createDemoSession, DemoError, type DemoSession } from '../../services/demoApi';
import { CallReplay } from './CallReplay';

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

const btn =
  'inline-flex min-h-11 items-center gap-2 rounded-full bg-accent px-6 font-semibold text-white transition-[background-color,transform] duration-200 hover:bg-accent-dark active:scale-[0.98]';
const linkBtn =
  'min-h-11 font-medium text-ink underline decoration-ink/40 underline-offset-4 transition-colors hover:decoration-ink';
const h = 'font-display text-2xl font-bold tracking-[-0.01em] text-ink';

export function LiveDemo() {
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

  return (
    <div
      id="live-demo"
      className="line-panel rounded-[28px] p-6 shadow-[0_24px_60px_-28px_rgb(27_37_89/0.55)] sm:p-8"
    >
      <div className="mb-6 flex items-center justify-between gap-4 border-b border-rule pb-4">
        <p className="font-display font-wide font-bold tracking-[-0.01em]">
          Brightside Dental
          <span className="block font-body sm:ml-2 sm:inline text-sm font-normal [font-stretch:100%] text-muted">made-up clinic</span>
        </p>
        <p className="flex shrink-0 items-center gap-2 text-sm text-muted">
          <span
            aria-hidden="true"
            className={`h-2 w-2 rounded-full ${phase.name === 'live' ? 'animate-pulse bg-[#3ddc97]' : LIVE_DEMO ? 'bg-[#3ddc97]' : 'bg-muted/60'}`}
          />
          {phase.name === 'live' ? 'On a call' : LIVE_DEMO ? 'Line open' : 'Example call'}
        </p>
      </div>

      {phase.name === 'idle' && (
        <div>
          <h2 className={h}>Call the front desk</h2>
          <p className="mt-3 max-w-[46ch] leading-relaxed text-muted">
            Ask what a cleaning costs, whether they're open Saturday, or book a visit. It uses
            your microphone, lasts up to two minutes, and nothing is saved.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <button onClick={start} className={btn + ' min-h-14 px-7 text-lg'}>
              <Phone aria-hidden="true" className="h-5 w-5" strokeWidth={2} />
              Start a call
            </button>
            <button onClick={replay} className={linkBtn}>
              Watch an example call
            </button>
          </div>
        </div>
      )}

      {phase.name === 'replay' && (
        <div>
          <h2 className={h + ' mb-4'}>An example call</h2>
          <CallReplay onClose={LIVE_DEMO ? back : undefined} />
        </div>
      )}

      {phase.name === 'connecting' && (
        <div role="status" className="py-8">
          <p className={h}>
            {phase.step === 'mic' ? 'Waiting for microphone permission' : 'Connecting to the receptionist'}
          </p>
          <p className="mt-2 text-muted">
            {phase.step === 'mic' ? 'Choose Allow in the browser prompt.' : 'This takes a few seconds.'}
          </p>
        </div>
      )}

      {phase.name === 'live' && (
        <Suspense fallback={<p role="status" className="py-8 text-muted">Loading call</p>}>
          <LiveDemoRoom session={phase.session} onEnd={end} onError={fail} />
        </Suspense>
      )}

      {phase.name === 'ended' && (
        <div>
          <h2 className={h}>Call ended</h2>
          <p className="mt-3 max-w-prose text-muted">
            On a real account this call would now be saved with a transcript and a ticket holding
            a summary, sentiment and action items.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2">
            <button onClick={start} className={btn}>
              Call again
            </button>
            <a href="/sign-in" className={linkBtn + ' inline-flex items-center'}>
              Set up your own agent
            </a>
          </div>
        </div>
      )}

      {phase.name === 'error' && (
        <div role="alert">
          <h2 className={h}>The call did not start</h2>
          <p className="mt-3 max-w-prose text-ink">{phase.message}</p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2">
            <button onClick={start} className={btn}>
              Try again
            </button>
            <button onClick={replay} className={linkBtn}>
              Watch an example call instead
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
