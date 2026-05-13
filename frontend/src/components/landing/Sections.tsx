import { motion, useReducedMotion, type Variants } from 'framer-motion';
import { Waitlist } from './Waitlist';

/* ------------------------------------------------------------------ */
/* The message slips: what a busy front desk writes vs what Echolet does */
/* ------------------------------------------------------------------ */

const scrawl = [
  ['For', 'Dr. Kapoor'],
  ['Caller', 'Dana? Deanna?'],
  ['Phone', '555 01'],
  ['Message', 'wants cleaning. thurs?? or tues. call back'],
] as const;

const ticket = [
  ['Taken', '11:42, by Echolet'],
  ['Caller', 'Dana Reyes'],
  ['Phone', '555 0142'],
  ['About', 'Check-up and cleaning, $120, 45 min'],
  ['Wants', 'Thursday afternoon'],
  ['Mood', 'Positive'],
  ['To do', 'Confirm a Thursday afternoon slot by text. Ask if she has insurance on file.'],
] as const;

function HandwrittenSlip() {
  return (
    <figure className="md:mt-10">
      <div className="-rotate-2 bg-slip px-6 pb-7 pt-5 shadow-[0_18px_40px_-22px_rgb(27_37_89/0.45)] sm:px-8">
        <p className="font-narrow text-lg font-extrabold uppercase sm:text-[22px] tracking-[0.02em] text-stamp">
          While you were out
        </p>
        <dl className="mt-3 space-y-0.5">
          {scrawl.map(([k, v]) => (
            <div key={k} className="flex items-baseline gap-3 border-b border-ink/25 pb-0.5 leading-8">
              <dt className="w-20 shrink-0 text-[13px] font-semibold text-ink/70">{k}</dt>
              <dd className="font-scrawl text-[27px] leading-8 text-ink">
                {k === 'Phone' ? (
                  <>
                    {v}
                    <span className="inline-block blur-[3px]">47</span>
                  </>
                ) : (
                  v
                )}
              </dd>
            </div>
          ))}
        </dl>
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-[13px] font-semibold text-ink/70">
          <span>
            <span className="font-scrawl mr-1 text-2xl text-ink">x</span>Please call
          </span>
          <span>Will call again</span>
          <span>Urgent</span>
        </div>
      </div>
      <figcaption className="mt-5 text-[15px] text-muted">Written between patients, at 11:40ish.</figcaption>
    </figure>
  );
}

function EcholetSlip() {
  const reduce = useReducedMotion();
  const line: Variants = {
    hidden: { opacity: 0, x: -6 },
    show: { opacity: 1, x: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] as const } },
  };
  return (
    <figure>
      <motion.div
        className="relative rotate-1 bg-white shadow-[0_24px_50px_-24px_rgb(27_37_89/0.5)]"
        initial={reduce ? false : 'hidden'}
        whileInView="show"
        viewport={{ once: true, amount: 0.5 }}
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.16, delayChildren: 0.15 } } }}
      >
        <div className="bg-slip px-6 pb-3 pt-4 sm:px-8">
          <p className="font-narrow text-lg font-extrabold uppercase sm:text-[22px] tracking-[0.02em] text-stamp">
            While you were out
          </p>
        </div>
        <dl className="px-6 pb-8 pt-4 sm:px-8">
          {ticket.map(([k, v]) => (
            <motion.div
              key={k}
              variants={line}
              className="grid grid-cols-[5rem_1fr] gap-3 border-b border-rule/70 py-2.5 last:border-0"
            >
              <dt className="text-[13px] font-semibold text-ink/70">{k}</dt>
              <dd className="font-medium leading-snug text-ink">{v}</dd>
            </motion.div>
          ))}
        </dl>
        <motion.p
          aria-label="Stamped: call back"
          className="font-narrow pointer-events-none absolute -top-5 right-3 rotate-[-10deg] sm:-right-5 border-[3px] border-stamp px-3 py-1 text-xl font-extrabold uppercase tracking-[0.04em] text-stamp opacity-90 sm:-right-6"
          variants={{
            hidden: { opacity: 0, scale: 1.6 },
            show: { opacity: 0.9, scale: 1, transition: { type: 'spring', stiffness: 420, damping: 18, delay: 0.2 } },
          }}
        >
          Call back
        </motion.p>
      </motion.div>
      <figcaption className="mt-5 text-[15px] text-muted">
        Written by Echolet as the call ends. An invented example from the demo clinic.
      </figcaption>
    </figure>
  );
}

