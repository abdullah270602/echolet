// POST /api/waitlist: Vercel Function that adds a name + email to the waitlist
// table in Postgres (schema: backend/alembic/versions/k1l2m3n4o5p6_add_waitlist_table.py).
import { neon } from '@neondatabase/serverless';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
// Letters from any script, plus the separators real names use.
const NAME = /^[\p{L}\p{M}][\p{L}\p{M}\s'.-]*$/u;

/** Returns { name, email } or { error } with a message fit to show the visitor. */
export function validate(body) {
  const name = typeof body?.name === 'string' ? body.name.trim().replace(/\s+/g, ' ') : '';
  const email = typeof body?.email === 'string' ? body.email.trim().toLowerCase() : '';
  if (name.length < 2) return { error: 'Enter your name.', field: 'name' };
  if (name.length > 100 || !NAME.test(name)) return { error: 'Enter your name using letters only.', field: 'name' };
  if (!email) return { error: 'Enter your email address.', field: 'email' };
  if (email.length > 254 || !EMAIL.test(email)) return { error: 'Enter a valid email address, like name@clinic.com.', field: 'email' };
  return { name, email };
}

const json = (status, data) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

/** `sql` is injectable for tests; production uses Neon's HTTP driver. */
export function createHandler(getSql = () => neon(process.env.DATABASE_URL)) {
  return async function POST(request) {
    let body;
    try {
      body = await request.json();
    } catch {
      return json(400, { error: 'Send name and email as JSON.' });
    }
    // Honeypot: a field people never see. Bots fill it; pretend success.
    if (body?.company) return json(200, { ok: true });

    const result = validate(body);
    if (result.error) return json(400, result);

    if (!process.env.DATABASE_URL) return json(503, { error: 'The waitlist is closed right now.' });
    try {
      const sql = getSql();
      // created_at is set explicitly: the table predates its migration and may lack a default.
      // Re-joining with the same email is a no-op and still returns ok, so the
      // response never reveals who is already on the list.
      await sql`INSERT INTO waitlist (name, email, created_at) VALUES (${result.name}, ${result.email}, NOW())
                ON CONFLICT (email) DO NOTHING`;
      return json(200, { ok: true });
    } catch (e) {
      console.error('waitlist insert failed', e);
      return json(500, { error: "We couldn't save that. Try again in a minute." });
    }
  };
}

export const POST = createHandler();
