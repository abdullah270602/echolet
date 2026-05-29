// The ticket Emma writes for the visitor's own call, as returned by the agent's
// `echolet.ticket` RPC method (see agent/demo_ticket.py).
export interface Ticket {
  caller: string | null;
  phone: string | null;
  about: string | null;
  wants: string | null;
  mood: string | null;
  todo: string[];
  summary: string | null;
}

export type SlipRows = readonly (readonly [string, string])[];

const str = (v: unknown) => (typeof v === 'string' && v.trim() ? v.trim() : null);

/** Validate the RPC reply. Returns null if it is an error or not a ticket. */
export function parseTicket(raw: string): Ticket | null {
  try {
    const d = JSON.parse(raw);
    if (!d || typeof d !== 'object' || 'error' in d) return null;
    return {
      caller: str(d.caller),
      phone: str(d.phone),
      about: str(d.about),
      wants: str(d.wants),
      mood: str(d.mood),
      todo: Array.isArray(d.todo) ? (d.todo as unknown[]).map(str).filter((t): t is string => !!t).slice(0, 3) : [],
      summary: str(d.summary),
    };
  } catch {
    return null;
  }
}

/** True when the caller gave us nothing worth writing on a slip. */
export const isBlank = (t: Ticket) => !t.caller && !t.phone && !t.about && !t.wants && !t.todo.length;

const NOT_GIVEN = 'Not given';

export function ticketRows(t: Ticket, takenAt = new Date()): SlipRows {
  const time = takenAt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return [
    ['Taken', `${time}, by Echolet`],
    ['Caller', t.caller ?? NOT_GIVEN],
    ['Phone', t.phone ?? NOT_GIVEN],
    ['About', t.about ?? NOT_GIVEN],
    ['Wants', t.wants ?? NOT_GIVEN],
    ['Mood', t.mood ? t.mood.charAt(0).toUpperCase() + t.mood.slice(1) : NOT_GIVEN],
    ['To do', t.todo.length ? t.todo.join('; ') : NOT_GIVEN],
  ];
}

/** What the live call hands back when it ends. `ticket` is null if no write-up arrived. */
export interface CallResult {
  ticket: Ticket | null;
  spoke: boolean;
}