export function Slips() {
  return (
    <section id="message" className="border-t-2 border-ink">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 md:py-28">
        <h2 className="max-w-[18ch] font-display font-wide text-[clamp(2rem,4.6vw,3.25rem)] font-extrabold leading-[1.02] tracking-[-0.03em] [text-wrap:balance]">
          The message, written down properly.
        </h2>
        <p className="mt-5 max-w-[56ch] text-lg leading-relaxed text-muted">
          Every call ends with a ticket in your call history: who called, what they want and
          what to do next, with the full transcript underneath.
        </p>
        <div className="mt-14 grid items-start gap-14 md:grid-cols-2 md:gap-16">
          <HandwrittenSlip />
          <EcholetSlip />
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Setup: what the owner configures                                     */
/* ------------------------------------------------------------------ */

const groups = [
  {
    title: 'What it knows',
    items: [
      ['Services and prices', 'Each service with its price and how long it takes.'],
      ['Hours and policies', 'Paste in your hours, FAQs and rules. It answers from that text and says so when something isn’t covered.'],
    ],
  },
  {
    title: 'How it sounds',
    items: [
      ['Name and greeting', 'Who answers, and the first thing callers hear.'],
      ['Voice', 'Pick the voice and speaking style.'],
    ],
  },
  {
    title: 'Where it stops',
    items: [
      ['Off-limits topics', 'Things it shouldn’t discuss or promise, like medical advice.'],
      ['Ticket fields', 'What to capture on every call: name, number, reason, urgency.'],
    ],
  },
] as const;

export function Setup() {
  return (
    <section className="bg-white">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.4fr)] md:gap-16 md:py-28">
        <div>
          <h2 className="font-display font-wide text-[clamp(2rem,4.2vw,3rem)] font-extrabold leading-[1.02] tracking-[-0.03em] [text-wrap:balance] md:sticky md:top-10">
            You describe the business once.
          </h2>
        </div>
        <div className="space-y-12">
          {groups.map((g) => (
            <div key={g.title}>
              <h3 className="font-display font-wide text-xl font-bold tracking-[-0.01em]">{g.title}</h3>
              <dl className="mt-5 grid gap-x-10 gap-y-6 sm:grid-cols-2">
                {g.items.map(([t, d]) => (
                  <div key={t} className="border-t-2 border-ink pt-3">
                    <dt className="font-semibold">{t}</dt>
                    <dd className="mt-1.5 leading-relaxed text-muted">{d}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Call path: the four things that happen, in order                    */
/* ------------------------------------------------------------------ */

const path = [
  ['You set it up', 'Fill in your details and test it from the dashboard before it takes real calls.'],
  ['A caller talks to it', 'Speech is transcribed by Deepgram, answered by Gemini and spoken by Inworld, over LiveKit.'],
  ['The call is saved', 'The transcript and call details are stored against your agent.'],
  ['A ticket is written', 'A background worker reads the transcript and writes the summary, mood and to-dos.'],
] as const;

export function CallPath() {
  return (
    <section id="how-it-works" className="scroll-mt-6">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 md:py-28">
        <h2 className="font-display font-wide text-[clamp(2rem,4.2vw,3rem)] font-extrabold leading-[1.02] tracking-[-0.03em]">
          What happens on a call.
        </h2>
        <ol className="relative mt-14 grid gap-10 md:grid-cols-4 md:gap-8">
          <span aria-hidden="true" className="absolute left-[9px] top-2 bottom-2 w-0.5 bg-ink md:left-0 md:right-0 md:top-[9px] md:bottom-auto md:h-0.5 md:w-auto" />
          {path.map(([t, d]) => (
            <li key={t} className="relative pl-10 md:pl-0 md:pt-10">
              <span aria-hidden="true" className="absolute left-0 top-0.5 h-5 w-5 rounded-full border-2 border-ink bg-slip md:top-0" />
              <h3 className="font-display font-wide text-lg font-bold leading-snug tracking-[-0.01em]">{t}</h3>
              <p className="mt-2 max-w-[32ch] leading-relaxed text-muted">{d}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Closing: waitlist on a slip-pink sheet                               */
/* ------------------------------------------------------------------ */

export function Closing() {
  return (
    <section id="waitlist" className="bg-slip">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 pb-10 pt-20 sm:px-6 md:grid-cols-2 md:gap-16 md:pt-28">
        <div>
          <h2 className="font-display font-wide text-[clamp(2.25rem,5vw,3.75rem)] font-extrabold leading-[0.98] tracking-[-0.035em] [text-wrap:balance]">
            Get on the list.
          </h2>
          <p className="mt-5 max-w-[40ch] text-lg leading-relaxed text-ink/80">
            Echolet is opening to businesses a few at a time. Leave your name and email and
            we'll write when there's room for yours.
          </p>
        </div>
        <Waitlist />
      </div>
      <footer className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 pb-10 pt-16 text-[15px] text-ink/80 sm:px-6">
        <span className="font-display font-wide font-extrabold text-ink">echolet</span>
        <span>© 2026 Echolet</span>
      </footer>
    </section>
  );
}
