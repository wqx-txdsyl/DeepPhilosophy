import { Hono } from 'hono';
import { cors } from 'hono/cors';

const ALLOWED_ORIGINS = [
  'https://deepphilosophy.top',
  'https://deepphilosophy.pages.dev',
  'https://deepphilosophy.vercel.app',
  'http://localhost:5173',
  'http://localhost:5174',
  'http://localhost:5175',
  'http://localhost:5201',
];

const app = new Hono();
app.use('*', cors({
  origin: (origin) => ALLOWED_ORIGINS.includes(origin) ? origin : null,
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Authorization', 'Content-Type'],
  credentials: false,
}));

function buf2hex(buf) { return Array.from(new Uint8Array(buf), b => b.toString(16).padStart(2, '0')).join(''); }
function buf2b64url(buf) { return btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,''); }
function b64url2buf(str) { return Uint8Array.from(atob(str.replace(/-/g,'+').replace(/_/g,'/')), c => c.charCodeAt(0)); }

// 简单 SHA-256 哈希密码（遗留格式; 新注册/改密一律走下方 PBKDF2）
async function hashPw(password, salt) {
  const data = new TextEncoder().encode(password + salt);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return salt + ':' + buf2hex(hash);
}
// PBKDF2 密码哈希（2026-08-14 安全加固: 裸 SHA-256 零迭代太弱, 新注册一律 PBKDF2 10 万次）
const PBKDF2_ITER = 100000;
async function hashPwPBKDF2(password, salt) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: new TextEncoder().encode(salt), iterations: PBKDF2_ITER, hash: 'SHA-256' },
    key, 256);
  return `pbkdf2:${PBKDF2_ITER}:${salt}:` + buf2hex(bits);
}
async function verifyPBKDF2(password, salt, iter, hex) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: new TextEncoder().encode(salt), iterations: iter, hash: 'SHA-256' },
    key, 256);
  return buf2hex(bits) === hex.toLowerCase();
}
// 密码校验，支持四种格式：
//   "pbkdf2:{iter}:{salt}:{hex}"  新格式（2026-08-14 起注册/改密）
//   "{salt}:{sha256hex}"          原生格式（旧注册）
//   "sha256:{salt}:{hash}"        迁移自旧 Render 库的 SHA-256 用户（原密码继续可用）
//   "scrypt:{salt}:{hash}"        旧 scrypt 用户 — 免费版无法验证（JS scrypt 超 CPU 上限），
//                                 路径 B 提示重置；将来 Workers Paid + verifyScrypt 开关可自动登录
async function checkPw(password, stored) {
  if (stored.startsWith('pbkdf2:')) {
    const [, iter, salt, hex] = stored.split(':');
    return await verifyPBKDF2(password, salt, parseInt(iter, 10) || PBKDF2_ITER, hex);
  }
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

// ── 登录/注册限流（2026-08-14 安全加固: 防暴力破解; 内存滑窗, 单实例够用）──
const LOGIN_LIMIT = 10, REGISTER_LIMIT = 5, WINDOW_MS = 15 * 60 * 1000;
const _attempts = new Map();   // ip -> {count, start}
function _rateLimit(ip, limit) {
  const now = Date.now();
  // 顺带清理过期条目, 防 Map 无限增长
  if (_attempts.size > 500) {
    for (const [k, v] of _attempts) if (now - v.start > WINDOW_MS) _attempts.delete(k);
  }
  const rec = _attempts.get(ip);
  if (!rec || now - rec.start > WINDOW_MS) {
    _attempts.set(ip, { count: 1, start: now });
    return true;
  }
  rec.count += 1;
  return rec.count <= limit;
}
function _clientIp(c) {
  const ff = c.req.header('x-forwarded-for') || '';
  if (ff) return ff.split(',')[0].trim();
  const cf = c.req.header('cf-connecting-ip');
  if (cf) return cf.trim();
  return c.req.header('x-real-ip') || 'unknown';
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
  const ip = _clientIp(c);
  if (!_rateLimit(ip, REGISTER_LIMIT)) {
    return c.json({ error: '注册过于频繁，请稍后再试' }, 429);
  }
  try {
    const db = c.env.deepphilosophy_db;
    await initDB(db);
    const { username, password } = await c.req.json();
    // 密码策略与本地后端统一：注册 ≥8 位（S5/S10）。老用户弱密码不强制改密，仅在其主动改密时按 ≥8 位校验
    if (!username || !password || username.length < 2 || password.length < 8) {
      return c.json({ error: '用户名2+，密码8+' }, 400);
    }
    const existing = await db.prepare('SELECT id FROM users WHERE username = ?').bind(username).first();
    if (existing) return c.json({ error: '用户名已存在' }, 409);
    const hash = await hashPwPBKDF2(password, crypto.randomUUID());   // PBKDF2 加固
    const ins = await db.prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)').bind(username, hash).run();
    const token = await signJWT({ username, user_id: ins.meta.last_row_id }, c.env.JWT_SECRET);
    return c.json({ token, username });
  } catch (e) { return c.json({ error: e.message }, 500); }
});

// Login
app.post('/api/auth/login', async (c) => {
  const ip = _clientIp(c);
  if (!_rateLimit(ip, LOGIN_LIMIT)) {
    return c.json({ error: '登录尝试过于频繁，请 15 分钟后再试' }, 429);
  }
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
    // 旧格式（非 pbkdf2）登录成功 → 升级为 PBKDF2 哈希
    if (!user.password_hash.startsWith('pbkdf2:')) {
      const newHash = await hashPwPBKDF2(password, crypto.randomUUID());
      await db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').bind(newHash, user.id).run();
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
