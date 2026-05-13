import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHandler, validate } from '../api/waitlist.js';

process.env.DATABASE_URL = 'postgres://example';

const req = (body) =>
  new Request('https://x/api/waitlist', { method: 'POST', body: typeof body === 'string' ? body : JSON.stringify(body) });

function fakeSql() {
  const calls = [];
  const sql = (strings, ...values) => {
    calls.push({ text: strings.join('?'), values });
    return Promise.resolve([]);
  };
  return { sql, calls };
}

test('accepts real names in any script and normalises the email', () => {
  for (const name of ['Dana Reyes', 'José Álvarez', "Siobhán O'Neill", 'Zoë Ng-Smith', 'محمد علي']) {
    assert.equal(validate({ name, email: 'a@b.co' }).name, name);
  }
  assert.equal(validate({ name: 'Dana', email: '  Dana@Clinic.COM ' }).email, 'dana@clinic.com');
});

test('rejects bad input with a field-specific message', () => {
  assert.equal(validate({ name: 'D', email: 'a@b.co' }).field, 'name');
  assert.equal(validate({ name: '<script>', email: 'a@b.co' }).field, 'name');
  assert.equal(validate({ name: 'Dana', email: 'not-an-email' }).field, 'email');
  assert.equal(validate({}).field, 'name');
});

test('inserts with parameters and ignores duplicates', async () => {
  const { sql, calls } = fakeSql();
  const res = await createHandler(() => sql)(req({ name: 'Dana Reyes', email: 'dana@clinic.com' }));
  assert.equal(res.status, 200);
  assert.deepEqual(calls[0].values, ['Dana Reyes', 'dana@clinic.com']);
  assert.match(calls[0].text, /ON CONFLICT \(email\) DO NOTHING/);
});

test('honeypot submissions are dropped without touching the database', async () => {
  const { sql, calls } = fakeSql();
  const res = await createHandler(() => sql)(req({ name: 'Bot', email: 'b@b.co', company: 'spam' }));
  assert.equal(res.status, 200);
  assert.equal(calls.length, 0);
});

test('invalid JSON is a 400, a database failure is a 500', async () => {
  assert.equal((await createHandler()(req('nope'))).status, 400);
  const failing = () => () => Promise.reject(new Error('down'));
  assert.equal((await createHandler(failing)(req({ name: 'Dana', email: 'd@c.co' }))).status, 500);
});
