/** Three dots that pulse in turn: someone is about to speak. Decorative. */
export function Typing({ className = '' }: { className?: string }) {
  return (
    <span className={`typing inline-flex items-center gap-1.5 ${className}`} aria-hidden="true">
      <span className="h-2 w-2 rounded-full bg-ink" />
      <span className="h-2 w-2 rounded-full bg-ink" />
      <span className="h-2 w-2 rounded-full bg-ink" />
    </span>
  );
}
