import { Navbar, LiveDemo, Slips, Setup, CallPath, Closing } from '../components/landing';

export function LandingPage() {
  return (
    <div id="top" className="landing min-h-[100dvh] overflow-x-hidden bg-paper font-body text-ink antialiased">
      <Navbar />
      <main>
        <section className="mx-auto grid max-w-6xl items-start gap-12 px-4 pb-24 pt-16 sm:px-6 md:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)] md:gap-14 md:pb-28 md:pt-24">
          <div>
            <h1 className="font-display font-wide text-[clamp(2.9rem,7vw,5.25rem)] font-extrabold leading-[0.96] tracking-[-0.035em]">
              Picks up
              <br />
              when you can't.
            </h1>
            <p className="mt-8 max-w-[30ch] text-xl leading-relaxed text-muted sm:text-[1.4rem]">
              An AI receptionist for clinics, salons and trades. It answers callers, takes booking
              requests and writes up every call.
            </p>
          </div>
          <LiveDemo />
        </section>

        <Slips />
        <Setup />
        <CallPath />
        <Closing />
      </main>
    </div>
  );
}
