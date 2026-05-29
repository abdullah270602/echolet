import type { CSSProperties } from 'react';
import type { SlipRows } from './ticket';

/**
 * The yellow "While you were out" slip. Used for the example ticket on the page and
 * for the visitor's own ticket after a demo call, so the two always look the same.
 * `waiting` hides the lines until `animate` starts the write-in.
 */
export function TicketSlip({
  rows,
  animate,
  waiting = false,
  className = '',
}: {
  rows: SlipRows;
  animate: boolean;
  waiting?: boolean;
  className?: string;
}) {
  const motion = animate ? 'write-in' : waiting ? 'write-wait' : '';
  return (
    <div
      className={`relative rotate-1 bg-white [--color-ink:#131a4f] [--color-rule:#c5cdea] shadow-[0_24px_50px_-24px_rgb(19_26_79/0.5)] ${motion} ${className}`}
    >
      <div className="bg-slip px-6 pb-3 pt-4 sm:px-8">
        <p className="font-narrow text-lg font-extrabold uppercase tracking-[0.02em] text-stamp sm:text-[22px]">
          While you were out
        </p>
      </div>
      <dl className="px-6 pb-8 pt-4 sm:px-8">
        {rows.map(([k, v], i) => (
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
  );
}
