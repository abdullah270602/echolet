import { Logo } from './Logo';

const link =
  'hidden min-h-11 items-center rounded-full px-4 text-ink transition-colors hover:bg-ink/[0.06] md:inline-flex';

export function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b-2 border-ink bg-paper">
      <nav aria-label="Main" className="mx-auto flex h-[72px] max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <a href="#top" aria-label="Echolet, back to top" className="rounded-md">
          <Logo />
        </a>
        <div className="flex items-center gap-1 text-[15px] font-medium sm:gap-2">
          <a href="#message" className={link}>The ticket</a>
          <a href="#how-it-works" className={link}>How it works</a>
          <a
            href="#waitlist"
            className="ml-1 inline-flex min-h-11 items-center rounded-full bg-accent px-5 font-semibold text-white transition-[background-color,transform] duration-200 hover:bg-accent-dark active:scale-[0.98]"
          >
            Join the waitlist
          </a>
        </div>
      </nav>
    </header>
  );
}
