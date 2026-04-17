import { Navbar, LiveDemo, Setup, HowItWorks, SampleTicket, Footer } from '../components/landing';

export function LandingPage() {
  return (
    <div className="landing min-h-screen overflow-x-hidden bg-paper font-body text-ink">
      <Navbar />
      <main>
        <section className="mx-auto grid max-w-5xl items-start gap-10 px-4 pb-16 pt-12 sm:px-6 md:grid-cols-[1.1fr_1fr] md:gap-14 md:pt-20">
          <div>
            <h1 className="font-display text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              An AI receptionist that talks to your callers and writes up every call
            </h1>
            <p className="mt-6 max-w-prose text-lg leading-relaxed text-muted">
              Echolet is for dental clinics, salons, trades and other small businesses. You tell
              it your services, prices and rules. It talks to callers by voice, saves the
              transcript, and leaves a ticket with a summary and what needs doing next.
            </p>
            <p className="mt-4 max-w-prose text-muted">
              You can talk to a demo agent right now, no account needed.
            </p>
          </div>
          <LiveDemo />
        </section>

        <Setup />
        <HowItWorks />
        <SampleTicket />
      </main>
      <Footer />

    </div>
  );
}
