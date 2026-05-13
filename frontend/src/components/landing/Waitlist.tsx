import { useId, useState, type FormEvent } from 'react';

// Same base as the other services; on Vercel this is the waitlist function.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

type Status =
  | { kind: 'idle' }
  | { kind: 'saving' }
  | { kind: 'done'; email: string }
  | { kind: 'error'; message: string; field?: 'name' | 'email' };

const input =
  'mt-2 block w-full min-h-12 border-0 border-b-2 border-ink bg-transparent px-0 text-lg text-ink placeholder:text-ink/45 focus:border-stamp focus:outline-none focus:ring-0';

export function Waitlist() {
  const id = useId();
  const [status, setStatus] = useState<Status>({ kind: 'idle' });

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const body = Object.fromEntries(form.entries());
    setStatus({ kind: 'saving' });
    try {
      const res = await fetch(`${API_BASE_URL}/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) return setStatus({ kind: 'done', email: String(body.email).trim() });
      setStatus({
        kind: 'error',
        message: data.error || "We couldn't save that. Try again in a minute.",
        field: data.field,
      });
    } catch {
      setStatus({ kind: 'error', message: "We couldn't reach the waitlist. Check your connection and try again." });
    }
  }

  if (status.kind === 'done') {
    return (
      <div role="status" className="self-end border-2 border-ink bg-white px-6 py-7">
        <p className="font-display font-wide text-2xl font-extrabold tracking-[-0.02em]">You're on the list.</p>
        <p className="mt-2 text-ink/80">We'll write to {status.email} when there's room.</p>
      </div>
    );
  }

  const err = status.kind === 'error' ? status : null;
  return (
    <form onSubmit={submit} noValidate className="self-end space-y-7">
      <div>
        <label htmlFor={`${id}-name`} className="text-[15px] font-semibold">
          Your name
        </label>
        <input
          id={`${id}-name`}
          name="name"
          autoComplete="name"
          required
          maxLength={100}
          placeholder="Dana Reyes"
          aria-invalid={err?.field === 'name' || undefined}
          aria-describedby={err ? `${id}-err` : undefined}
          className={input}
        />
      </div>
      <div>
        <label htmlFor={`${id}-email`} className="text-[15px] font-semibold">
          Work email
        </label>
        <input
          id={`${id}-email`}
          name="email"
          type="email"
          autoComplete="email"
          required
          maxLength={254}
          placeholder="dana@brightsidedental.com"
          aria-invalid={err?.field === 'email' || undefined}
          aria-describedby={err ? `${id}-err` : undefined}
          className={input}
        />
      </div>
      {/* Honeypot for bots; hidden from people and assistive tech. */}
      <input name="company" tabIndex={-1} autoComplete="off" aria-hidden="true" className="hidden" />
      {err && (
        <p id={`${id}-err`} role="alert" className="font-semibold text-stamp">
          {err.message}
        </p>
      )}
      <button
        type="submit"
        disabled={status.kind === 'saving'}
        className="inline-flex min-h-14 items-center rounded-full bg-ink px-8 text-lg font-semibold text-paper transition-[background-color,transform] duration-200 hover:bg-accent-dark active:scale-[0.98] disabled:cursor-wait disabled:opacity-70"
      >
        {status.kind === 'saving' ? 'Adding you…' : 'Join the waitlist'}
      </button>
    </form>
  );
}
