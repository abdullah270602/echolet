import { Link } from 'react-router-dom';

export function Navbar() {
  return (
    <header className="border-b border-rule">
      <nav
        aria-label="Main"
        className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6"
      >
        <Link to="/" className="font-display text-xl font-bold text-ink">
          Echolet
        </Link>
        <div className="flex items-center gap-5 text-[15px]">
          <a href="#how-it-works" className="hidden min-h-11 items-center text-ink hover:text-accent sm:inline-flex">
            How it works
          </a>
          <Link to="/sign-in" className="inline-flex min-h-11 items-center font-medium text-ink underline underline-offset-4 hover:text-accent">
            Sign in
          </Link>
        </div>
      </nav>
    </header>
  );
}
