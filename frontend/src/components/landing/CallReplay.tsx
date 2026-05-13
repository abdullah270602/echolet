import { useEffect, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import { Typing } from './Typing';
import { showTicket } from './ticketEvents';

// A scripted call with the demo clinic (see backend/app/agent_templates/default.py),
// shown when the live demo is off or can't connect. It is labelled as scripted in the UI;
// it is not a recording and must not be presented as one.
const SCRIPT: { who: 'caller' | 'agent'; text: string }[] = [
  { who: 'agent', text: 'Hi, thanks for calling Brightside Dental, this is Emma. How can I help?' },
  { who: 'caller', text: "Hi, how much is a cleaning? I haven't been in a while." },
  { who: 'agent', text: 'A check-up and cleaning is $120 and takes about 45 minutes. Want me to set one up?' },
  { who: 'caller', text: 'Yeah, do you have anything Thursday afternoon?' },
  { who: 'agent', text: "I can't see the live calendar, but I'll note Thursday afternoon and the front desk will text you to confirm a time. Can I get your name and number?" },
  { who: 'caller', text: "It's Dana Reyes, 555 0142." },
  { who: 'agent', text: "Thanks Dana. That's a cleaning, Thursday afternoon, at 555 0142. Bring your insurance card if you have one. Anything else?" },
  { who: 'caller', text: "No, that's it. Thanks!" },
  { who: 'agent', text: 'Great, talk soon. Bye!' },
];

// Rough speaking pace so lines arrive roughly when they'd finish being said.
const delayFor = (text: string) => Math.min(4200, 700 + text.length * 38);

const pill =
  'inline-flex min-h-11 items-center rounded-full border-2 px-5 font-semibold transition-colors';
const link =
  'min-h-11 font-medium text-ink underline decoration-ink/40 underline-offset-4 transition-colors hover:decoration-ink';

export function CallReplay({ onClose }: { onClose?: () => void }) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(() => (reduce ? SCRIPT.length : 1));
  const [expanded, setExpanded] = useState(false);
  const done = shown >= SCRIPT.length;

  useEffect(() => {
    if (done) return;
    const id = setTimeout(() => setShown((n) => n + 1), delayFor(SCRIPT[shown - 1].text));
    return () => clearTimeout(id);
  }, [shown, done]);

  const next = SCRIPT[shown]?.who;

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p className="font-semibold text-ink" role="status">
          {done ? 'Call ended' : next === 'agent' ? 'Receptionist is speaking' : 'Caller is speaking'}
        </p>
        <p className="text-sm text-muted">Scripted example</p>
      </div>

      {/* Newest line sits at the bottom; older lines fade out at the top. No scrollbar. */}
      <ol
        aria-label="Example call transcript"
        aria-live="polite"
        className={
          expanded
            ? 'mt-4 space-y-3 text-[15px] leading-relaxed'
            : 'transcript-fade mt-4 flex h-64 flex-col justify-end gap-3 overflow-hidden text-[15px] leading-relaxed'
        }
      >
        {SCRIPT.slice(0, shown).map((line, i) => (
          <li key={i} className="line-in shrink-0">
            <span className={line.who === 'agent' ? 'font-semibold text-slip' : 'font-semibold text-ink'}>
              {line.who === 'agent' ? 'Receptionist' : 'Caller'}:{' '}
            </span>
            <span className="text-ink/85">{line.text}</span>
          </li>
        ))}
        {!done && (
          <li className="shrink-0 py-1">
            <Typing />
          </li>
        )}
      </ol>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
        {done ? (
          <>
            <button onClick={showTicket} className={pill + ' border-slip text-slip hover:bg-slip hover:text-[#131a4f]'}>
              See the ticket it wrote
            </button>
            <button
              onClick={() => {
                setExpanded(false);
                setShown(1);
              }}
              className={link}
            >
              Play again
            </button>
          </>
        ) : (
          <button
            onClick={() => {
              setShown(SCRIPT.length);
              setExpanded(true);
            }}
            className={pill + ' border-ink/70 text-ink hover:border-ink hover:bg-ink hover:text-paper'}
          >
            Show the whole call
          </button>
        )}
        {onClose && (
          <button onClick={onClose} className={link}>
            Back
          </button>
        )}
      </div>
    </div>
  );
}
