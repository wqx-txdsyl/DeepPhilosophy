import test from 'node:test';
import assert from 'node:assert/strict';
import app from '../src/index.js';
import stats from '../src/stats.json' with { type: 'json' };

test('retired AI and chat endpoints reject cached clients without model or database access', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () => { throw new Error('A retired endpoint attempted network access'); };
  const env = { DEEPSEEK_API_KEY: 'test-only', deepphilosophy_db: { prepare() { throw new Error('Retired endpoint accessed user data'); } } };
  try {
    for (const path of ['/api/ai', '/api/ai/stream', '/api/ai/unknown', '/api/qa', '/api/history/chat', '/api/book-chat', '/api/book-chat/save', '/api/book-chat/book-id']) {
      for (const method of ['GET', 'POST', 'PUT', 'DELETE']) {
        const response = await app.request(path, { method, ...(method === 'POST' ? { body: '{invalid' } : {}) }, env);
        assert.equal(response.status, 410, `${method} ${path}`);
        assert.equal((await response.json()).code, 'FEATURE_REMOVED');
      }
    }
  } finally { globalThis.fetch = originalFetch; }
});

test('health and book statistics remain available', async () => {
  assert.equal((await (await app.request('/api/health')).json()).status, 'healthy');
  assert.deepEqual(await (await app.request('/api/stats')).json(), stats);
});

test('reading, notes and account endpoints retain authentication protection', async () => {
  for (const [path, method] of [['/api/history/reading','GET'], ['/api/history/reading','POST'], ['/api/notes/load?book_id=b','GET'], ['/api/notes/save','POST'], ['/api/user/avatar','GET']]) {
    assert.equal((await app.request(path, { method }, {})).status, 401, path);
  }
});

test('authenticated ordinary notes can still be saved and loaded', async () => {
  const secret = 'test-secret';
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const payload = Buffer.from(JSON.stringify({ user_id: 7, exp: Math.floor(Date.now()/1000)+60 })).toString('base64url');
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), {name:'HMAC',hash:'SHA-256'}, false, ['sign']);
  const signature = Buffer.from(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${header}.${payload}`))).toString('base64url');
  const headers = { Authorization: `Bearer ${header}.${payload}.${signature}`, 'Content-Type': 'application/json' };
  let saved;
  const env = { JWT_SECRET: secret, deepphilosophy_db: { prepare(sql) {
    return { bind(...args) {
      return {
        first: async () => sql.includes('FROM users') ? { id: 7 } : { note_text: saved?.[2] },
        run: async () => { assert.ok(sql.includes('book_notes')); saved = args; return {success:true}; },
      };
    } };
  } } };
  const write = await app.request('/api/notes/save', {method:'POST',headers,body:JSON.stringify({book_id:'book-1',note_text:'普通阅读笔记'})}, env);
  assert.equal(write.status, 200);
  assert.deepEqual(saved, [7,'book-1','普通阅读笔记']);
  const read = await app.request('/api/notes/load?book_id=book-1', {headers}, env);
  assert.deepEqual(await read.json(), {note_text:'普通阅读笔记'});
});
