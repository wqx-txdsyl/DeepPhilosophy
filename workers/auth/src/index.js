import { Hono } from 'hono';
import { cors } from 'hono/cors';

const app = new Hono();
app.use('*', cors({ origin: '*' }));

function buf2hex(buf) { return Array.from(new Uint8Array(buf), b => b.toString(16).padStart(2, '0')).join(''); }
function buf2b64url(buf) { return btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,''); }
function b64url2buf(str) { return Uint8Array.from(atob(str.replace(/-/g,'+').replace(/_/g,'/')), c => c.charCodeAt(0)); }

// 简单 SHA-256 哈希密码
async function hashPw(password, salt) {
  const data = new TextEncoder().encode(password + salt);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return salt + ':' + buf2hex(hash);
}
// 密码校验，支持三种格式：
//   "{salt}:{sha256hex}"        原生格式（新注册/重置后）
//   "sha256:{salt}:{hash}"      迁移自旧 Render 库的 SHA-256 用户（原密码继续可用）
//   "scrypt:{salt}:{hash}"      旧 scrypt 用户 — 免费版无法验证（JS scrypt 超 CPU 上限），
//                               路径 B 提示重置；将来 Workers Paid + verifyScrypt 开关可自动登录
async function checkPw(password, stored) {
  if (stored.startsWith('sha256:')) {
    const [, salt, hash] = stored.split(':');
    const data = new TextEncoder().encode(password + salt);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return hash.toLowerCase() === buf2hex(digest);
  }
  if (stored.startsWith('scrypt:')) {
    return 'SCRYPT_LEGACY';  // 特殊标记：登录处转 401 提示重置
  }
  const [salt] = stored.split(':');
  return stored === await hashPw(password, salt);
}

// JWT
async function signJWT(payload, secret) {
  const h = buf2b64url(new TextEncoder().encode(JSON.stringify({ alg: 'HS256', typ: 'JWT' })));
  const b = buf2b64url(new TextEncoder().encode(JSON.stringify({ ...payload, iat: Math.floor(Date.now()/1000), exp: Math.floor(Date.now()/1000)+2592000 })));
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const s = buf2b64url(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(`${h}.${b}`)));
  return `${h}.${b}.${s}`;
}
async function verifyJWT(token, secret) {
  try {
    const [h, b, s] = token.split('.');
    const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify('HMAC', k, b64url2buf(s), new TextEncoder().encode(`${h}.${b}`));
    if (!ok) return null;
    const p = JSON.parse(new TextDecoder().decode(b64url2buf(b)));
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
    const ins = await db.prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)').bind(username, hash).run();
    const token = await signJWT({ username, user_id: ins.meta.last_row_id }, c.env.JWT_SECRET);
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
    if (!user) {
      return c.json({ error: '用户名或密码错误' }, 401);
    }
    const pw = await checkPw(password, user.password_hash);
    if (pw === 'SCRYPT_LEGACY') {
      return c.json({ error: '该账号由旧系统迁移而来，密码体系已升级，请联系管理员重置密码后再登录' }, 401);
    }
    if (!pw) {
      return c.json({ error: '用户名或密码错误' }, 401);
    }
    const token = await signJWT({ username, user_id: user.id }, c.env.JWT_SECRET);
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
    const user = await db.prepare('SELECT username, avatar FROM users WHERE username = ?').bind(payload.username).first();
    if (!user) return c.json({ error: '用户不存在' }, 404);
    return c.json(user);  // 注意：不能写 c.json(user || {...}, 404) —— user 存在时也会返回 404（历史 bug）
  } catch (e) { return c.json({ error: e.message }, 500); }
});

// Health
app.get('/api/health', c => c.json({ status: 'ok' }));

export default app;
