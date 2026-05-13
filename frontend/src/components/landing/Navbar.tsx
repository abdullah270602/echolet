import { Link } from 'react-router-dom';

export function Navbar() {
  return (
    <header>
      <nav
        aria-label="Main"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6"
      >
        <Link to="/" className="font-display font-wide text-xl font-extrabold tracking-[-0.02em] text-ink">
          echolet
        </Link>
        <div className="flex items-center gap-2 text-[15px] font-medium">
          <a
            href="#how-it-works"
            className="hidden min-h-11 items-center rounded-full px-4 text-ink transition-colors hover:bg-ink/5 sm:inline-flex"
          >
            How it works
          </a>
          <Link
            to="/sign-in"
            className="inline-flex min-h-11 items-center rounded-full border-2 border-ink px-5 text-ink transition-[background-color,color,transform] duration-200 hover:bg-ink hover:text-paper active:scale-[0.98]"
          >
            Sign in
          </Link>
        </div>
      </nav>
    </header>
  );
}
