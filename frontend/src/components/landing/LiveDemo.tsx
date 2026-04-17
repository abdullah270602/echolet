import { lazy, Suspense, useCallback, useState } from 'react';
import { createDemoSession, DemoError, type DemoSession } from '../../services/demoApi';

const LiveDemoRoom = lazy(() => import('./LiveDemoRoom'));

type Phase =
  | { name: 'idle' }
  | { name: 'connecting'; step: 'mic' | 'server' }
  | { name: 'live'; session: DemoSession }
  | { name: 'ended' }
  | { name: 'error'; message: string };

const btn = 'min-h-11 bg-accent px-6 font-semibold text-white hover:bg-accent-dark';
const linkBtn = 'min-h-11 font-medium text-ink underline underline-offset-4 hover:text-accent';
const h = 'font-display text-2xl font-semibold text-ink';

export function LiveDemo() {
  const [phase, setPhase] = useState<Phase>({ name: 'idle' });

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
    <div className="border-2 border-ink bg-white p-5 sm:p-8" id="live-demo">
      {phase.name === 'idle' && (
        <div>
          <h2 className={h}>Call the demo receptionist</h2>
          <p className="mt-3 max-w-prose text-muted">
            You will talk to an agent that answers for a fictional dental clinic. Ask about
            cleanings, prices or opening hours, or try to book a visit.
          </p>
          <p className="mt-3 max-w-prose text-muted">
            This uses your microphone. Your browser will ask for permission first. Calls are
            time-limited and nothing is saved.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2">
            <button onClick={start} className={btn}>
              Start a call
            </button>
            <a href="#how-it-works" className={linkBtn + ' inline-flex items-center'}>
              See how it works
            </a>
          </div>
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
            <a href="#how-it-works" className={linkBtn + ' inline-flex items-center'}>
              See how it works
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
