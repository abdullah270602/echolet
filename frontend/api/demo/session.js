// POST /api/demo/session: Vercel Function that mints a LiveKit token for an
// anonymous landing-page demo call. It mirrors the backend's
// /api/demo/session (backend/app/routes/demo.py) so the landing page can run
// its live demo without the backend: the agent on LiveKit Cloud reads the
// config and time cap from the signed token metadata (agent/demo.py).
import { createHmac, randomUUID } from 'node:crypto';
import clinicConfig from '../_clinic_config.js';

const env = (name, fallback) => process.env[name] ?? fallback;
const MAX_SECONDS = Number(env('DEMO_MAX_SECONDS', '120'));
const PER_IP_PER_HOUR = Number(env('DEMO_SESSIONS_PER_IP_PER_HOUR', '3'));
const PER_DAY = Number(env('DEMO_SESSIONS_PER_DAY', '200'));

// ponytail: per-instance memory, so limits reset on cold start and aren't shared
// across instances. Real cost bounds are the per-call cap, a Vercel Firewall
// rate-limit rule on this path, and provider spend limits. Move to a KV store
// if the demo gets real traffic.
const hitsByIp = new Map();
let day = new Date().toISOString().slice(0, 10);
let today = 0;

export function checkLimit(ip, now = Date.now(), date = new Date(now).toISOString().slice(0, 10)) {
  if (date !== day) {
    day = date;
    today = 0;
    hitsByIp.clear();
  }
  if (today >= PER_DAY) return "Today's live demo slots are used up. Try again tomorrow.";
  const hits = (hitsByIp.get(ip) ?? []).filter((t) => now - t < 3600_000);
  if (hits.length >= PER_IP_PER_HOUR) {
    hitsByIp.set(ip, hits);
    return "You've used your demo calls for this hour. Try again in an hour.";
  }
  hits.push(now);
  hitsByIp.set(ip, hits);
  today += 1;
  return null;
}

const b64url = (data) => Buffer.from(data).toString('base64url');

// LiveKit access token: an HS256 JWT signed with the API secret.
export function mintToken({ apiKey, apiSecret, room, identity, name, metadata, ttlSeconds }) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'HS256', typ: 'JWT' };
  const claims = {
    iss: apiKey,
    sub: identity,
    nbf: now,
    exp: now + ttlSeconds,
    name,
    metadata,
    video: {
      roomJoin: true,
      room,
      canPublish: true,
      canPublishSources: ['microphone'],
      canSubscribe: true,
      canPublishData: true,
    },
  };
  const body = `${b64url(JSON.stringify(header))}.${b64url(JSON.stringify(claims))}`;
  const sig = createHmac('sha256', apiSecret).update(body).digest('base64url');
  return `${body}.${sig}`;
}

const json = (status, data) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

export async function POST(request) {
  const { LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET } = process.env;
  if (env('DEMO_ENABLED', 'true') !== 'true' || !LIVEKIT_URL || !LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
    return json(503, { detail: 'The live demo is unavailable right now.' });
  }

  // Vercel sets x-real-ip to the client address; it can't be spoofed by the caller.
  const ip = request.headers.get('x-real-ip') ?? 'unknown';
  const reason = checkLimit(ip);
  if (reason) return json(429, { detail: reason });

  const room = `demo-${randomUUID()}`;
  const token = mintToken({
    apiKey: LIVEKIT_API_KEY,
    apiSecret: LIVEKIT_API_SECRET,
    room,
    identity: randomUUID(),
    name: 'Demo visitor',
    metadata: JSON.stringify({ demo: true, max_seconds: MAX_SECONDS, config: clinicConfig }),
    ttlSeconds: 120, // only needs to live long enough to join; the agent enforces the call cap
  });
  return json(200, { token, livekit_url: LIVEKIT_URL, room_name: room, max_seconds: MAX_SECONDS });
}
