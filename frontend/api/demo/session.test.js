import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';

process.env.LIVEKIT_URL = 'wss://example.livekit.cloud';
process.env.LIVEKIT_API_KEY = 'devkey';
process.env.LIVEKIT_API_SECRET = 's'.repeat(32);
process.env.DEMO_SESSIONS_PER_IP_PER_HOUR = '1';

const { POST, checkLimit } = await import('./session.js');

const claimsOf = (token) => JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
const post = (ip) => POST(new Request('https://x/api/demo/session', { method: 'POST', headers: { 'x-real-ip': ip } }));

test('issues a signed microphone-only token carrying the demo config and cap', async () => {
  const res = await post('10.0.0.1');
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.match(body.room_name, /^demo-/);
  assert.equal(body.livekit_url, 'wss://example.livekit.cloud');

  const [h, p, sig] = body.token.split('.');
  assert.equal(createHmac('sha256', 's'.repeat(32)).update(`${h}.${p}`).digest('base64url'), sig);

  const c = claimsOf(body.token);
  assert.equal(c.iss, 'devkey');
  assert.equal(c.video.room, body.room_name);
  assert.deepEqual(c.video.canPublishSources, ['microphone']);
  assert.ok(c.exp - c.nbf <= 120);
  const meta = JSON.parse(c.metadata);
  assert.equal(meta.demo, true);
  assert.equal(meta.max_seconds, body.max_seconds);
  assert.equal(meta.config.agent.business_name, 'Brightside Dental');
});

test('second call from the same visitor within the hour is rate limited', async () => {
  assert.equal((await post('10.0.0.2')).status, 200);
  const res = await post('10.0.0.2');
  assert.equal(res.status, 429);
  assert.ok((await res.json()).detail);
});

test('limit window slides and resets on a new day', () => {
  const t0 = Date.parse('2026-05-01T10:00:00Z');
  assert.equal(checkLimit('a', t0), null);
  assert.notEqual(checkLimit('a', t0 + 1000), null);
  assert.equal(checkLimit('a', t0 + 3600_001), null);
  assert.equal(checkLimit('a', Date.parse('2026-05-02T00:00:01Z')), null);
});

test('returns 503 when LiveKit is not configured', async () => {
  const secret = process.env.LIVEKIT_API_SECRET;
  delete process.env.LIVEKIT_API_SECRET;
  try {
    assert.equal((await post('10.0.0.3')).status, 503);
  } finally {
    process.env.LIVEKIT_API_SECRET = secret;
  }
});
