import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';

process.env.LIVEKIT_URL = 'wss://example.livekit.cloud';
process.env.LIVEKIT_API_KEY = 'devkey';
process.env.LIVEKIT_API_SECRET = 's'.repeat(32);

const { createHandler, countLiveDemoCalls } = await import('../api/demo/session.js');

const claimsOf = (token) => JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
const req = (ip = '10.0.0.1') =>
  new Request('https://x/api/demo/session', { method: 'POST', headers: { 'x-real-ip': ip } });

/** Fake Neon tagged-template client. `counts` is what the limits query returns. */
function fakeSql(counts = { ip_hour: 0, ip_day: 0, day: 0 }) {
  const inserts = [];
  const sql = (strings, ...values) => {
    const text = strings.join('?');
    if (text.includes('SELECT')) return Promise.resolve([counts]);
    if (text.includes('INSERT')) inserts.push(values);
    return Promise.resolve([]);
  };
  return { sql, inserts };
}
const handler = ({ counts, live = 0, sql } = {}) => {
  const fake = sql ?? fakeSql(counts);
  return {
    fake,
    POST: createHandler({ getSql: () => fake.sql, liveCalls: async () => live }),
  };
};

test('issues a signed, short-lived, microphone-only token and records the call', async () => {
  const { POST, fake } = handler();
  const res = await POST(req());
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.match(body.room_name, /^demo-/);

  const [h, p, sig] = body.token.split('.');
  assert.equal(createHmac('sha256', 's'.repeat(32)).update(`${h}.${p}`).digest('base64url'), sig);
  const c = claimsOf(body.token);
  assert.equal(c.video.room, body.room_name);
  assert.deepEqual(c.video.canPublishSources, ['microphone']);
  assert.ok(c.exp - c.nbf <= 120);
  assert.equal(JSON.parse(c.metadata).config.agent.business_name, 'Brightside Dental');

  assert.equal(fake.inserts.length, 1);
  assert.match(fake.inserts[0][0], /^[0-9a-f]{32}$/, 'stores a hash, not the IP');
  assert.notEqual(fake.inserts[0][0], '10.0.0.1');
});

test('per-visitor hourly, per-visitor daily and global daily limits return 429 without recording', async () => {
  for (const counts of [
    { ip_hour: 3, ip_day: 3, day: 3 },
    { ip_hour: 0, ip_day: 6, day: 6 },
    { ip_hour: 0, ip_day: 0, day: 200 },
  ]) {
    const { POST, fake } = handler({ counts });
    const res = await POST(req());
    assert.equal(res.status, 429, JSON.stringify(counts));
    assert.ok((await res.json()).detail);
    assert.equal(fake.inserts.length, 0);
  }
});

test('refuses when the simultaneous-call cap is reached', async () => {
  const { POST } = handler({ live: 5 });
  const res = await POST(req());
  assert.equal(res.status, 429);
  assert.equal((await res.json()).token, undefined);
});

test('fails closed when the database or LiveKit cannot be reached', async () => {
  const brokenDb = createHandler({ getSql: () => () => Promise.reject(new Error('db down')), liveCalls: async () => 0 });
  assert.equal((await brokenDb(req())).status, 503);

  const brokenLk = createHandler({ getSql: () => fakeSql().sql, liveCalls: async () => { throw new Error('lk down'); } });
  assert.equal((await brokenLk(req())).status, 503);
});

test('without a database, falls back to an in-memory hourly limit', async () => {
  const POST = createHandler({ getSql: () => null, liveCalls: async () => 0 });
  for (let i = 0; i < 3; i++) assert.equal((await POST(req('10.9.9.9'))).status, 200);
  assert.equal((await POST(req('10.9.9.9'))).status, 429);
});

test('returns 503 when LiveKit is not configured', async () => {
  const secret = process.env.LIVEKIT_API_SECRET;
  delete process.env.LIVEKIT_API_SECRET;
  try {
    assert.equal((await handler().POST(req())).status, 503);
  } finally {
    process.env.LIVEKIT_API_SECRET = secret;
  }
});

test('counts only demo rooms, via ListRooms with a roomList-only token', async () => {
  let called;
  const fetchImpl = async (url, init) => {
    called = { url, init };
    return Response.json({ rooms: [{ name: 'demo-1' }, { name: 'demo-2' }, { name: 'a-real-call' }] });
  };
  const n = await countLiveDemoCalls({ url: 'wss://example.livekit.cloud', apiKey: 'k', apiSecret: 's'.repeat(32), fetchImpl });
  assert.equal(n, 2);
  assert.equal(called.url, 'https://example.livekit.cloud/twirp/livekit.RoomService/ListRooms');
  const c = claimsOf(called.init.headers.Authorization.slice('Bearer '.length));
  assert.deepEqual(c.video, { roomList: true });
});
