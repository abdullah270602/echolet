import { Link } from 'react-router-dom';

const setup = [
  ['Identity', 'Business name, the greeting, and how the agent should sound.'],
  ['Voice', 'Pick the voice callers will hear.'],
  ['Services', 'Each service with its price and how long it takes, so callers get real answers.'],
  ['Knowledge base', 'Paste in your hours, policies and FAQs. The agent answers from this text and says so when something is not covered.'],
  ['Guardrails', 'Topics the agent should not discuss or promise.'],
  ['Ticket fields', 'The details to collect on every call, such as name, number and reason for calling.'],
];

const steps = [
  ['You configure an agent', 'Fill in the settings above. You can test it from the dashboard before it takes real calls.'],
  ['A caller talks to it', 'The call runs over LiveKit. Speech is transcribed by Deepgram, replies come from Gemini through OpenRouter, and Inworld speaks them.'],
  ['The call is saved', 'The full transcript and the call details are stored against your agent.'],
  ['A ticket is written', 'After the call, a background worker produces a summary, the caller sentiment and a list of action items.'],
];

export function Setup() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto grid max-w-5xl gap-8 px-4 py-16 sm:px-6 md:grid-cols-[1fr_2fr] md:gap-16">
        <h2 className="font-display text-3xl font-bold leading-tight text-ink">
          You describe the business once
        </h2>
        <dl className="divide-y divide-rule border-y border-rule">
          {setup.map(([t, d]) => (
            <div key={t} className="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-6">
              <dt className="font-semibold text-ink">{t}</dt>
              <dd className="text-muted">{d}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-rule bg-white">
      <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
        <h2 className="font-display text-3xl font-bold text-ink">What happens on a call</h2>
        <ol className="mt-10 grid gap-x-10 gap-y-8 md:grid-cols-2">
          {steps.map(([t, d], i) => (
            <li key={t} className="border-t-2 border-ink pt-4">
              <p className="text-sm font-semibold text-accent">Step {i + 1}</p>
              <h3 className="mt-1 font-display text-xl font-semibold text-ink">{t}</h3>
              <p className="mt-2 max-w-prose text-muted">{d}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function SampleTicket() {
  return (
    <section id="sample-ticket" className="border-t border-rule">
      <div className="mx-auto grid max-w-5xl gap-8 px-4 py-16 sm:px-6 md:grid-cols-[1fr_1.4fr] md:gap-16">
        <div>
          <h2 className="font-display text-3xl font-bold leading-tight text-ink">
            The ticket you read afterwards
          </h2>
          <p className="mt-4 max-w-prose text-muted">
            Every call appears in your dashboard call history with its ticket and full
            transcript. This one is an invented example from the demo clinic.
          </p>
        </div>
        <article aria-label="Example ticket" className="border-2 border-ink bg-white p-5 sm:p-6">
          <p className="text-sm text-muted">Example, not a real call</p>
          <h3 className="mt-1 font-display text-xl font-semibold text-ink">
            Caller wants a cleaning and asked about price
          </h3>
          <dl className="mt-4 space-y-3 text-[15px]">
            <div>
              <dt className="font-semibold text-ink">Summary</dt>
              <dd className="text-muted">
                Caller asked how much a routine cleaning costs and how long it takes, then asked
                for a Thursday afternoon slot. Left a name and phone number.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Sentiment</dt>
              <dd className="text-muted">Positive</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Action items</dt>
              <dd>
                <ul className="list-disc pl-5 text-muted">
                  <li>Call back to confirm a Thursday afternoon cleaning</li>
                  <li>Ask whether the caller has insurance on file</li>
                </ul>
              </dd>
            </div>
          </dl>
        </article>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t-2 border-ink bg-ink text-paper">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-14 sm:px-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="font-display text-3xl font-bold">Set up your own receptionist</h2>
          <p className="mt-2 max-w-prose text-paper/80">
            Sign in, fill in your business details, and test the agent from your dashboard.
          </p>
        </div>
        <Link
          to="/sign-in"
          className="inline-flex min-h-11 shrink-0 items-center justify-center bg-paper px-6 font-semibold text-ink hover:bg-white focus-visible:outline-paper"
        >
          Sign in or create an account
        </Link>
      </div>
    </footer>
  );
}
