import { Navbar, LiveDemo, Slips, Setup, CallPath, Closing } from '../components/landing';

export function LandingPage() {
  return (
    <div className="landing min-h-[100dvh] overflow-x-hidden bg-paper font-body text-ink antialiased">
      <Navbar />
      <main>
        <section className="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6 md:pt-16">
          <h1 className="font-display font-wide text-[clamp(2.75rem,8.4vw,6rem)] font-extrabold leading-[0.95] tracking-[-0.035em] [text-wrap:balance]">
            Picks up when you can't.
          </h1>

          <div className="mt-10 grid items-start gap-10 md:mt-14 md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] md:gap-14">
            <div className="md:pt-2">
              <p className="max-w-[34ch] text-xl leading-relaxed text-muted sm:text-[1.4rem]">
                Echolet is an AI receptionist for clinics, salons and trades. It answers callers,
                books visits and writes up every call.
              </p>
              <p className="mt-8 max-w-[38ch] text-[15px] leading-relaxed text-muted">
                {import.meta.env.VITE_LIVE_DEMO !== 'false'
                  ? 'The demo line answers for a made-up dental clinic. It runs in your browser and needs no account.'
                  : 'The panel shows an example call with a made-up dental clinic. Sign in to set up and talk to your own receptionist.'}
              </p>
            </div>
            <LiveDemo />
          </div>
        </section>

        <Slips />
        <Setup />
        <CallPath />
        <Closing />
      </main>
    </div>
  );
}
