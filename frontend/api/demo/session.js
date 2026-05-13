// POST /api/demo/session: Vercel Function that mints a LiveKit token for an
// anonymous landing-page demo call. Same contract as the backend's
// /api/demo/session (backend/app/routes/demo.py); the agent on LiveKit Cloud reads
// the config and time cap from the signed token metadata (agent/demo.py).
//
// Abuse and cost protection, in the order they are checked:
//   1. Vercel Firewall rate limit on this path (configured in the dashboard/CLI).
//   2. Per-visitor limits (hourly and daily) and a global daily budget, stored in
//      Postgres so they hold across cold starts and instances. IPs are hashed.
//   3. A cap on simultaneous demo calls, read live from LiveKit.
//   4. A short token TTL, microphone-only grant, and the agent's per-call time cap.
import { createHash, createHmac, randomUUID } from 'node:crypto';
import { neon } from '@neondatabase/serverless';
import clinicConfig from '../_clinic_config.js';

const num = (name, fallback) => Number(process.env[name] ?? fallback);
const limits = () => ({
  maxSeconds: num('DEMO_MAX_SECONDS', 120),
  perIpHour: num('DEMO_SESSIONS_PER_IP_PER_HOUR', 3),
  perIpDay: num('DEMO_SESSIONS_PER_IP_PER_DAY', 6),
  perDay: num('DEMO_SESSIONS_PER_DAY', 200),
  concurrent: num('DEMO_MAX_CONCURRENT_CALLS', 5),
});

const BUSY = 'The demo line is busy right now. Try again in a few minutes.';
const HOURLY = "You've used your demo calls for this hour. Try again in an hour.";
const DAILY_IP = "You've used your demo calls for today. Try again tomorrow.";
const DAILY = "Today's live demo slots are used up. Try again tomorrow.";

const b64url = (data) => Buffer.from(data).toString('base64url');

/** LiveKit access token: an HS256 JWT signed with the API secret. */
export function mintToken({ apiKey, apiSecret, ttlSeconds, identity, name, metadata, video }) {
  const now = Math.floor(Date.now() / 1000);
  const claims = { iss: apiKey, sub: identity, nbf: now, exp: now + ttlSeconds, video };
  if (name) claims.name = name;
  if (metadata) claims.metadata = metadata;
  const body = `${b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))}.${b64url(JSON.stringify(claims))}`;
  return `${body}.${createHmac('sha256', apiSecret).update(body).digest('base64url')}`;
}

/** Number of demo rooms currently open on the LiveKit project. Throws if LiveKit can't be reached. */
export async function countLiveDemoCalls({ url, apiKey, apiSecret, fetchImpl = fetch }) {
  const token = mintToken({ apiKey, apiSecret, ttlSeconds: 60, identity: 'demo-gate', video: { roomList: true } });
  const res = await fetchImpl(`${url.replace(/^ws/, 'http')}/twirp/livekit.RoomService/ListRooms`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: '{}',
  });
  if (!res.ok) throw new Error(`ListRooms ${res.status}`);
  const { rooms = [] } = await res.json();
  return rooms.filter((r) => r.name?.startsWith('demo-')).length;
}

// ponytail: count-then-insert is not atomic, so a burst can overshoot a limit by a
// call or two. The concurrency cap and per-call time cap bound the cost of that.
let tableReady;
async function checkAndRecord(sql, ipHash, l) {
  tableReady ??= sql`CREATE TABLE IF NOT EXISTS demo_calls (
      id BIGSERIAL PRIMARY KEY,
      ip_hash TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())`.then(() =>
    sql`CREATE INDEX IF NOT EXISTS demo_calls_ip_time ON demo_calls (ip_hash, created_at)`);
  try {
    await tableReady;
  } catch (e) {
    tableReady = undefined; // retry on the next request instead of failing forever
    throw e;
  }

  const [c] = await sql`SELECT
      COUNT(*) FILTER (WHERE ip_hash = ${ipHash} AND created_at > NOW() - INTERVAL '1 hour') AS ip_hour,
      COUNT(*) FILTER (WHERE ip_hash = ${ipHash}) AS ip_day,
      COUNT(*) AS day
    FROM demo_calls WHERE created_at > NOW() - INTERVAL '1 day'`;
  if (Number(c.day) >= l.perDay) return DAILY;
  if (Number(c.ip_day) >= l.perIpDay) return DAILY_IP;
  if (Number(c.ip_hour) >= l.perIpHour) return HOURLY;
  await sql`INSERT INTO demo_calls (ip_hash) VALUES (${ipHash})`;
  return null;
}

// Fallback for local runs without a database: per-instance memory only.
const memory = new Map();
function checkMemory(ipHash, l, now = Date.now()) {
  const hits = (memory.get(ipHash) ?? []).filter((t) => now - t < 3600_000);
  if (hits.length >= l.perIpHour) return HOURLY;
  memory.set(ipHash, [...hits, now]);
  return null;
}

const json = (status, data) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

/** Dependencies are injectable for tests. */
export function createHandler({
  getSql = () => (process.env.DATABASE_URL ? neon(process.env.DATABASE_URL) : null),
  liveCalls = countLiveDemoCalls,
} = {}) {
  return async function POST(request) {
    const { LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET } = process.env;
    if ((process.env.DEMO_ENABLED ?? 'true') !== 'true' || !LIVEKIT_URL || !LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
      return json(503, { detail: 'The live demo is unavailable right now.' });
    }
    const l = limits();

    // Vercel sets x-real-ip to the client address; callers can't spoof it. Only a
    // salted hash is stored.
    const ip = request.headers.get('x-real-ip') ?? 'unknown';
    const ipHash = createHash('sha256').update(`${LIVEKIT_API_SECRET}:${ip}`).digest('hex').slice(0, 32);

    let reason;
    try {
      const sql = getSql();
      reason = sql ? await checkAndRecord(sql, ipHash, l) : checkMemory(ipHash, l);
    } catch (e) {
      console.error('demo limit check failed', e);
      return json(503, { detail: BUSY }); // fail closed: no limits, no call
    }
    if (reason) return json(429, { detail: reason });

    try {
      const active = await liveCalls({ url: LIVEKIT_URL, apiKey: LIVEKIT_API_KEY, apiSecret: LIVEKIT_API_SECRET });
      if (active >= l.concurrent) return json(429, { detail: BUSY });
    } catch (e) {
      console.error('demo concurrency check failed', e);
      return json(503, { detail: BUSY });
    }

    const room = `demo-${randomUUID()}`;
    const token = mintToken({
      apiKey: LIVEKIT_API_KEY,
      apiSecret: LIVEKIT_API_SECRET,
      ttlSeconds: 120, // only needs to live long enough to join; the agent enforces the call cap
      identity: randomUUID(),
      name: 'Demo visitor',
      metadata: JSON.stringify({ demo: true, max_seconds: l.maxSeconds, config: clinicConfig }),
      video: {
        roomJoin: true,
        room,
        canPublish: true,
        canPublishSources: ['microphone'],
        canSubscribe: true,
        canPublishData: true,
      },
    });
    return json(200, { token, livekit_url: LIVEKIT_URL, room_name: room, max_seconds: l.maxSeconds });
  };
}

export const POST = createHandler();
