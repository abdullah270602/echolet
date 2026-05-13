import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';
import { useInView } from 'framer-motion';
import { Waitlist } from './Waitlist';
import { LogoMark } from './Logo';
import { onShowTicket } from './ticketEvents';

/* ------------------------------------------------------------------ */
/* The message slips: what a busy front desk writes vs what Echolet does */
/* ------------------------------------------------------------------ */

const scrawl = [
  ['For', 'Dr. Kapoor'],
  ['Caller', 'Dana? Deanna?'],
  ['Phone', '555 01'],
  ['Message', 'cleaning. thurs?? call back'],
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
      <div className="-rotate-2 bg-slip px-6 pb-7 pt-5 shadow-[0_18px_40px_-22px_rgb(19_26_79/0.45)] sm:px-8">
        <p className="font-narrow text-lg font-extrabold uppercase sm:text-[22px] tracking-[0.02em] text-stamp">
          While you were out
        </p>
        <dl className="mt-3 space-y-0.5">
          {scrawl.map(([k, v]) => (
            <div key={k} className="flex items-baseline gap-3 border-b border-ink/25 pb-0.5 leading-8">
              <dt className="w-20 shrink-0 text-[13px] font-semibold text-ink/70">{k}</dt>
              <dd className="font-scrawl text-[23px] leading-8 text-ink sm:text-[27px]">
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
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.5 });
  // Remounting replays the write-in; triggered by "See the ticket it wrote" in the demo.
  const [run, setRun] = useState(0);
  useEffect(() => onShowTicket(() => setRun((n) => n + 1)), []);
  return (
    <figure>
      <div
        ref={ref}
        key={run}
        className={`relative rotate-1 bg-white shadow-[0_24px_50px_-24px_rgb(19_26_79/0.5)] ${inView ? 'write-in' : 'write-wait'}`}
      >
        <div className="bg-slip px-6 pb-3 pt-4 sm:px-8">
          <p className="font-narrow text-lg font-extrabold uppercase tracking-[0.02em] text-stamp sm:text-[22px]">
            While you were out
          </p>
        </div>
        <dl className="px-6 pb-8 pt-4 sm:px-8">
          {ticket.map(([k, v], i) => (
            <div
              key={k}
              style={{ '--i': i } as CSSProperties}
              className="write-line grid grid-cols-[5rem_1fr] gap-3 border-b border-rule/70 py-2.5 last:border-0"
            >
              <dt className="text-[13px] font-semibold text-ink/70">{k}</dt>
              <dd className="font-medium leading-snug text-ink">{v}</dd>
            </div>
          ))}
        </dl>
        <p
          aria-label="Stamped: call back"
          className="write-stamp font-narrow pointer-events-none absolute -top-5 right-3 rotate-[-10deg] border-[3px] border-stamp px-3 py-1 text-xl font-extrabold uppercase tracking-[0.04em] text-stamp opacity-90 sm:-right-6"
        >
          Call back
        </p>
      </div>
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
/* Setup: one filled-in sheet, using the demo clinic's real config      */
/* ------------------------------------------------------------------ */

const services = [
  ['Check-up and cleaning', '$120', '45 min'],
  ['Teeth whitening', '$300', '60 min'],
  ['Emergency visit', '$90 exam fee', '30 min'],
  ['New patient consultation', 'Free', '20 min'],
] as const;

function Field({ label, children, last = false }: { label: string; children: ReactNode; last?: boolean }) {
  return (
    <div className={`grid gap-1 py-4 sm:grid-cols-[9rem_1fr] sm:gap-6 ${last ? '' : 'border-b border-rule'}`}>
      <dt className="text-[13px] font-semibold text-muted sm:pt-0.5">{label}</dt>
      <dd className="leading-relaxed">{children}</dd>
    </div>
  );
}

export function Setup() {
  return (
    <section className="border-t-2 border-ink">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 md:grid-cols-[minmax(0,0.8fr)_minmax(0,1.3fr)] md:gap-16 md:py-28">
        <div>
          <h2 className="font-display font-wide text-[clamp(2rem,4.2vw,3rem)] font-extrabold leading-[1.02] tracking-[-0.03em] [text-wrap:balance] md:sticky md:top-28">
            You describe the business once.
          </h2>
          <p className="mt-5 max-w-[34ch] text-lg leading-relaxed text-muted">
            This is the setup behind the demo line. Yours would have your own services, prices and
            rules.
          </p>
        </div>
        <article
          aria-label="Setup for the demo clinic"
          className="bg-white px-6 py-2 shadow-[0_24px_50px_-30px_rgb(19_26_79/0.45)] sm:px-8"
        >
          <dl>
            <Field label="Answers as">Emma at Brightside Dental</Field>
            <Field label="Greeting">"Hi, thanks for calling Brightside Dental, this is Emma. How can I help?"</Field>
            <Field label="Services">
              <ul className="space-y-1">
                {services.map(([name, price, time]) => (
                  <li key={name} className="flex items-baseline justify-between gap-4">
                    <span>{name}</span>
                    <span className="shrink-0 tabular-nums">
                      {price} <span className="text-muted">{time}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </Field>
            <Field label="Knows">Hours, insurance, parking, cancellations, and what counts as a dental emergency.</Field>
            <Field label="Never discusses">Medical diagnosis or medication advice.</Field>
            <Field label="Every ticket has" last>
              <span className="flex flex-wrap gap-2">
                {['Name', 'Phone', 'Reason', 'Priority', 'Mood', 'To-dos'].map((t) => (
                  <span key={t} className="rounded-full bg-slip px-3 py-1 text-sm font-semibold">
                    {t}
                  </span>
                ))}
              </span>
            </Field>
          </dl>
        </article>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Call path: what happens, in order                                    */
/* ------------------------------------------------------------------ */

const path = [
  ['The caller is answered', 'Your receptionist picks up, answers from your setup and takes down what they need.'],
  ['The call is written down', 'Every word is saved as a transcript, so nothing depends on memory.'],
  ['A ticket lands in your history', 'Who called, what they want, how it went and what to do next. Ready between appointments.'],
] as const;

export function CallPath() {
  return (
    <section id="how-it-works" className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 md:py-28">
        <h2 className="font-display font-wide text-[clamp(2rem,4.2vw,3rem)] font-extrabold leading-[1.02] tracking-[-0.03em]">
          What happens on a call.
        </h2>
        <ol className="relative mt-14 grid gap-10 md:grid-cols-3">
          <span
            aria-hidden="true"
            className="absolute bottom-2 left-[9px] top-2 w-0.5 bg-ink md:bottom-auto md:left-0 md:right-0 md:top-[9px] md:h-0.5 md:w-auto"
          />
          {path.map(([t, d]) => (
            <li key={t} className="relative pl-10 md:pl-0 md:pt-10">
              <span aria-hidden="true" className="absolute left-0 top-0.5 h-5 w-5 rounded-full border-2 border-ink bg-slip md:top-0" />
              <h3 className="font-display font-wide text-lg font-bold leading-snug tracking-[-0.01em]">{t}</h3>
              <p className="mt-2 max-w-[34ch] leading-relaxed text-muted">{d}</p>
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
    <section id="waitlist" className="border-t-2 border-ink bg-slip">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 pb-16 pt-20 sm:px-6 md:grid-cols-2 md:gap-16 md:pt-28">
        <div>
          <h2 className="font-display font-wide text-[clamp(2.25rem,5vw,3.75rem)] font-extrabold leading-[0.98] tracking-[-0.035em] [text-wrap:balance]">
            Get on the list.
          </h2>
          <p className="mt-5 max-w-[38ch] text-lg leading-relaxed text-ink/80">
            Echolet is still being built. Leave your name and email and we'll write when it's ready
            to try with your own business.
          </p>
        </div>
        <Waitlist />
      </div>
      <footer className="border-t-2 border-ink">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 text-[15px] text-ink/80 sm:px-6">
          <span className="inline-flex items-center gap-2.5 text-ink">
            <LogoMark className="h-5 w-auto text-accent" />
            <span className="font-display font-wide font-extrabold">echolet</span>
          </span>
          <span className="flex flex-wrap items-center gap-x-6 gap-y-2">
            <a
              href="mailto:abdullah@echolet.xyz"
              className="font-semibold text-ink underline decoration-ink/40 underline-offset-4 transition-colors hover:decoration-ink"
            >
              abdullah@echolet.xyz
            </a>
            <span>© 2026 Echolet</span>
          </span>
        </div>
      </footer>
    </section>
  );
}
