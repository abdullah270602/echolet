import { useEffect, useRef, useState } from 'react';

// A scripted call with the demo clinic (see backend/app/agent_templates/default.py),
// shown when the live demo is off or can't connect. It is labelled as scripted in the UI;
// it is not a recording and must not be presented as one.
const SCRIPT: { who: 'caller' | 'agent'; text: string }[] = [
  { who: 'agent', text: 'Hi, thanks for calling Brightside Dental, this is Emma. How can I help?' },
  { who: 'caller', text: "Hi, how much is a cleaning? I haven't been in a while." },
  { who: 'agent', text: "A check-up and cleaning is $120 and takes about 45 minutes. Want me to set one up?" },
  { who: 'caller', text: 'Yeah, do you have anything Thursday afternoon?' },
  { who: 'agent', text: "I can't see the live calendar, but I'll note Thursday afternoon and the front desk will text you to confirm a time. Can I get your name and number?" },
  { who: 'caller', text: "It's Dana Reyes, 555 0142." },
  { who: 'agent', text: "Thanks Dana. That's a cleaning, Thursday afternoon, at 555 0142. Bring your insurance card if you have one. Anything else?" },
  { who: 'caller', text: "No, that's it. Thanks!" },
  { who: 'agent', text: 'Great, talk soon. Bye!' },
];

const reducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

// Rough speaking pace so lines arrive roughly when they'd finish being said.
const delayFor = (text: string) => Math.min(4200, 700 + text.length * 38);

export function CallReplay({ onClose }: { onClose?: () => void }) {
  const [shown, setShown] = useState(() => (reducedMotion() ? SCRIPT.length : 1));
  const logRef = useRef<HTMLOListElement>(null);
  const done = shown >= SCRIPT.length;

  useEffect(() => {
    if (done) return;
    const id = setTimeout(() => setShown((n) => n + 1), delayFor(SCRIPT[shown - 1].text));
    return () => clearTimeout(id);
  }, [shown, done]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [shown]);

  const next = SCRIPT[shown]?.who;

  return (
    <div>
      <div className="flex items-center justify-between gap-4 border-b border-rule pb-4">
        <p className="font-medium text-ink" role="status">
          {done ? 'Call ended' : next === 'agent' ? 'Receptionist is speaking' : 'Caller is speaking'}
        </p>
        <p className="text-sm text-muted">Scripted example, not a recording</p>
      </div>

      <ol
        ref={logRef}
        aria-label="Example call transcript"
        aria-live="polite"
        tabIndex={0}
        className="mt-4 h-64 space-y-3 overflow-y-auto text-[15px] leading-relaxed"
      >
        {SCRIPT.slice(0, shown).map((line, i) => (
          <li key={i}>
            <span className="font-semibold text-ink">
              {line.who === 'agent' ? 'Receptionist' : 'Caller'}:{' '}
            </span>
            <span className="text-ink/80">{line.text}</span>
          </li>
        ))}
      </ol>

      {done && (
        <p className="mt-4 border-t border-rule pt-4 text-muted">
          After a real call, the transcript is saved and a ticket like the{' '}
          <a href="#message" className="text-ink underline underline-offset-4 hover:text-accent">
            example below
          </a>{' '}
          appears in the call history.
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2">
        {done ? (
          <button
            onClick={() => setShown(1)}
            className="min-h-11 border-2 border-ink px-5 font-medium text-ink hover:bg-ink hover:text-paper"
          >
            Play again
          </button>
        ) : (
          <button
            onClick={() => setShown(SCRIPT.length)}
            className="min-h-11 border-2 border-ink px-5 font-medium text-ink hover:bg-ink hover:text-paper"
          >
            Show the whole call
          </button>
        )}
        {onClose && (
          <button onClick={onClose} className="min-h-11 font-medium text-ink underline underline-offset-4 hover:text-accent">
            Back
          </button>
        )}
      </div>
    </div>
  );
}
