import { Hono } from 'hono';
import { cors } from 'hono/cors';

const app = new Hono();
app.use('*', cors({ origin: '*' }));

function buf2hex(buf) { return Array.from(new Uint8Array(buf), b => b.toString(16).padStart(2, '0')).join(''); }
function buf2b64(buf) { return btoa(String.fromCharCode(...new Uint8Array(buf))); }
function b642buf(str) { return Uint8Array.from(atob(str), c => c.charCodeAt(0)); }

// 简单 SHA-256 哈希密码
async function hashPw(password, salt) {
  const data = new TextEncoder().encode(password + salt);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return salt + ':' + buf2hex(hash);
}
async function checkPw(password, stored) {
  const [salt] = stored.split(':');
  return stored === await hashPw(password, salt);
}

// JWT
async function signJWT(payload, secret) {
  const h = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const b = btoa(JSON.stringify({ ...payload, iat: Math.floor(Date.now()/1000), exp: Math.floor(Date.now()/1000)+2592000 }));
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const s = buf2b64(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(`${h}.${b}`)));
  return `${h}.${b}.${s}`;
}
async function verifyJWT(token, secret) {
  try {
    const [h, b, s] = token.split('.');
    const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify('HMAC', k, b642buf(s), new TextEncoder().encode(`${h}.${b}`));
    if (!ok) return null;
    const p = JSON.parse(atob(b));
    if (p.exp < Math.floor(Date.now()/1000)) return null;
    return p;
  } catch { return null; }
}

// Init DB
async function initDB(db) {
  await db.exec('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, avatar TEXT DEFAULT \'\')');
}

// Register
app.post('/api/auth/register', async (c) => {
  try {
    const db = c.env.deepphilosophy_db;
    await initDB(db);
    const { username, password } = await c.req.json();
    if (!username || !password || username.length < 2 || password.length < 4) {
      return c.json({ error: '用户名2+，密码4+' }, 400);
    }
    const existing = await db.prepare('SELECT id FROM users WHERE username = ?').bind(username).first();
    if (existing) return c.json({ error: '用户名已存在' }, 409);
    const hash = await hashPw(password, crypto.randomUUID());
    await db.prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)').bind(username, hash).run();
    const token = await signJWT({ username }, c.env.JWT_SECRET);
    return c.json({ token, username });
  } catch (e) { return c.json({ error: e.message }, 500); }
});

// Login
app.post('/api/auth/login', async (c) => {
  try {
    const db = c.env.deepphilosophy_db;
    await initDB(db);
    const { username, password } = await c.req.json();
    const user = await db.prepare('SELECT * FROM users WHERE username = ?').bind(username).first();
    if (!user || !(await checkPw(password, user.password_hash))) {
      return c.json({ error: '用户名或密码错误' }, 401);
    }
    const token = await signJWT({ username }, c.env.JWT_SECRET);
    return c.json({ token, username, avatar: user.avatar || '' });
  } catch (e) { return c.json({ error: e.message }, 500); }
});

// Profile
app.get('/api/auth/profile', async (c) => {
  try {
    const auth = c.req.header('Authorization') || '';
    const token = auth.replace('Bearer ', '');
    const payload = await verifyJWT(token, c.env.JWT_SECRET);
    if (!payload) return c.json({ error: '未登录' }, 401);
    const db = c.env.deepphilosophy_db;
    const user = await db.prepare('SELECT username, avatar, created_at FROM users WHERE username = ?').bind(payload.username).first();
    return c.json(user || { error: '用户不存在' }, 404);
  } catch (e) { return c.json({ error: e.message }, 500); }
});

// Health
app.get('/api/health', c => c.json({ status: 'ok' }));

export default app;
