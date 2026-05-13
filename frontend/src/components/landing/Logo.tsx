// The waveform mark from echolet_logo.svg, redrawn as eight flat bars so it stays
// sharp, tiny (the source export is ~300 KB) and in the page's ink colour.
// Bar heights follow the original. Also used as the idle waveform in the demo panel.
export const BARS = [3, 7, 13, 11, 19, 13, 9, 5] as const;

export function LogoMark({ className = 'h-7 w-auto' }: { className?: string }) {
  return (
    <svg viewBox="0 0 44 24" className={className} fill="currentColor" aria-hidden="true">
      {BARS.map((h, i) => {
        const height = 4 + h;
        return <rect key={i} x={i * 5.5} y={(24 - height) / 2} width="3.2" height={height} rx="1.6" />;
      })}
    </svg>
  );
}

export function Logo() {
  return (
    <span className="inline-flex items-center gap-2.5 text-ink">
      <LogoMark />
      <span className="font-display font-wide text-2xl font-extrabold tracking-[-0.03em]">echolet</span>
    </span>
  );
}
