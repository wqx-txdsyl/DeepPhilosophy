/**
 * deepphilosophy-api — 业务 API Worker（替代 Render FastAPI 剩余依赖）
 * 路由 deepphilosophy.top/api/*（与 auth worker 的 /api/auth/* 最长前缀匹配共存）
 *
 * 端点（响应字段与 Render main.py 语义一致，错误统一 {error, detail} 双字段：
 *   前端有的解析 e.error、有的解析 d.detail，两个都给）：
 *   GET  /api/health                     → {status:'healthy', version, timestamp}
 *   POST /api/ai/stream                  → SSE 纯透传 api.deepseek.com（不解析不 TransformStream，免费版 10ms CPU 够用）
 *   POST /api/qa                         → {answer, sources:[], question}；带 JWT 则插 chat_history 两条
 *   GET  /api/books/{id}/file            → oss: 302 直链（零流量）；仅 github: Range 代理 206；无 Range 且 >100MB → 302 直链
 *   GET  /api/stats                      → 构建产物 stats.json
 *   GET  /api/admin/stats?password=      → {stats, users, user_count}（stats 为迁移时刻快照，访问统计冻结）
 *   ── 以下全部 JWT（payload.user_id）鉴权 ──
 *   GET/POST /api/history/reading        → {history:[{book_id,book_title,book_author,progress_page,progress_percent,last_read_at}]} / upsert {success:true}
 *   GET/POST/DELETE /api/history/chat    → {messages:[{role,content,sources,created_at}]} ASC / {success:true}
 *   POST /api/notes/save                 → upsert {success:true}
 *   GET  /api/notes/load?book_id=        → {note_text}（ReaderPage 在用，Render 上一直 404 的遗留，此处补上）
 *   GET  /api/notes/{book_id}            → {note_text}
 *   GET  /api/notes                      → {notes:{book_id:note_text}}
 *   POST /api/book-chat/save             → {success:true}
 *   GET/DELETE /api/book-chat/{book_id}  → {messages:[{role,content,created_at}]} / {success:true}
 *   PUT  /api/user/profile               → 改用户名 → {status:'ok', username}（JWT 含 user_id，改名后旧 token 仍有效）
 *   PUT  /api/user/password              → 校验旧密码（checkPw 三格式）→ {status:'ok'}
 *   GET/POST /api/user/avatar            → {avatar} / {status:'ok'}
 *
 * 未注册端点（books/authors 列表、asr 等）→ Hono 404 —— 前端静态兜底已覆盖，无需迁移。
 */
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import booksData from './books.json';
import statsData from './stats.json';
import adminStatsData from './admin_stats.json';

const app = new Hono();
app.use('*', cors({ origin: '*' }));

// ============ crypto 工具（与 auth worker 同源逻辑） ============
function buf2hex(buf) { return Array.from(new Uint8Array(buf), b => b.toString(16).padStart(2, '0')).join(''); }
function buf2b64url(buf) { return btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, ''); }
function b64url2buf(str) { return Uint8Array.from(atob(str.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0)); }

async function hashPw(password, salt) {
  const data = new TextEncoder().encode(password + salt);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return salt + ':' + buf2hex(hash);
}
// PBKDF2（2026-08-14 加固: 与 auth worker 同格式 pbkdf2:{iter}:{salt}:{hex}）
const PBKDF2_ITER = 100000;
async function hashPwPBKDF2(password, salt) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: new TextEncoder().encode(salt), iterations: PBKDF2_ITER, hash: 'SHA-256' },
    key, 256);
  return `pbkdf2:${PBKDF2_ITER}:${salt}:` + buf2hex(bits);
}
// 四格式：pbkdf2:{iter}:{salt}:{hex} / {salt}:{hex} / sha256:{salt}:{hash}（迁移库）/ scrypt:{salt}:{hash}（旧库，返回标记）
async function checkPw(password, stored) {
  if (stored.startsWith('pbkdf2:')) {
    const [, iter, salt, hex] = stored.split(':');
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits(
      { name: 'PBKDF2', salt: new TextEncoder().encode(salt), iterations: parseInt(iter, 10) || PBKDF2_ITER, hash: 'SHA-256' },
      key, 256);
    return buf2hex(bits) === hex.toLowerCase();
  }
  if (stored.startsWith('sha256:')) {
    const [, salt, hash] = stored.split(':');
    const data = new TextEncoder().encode(password + salt);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return hash.toLowerCase() === buf2hex(digest);
  }
  if (stored.startsWith('scrypt:')) return 'SCRYPT_LEGACY';
  const [salt] = stored.split(':');
  return stored === await hashPw(password, salt);
}

// 恒定时间比较（2026-08-14: admin 密码校验改用, 防时序侧信道）
async function safeEqual(a, b) {
  const ha = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(a)));
  const hb = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(b)));
  if (ha.length !== hb.length) return false;
  let d = 0;
  for (let i = 0; i < ha.length; i++) d |= ha[i] ^ hb[i];
  return d === 0;
}

async function verifyJWT(token, secret) {
  try {
    const [h, b, s] = token.split('.');
    const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify('HMAC', k, b64url2buf(s), new TextEncoder().encode(`${h}.${b}`));
    if (!ok) return null;
    const p = JSON.parse(new TextDecoder().decode(b64url2buf(b)));
    if (p.exp < Math.floor(Date.now() / 1000)) return null;
    return p;
  } catch { return null; }
}

// JWT 校验中间件：payload.user_id 必需；用户必须真实存在于 D1
const requireAuth = async (c, next) => {
  const token = (c.req.header('Authorization') || '').replace('Bearer ', '');
  const payload = await verifyJWT(token, c.env.JWT_SECRET);
  if (!payload || !payload.user_id) {
    return c.json({ error: '未登录', detail: '未登录' }, 401);
  }
  const user = await c.env.deepphilosophy_db.prepare('SELECT id FROM users WHERE id = ?').bind(payload.user_id).first();
  if (!user) {
    return c.json({ error: '未登录', detail: '未登录' }, 401);
  }
  c.set('uid', payload.user_id);
  await next();
};

// ============ 健康检查 ============
app.get('/api/health', (c) => c.json({
  status: 'healthy', version: '1.1.0', timestamp: new Date().toISOString(),
}));

// ============ AI 流式代理 — 纯透传（免费版 10ms CPU 够用：不解析、不 TransformStream） ============
app.post('/api/ai/stream', async (c) => {
  const key = c.env.DEEPSEEK_API_KEY;
  if (!key) return c.json({ error: 'Server API key not configured', detail: 'Server API key not configured' }, 500);
  try {
    const body = await c.req.json();
    const base = (c.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com').replace(/\/+$/, '');
    const upstream = await fetch(`${base}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`,
      },
      body: JSON.stringify({
        ...body,
        model: body.model || c.env.DEFAULT_MODEL || 'deepseek-chat',
      }),
      signal: AbortSignal.timeout(120000),
    });
    if (!upstream.ok) {
      // 读一段错误体透传（SSE 错误也常是 JSON）
      const text = await upstream.text();
      return c.json({ error: `DeepSeek ${upstream.status}: ${text.slice(0, 300)}`, detail: `DeepSeek ${upstream.status}: ${text.slice(0, 300)}` }, upstream.status >= 500 ? 502 : upstream.status);
    }
    return new Response(upstream.body, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (e) {
    return c.json({ error: `AI 服务异常: ${e.message}`, detail: `AI 服务异常: ${e.message}` }, 500);
  }
});

// ============ RAG 问答（Worker 无向量库 → 直连 LLM，sources 恒空；语义与 Render kb_ready=false 一致） ============
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function callLLM(apiKey, baseUrl, model, question) {
  const resp = await fetch(`${(baseUrl || 'https://api.deepseek.com').replace(/\/+$/, '')}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
    body: JSON.stringify({
      model: model || 'deepseek-chat',
      messages: [
        { role: 'system', content: '你是一个哲学知识助手。请用中文回答用户的问题，尽可能准确和详细。如果不知道，请如实说明。' },
        { role: 'user', content: question },
      ],
      temperature: 0.7,
      max_tokens: 1024,
    }),
    signal: AbortSignal.timeout(60000),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  return data.choices?.[0]?.message?.content || '';
}

app.post('/api/qa', async (c) => {
  let body;
  try { body = await c.req.json(); } catch { return c.json({ error: '请求体非法', detail: '请求体非法' }, 400); }
  const question = (body.question || '').trim();
  if (!question) return c.json({ error: '问题不能为空', detail: '问题不能为空' }, 400);

  let answer = '';
  let lastErr = '';
  if (body.api_key) {
    // 用户自带 Key：直连 DeepSeek，3 次指数退避
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        answer = await callLLM(body.api_key, 'https://api.deepseek.com', body.model || null, question);
        break;
      } catch (e) { lastErr = e.message; if (attempt < 2) await sleep(500 * (2 ** attempt)); }
    }
  } else if (c.env.DEEPSEEK_API_KEY) {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        answer = await callLLM(c.env.DEEPSEEK_API_KEY, c.env.DEEPSEEK_BASE_URL, body.model || c.env.DEFAULT_MODEL, question);
        break;
      } catch (e) { lastErr = e.message; if (attempt < 2) await sleep(500 * (2 ** attempt)); }
    }
  } else {
    lastErr = 'Server API key not configured';
  }

  const result = answer
    ? { answer, sources: [], question }
    : { answer: `问答服务暂时不可用: ${lastErr}\n\n请确认已在设置中配置了有效的 API Key。`, sources: [], question };

  // 带 JWT 则保存聊天历史（Render 语义；前端 QAPage 实际不传 Authorization，此处保险）
  const token = (c.req.header('Authorization') || '').replace('Bearer ', '');
  if (token) {
    try {
      const payload = await verifyJWT(token, c.env.JWT_SECRET);
      if (payload?.user_id) {
        const db = c.env.deepphilosophy_db;
        const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
        await db.prepare('INSERT INTO chat_history (user_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)')
          .bind(payload.user_id, 'user', question, null, now).run();
        await db.prepare('INSERT INTO chat_history (user_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)')
          .bind(payload.user_id, 'assistant', result.answer, JSON.stringify([]), now).run();
      }
    } catch { /* 历史保存失败不影响回答 */ }
  }
  return c.json(result);
});

// ============ 书籍文件下载 — oss 302 直链零流量；仅 github 的走 Range 代理 ============
const MIME = { '.pdf': 'application/pdf', '.epub': 'application/epub+zip', '.txt': 'text/plain', '.md': 'text/markdown' };
const UA = 'DeepPhilosophy/1.0';

app.get('/api/books/:id/file', async (c) => {
  const book = booksData[c.req.param('id')];
  if (!book) return c.json({ error: '书籍未找到', detail: '书籍未找到' }, 404);

  // GitHub 优先：OSS bucket 现处于 UserDisable（阿里云账号停用，403 全部直链），
  // GitHub Release 公开下载无防盗链，Range 代理可覆盖 PDF 逐页加载
  if (book.github) {
    const ext = '.' + (book.ext || '');
    const mime = MIME[ext] || 'application/octet-stream';
    const rangeHeader = c.req.header('range') || '';
    // 无 Range 且大文件 → 302 直链 GitHub（避免免费 Worker 全量中转过流量）
    if (!rangeHeader && (book.size > 100 * 1024 * 1024)) return c.redirect(book.github, 302);

    const headers = { 'User-Agent': UA };
    if (rangeHeader) {
      const m = rangeHeader.match(/bytes=(\d+)-(\d*)/);
      if (m) {
        const start = parseInt(m[1], 10);
        const end = m[2] ? parseInt(m[2], 10) : start + 2097151; // 默认 2MB 块（PDF 逐页加载靠这个）
        headers['Range'] = `bytes=${start}-${end}`;
      }
    }
    try {
      const src = await fetch(book.github, { headers, signal: AbortSignal.timeout(30000) });
      if (!src.ok) return c.json({ error: `下载失败: HTTP ${src.status}`, detail: `下载失败: HTTP ${src.status}` }, 502);
      const outHeaders = new Headers();
      outHeaders.set('Content-Type', mime);
      outHeaders.set('Accept-Ranges', 'bytes');
      if (src.headers.get('Content-Range')) outHeaders.set('Content-Range', src.headers.get('Content-Range'));
      if (src.headers.get('Content-Length')) outHeaders.set('Content-Length', src.headers.get('Content-Length'));
      return new Response(src.body, { status: src.status, headers: outHeaders });
    } catch (e) {
      return c.json({ error: `下载失败: ${e.message}`, detail: `下载失败: ${e.message}` }, 502);
    }
  }

  return c.json({ error: '书籍未找到', detail: '书籍未找到' }, 404);
});

// ============ 章内图片 — 302 直链 OSS（Render 迁移遗漏补回 2026-08-11） ============
app.get('/api/books/:id/image/:name', (c) => {
  const name = c.req.param('name');
  if (!/^[A-Za-z0-9_\-\.]+$/.test(name) || !/\.(webp|png|jpg|jpeg)$/i.test(name)) {
    return c.json({ error: '非法的图片名', detail: '非法的图片名' }, 400);
  }
  return c.redirect(`https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/${name}`, 302);
});

// ============ 统计 ============
app.get('/api/stats', (c) => {
  c.header('Cache-Control', 'max-age=300');
  return c.json(statsData);
});

app.get('/api/admin/stats', async (c) => {
  // 2026-08-14: 密码从 query 参数改为 X-Admin-Password header（不进日志/历史）+ 恒定时间比较
  const pw = c.req.header('X-Admin-Password') || '';
  if (!c.env.ADMIN_PASSWORD) return c.json({ error: '管理后台未配置（请设置 ADMIN_PASSWORD 环境变量）', detail: '管理后台未配置' }, 503);
  if (!(await safeEqual(pw, c.env.ADMIN_PASSWORD))) return c.json({ error: '密码错误', detail: '密码错误' }, 403);
  const { results } = await c.env.deepphilosophy_db.prepare('SELECT id, username, created_at FROM users ORDER BY id').all();
  const users = results.map(u => ({ id: u.id, username: u.username, created_at: u.created_at || '' }));
  return c.json({ stats: adminStatsData, users, user_count: users.length });
});

// ============ 阅读历史 ============
app.get('/api/history/reading', requireAuth, async (c) => {
  const uid = c.get('uid');
  const { results } = await c.env.deepphilosophy_db.prepare(
    'SELECT book_id, book_title, book_author, progress_page, progress_percent, last_read_at FROM reading_history WHERE user_id = ? ORDER BY last_read_at DESC LIMIT 50'
  ).bind(uid).all();
  return c.json({ history: results });
});

app.post('/api/history/reading', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  if (!b.book_id) return c.json({ error: 'book_id 必填', detail: 'book_id 必填' }, 400);
  const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
  await c.env.deepphilosophy_db.prepare(
    `INSERT INTO reading_history (user_id, book_id, book_title, book_author, progress_page, progress_percent, last_read_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(user_id, book_id) DO UPDATE SET
       book_title = excluded.book_title, book_author = excluded.book_author,
       progress_page = excluded.progress_page, progress_percent = excluded.progress_percent,
       last_read_at = excluded.last_read_at`
  ).bind(uid, b.book_id || '', b.book_title || '', b.book_author || '', b.page || 1, b.percent || 0, now).run();
  return c.json({ success: true });
});

// 清空阅读记录（2026-08-12: 前端"清空"按钮曾只清本地 → 云端残留 → sync 合并复活）
app.delete('/api/history/reading', requireAuth, async (c) => {
  await c.env.deepphilosophy_db.prepare('DELETE FROM reading_history WHERE user_id = ?').bind(c.get('uid')).run();
  return c.json({ success: true });
});

// ============ 聊天历史 ============
app.get('/api/history/chat', requireAuth, async (c) => {
  const uid = c.get('uid');
  const { results } = await c.env.deepphilosophy_db.prepare(
    'SELECT role, content, sources, created_at FROM chat_history WHERE user_id = ? ORDER BY created_at ASC LIMIT 100'
  ).bind(uid).all();
  return c.json({ messages: results });
});

app.post('/api/history/chat', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
  await c.env.deepphilosophy_db.prepare(
    'INSERT INTO chat_history (user_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)'
  ).bind(uid, b.role || 'user', b.content || '', b.sources || null, now).run();
  return c.json({ success: true });
});

app.delete('/api/history/chat', requireAuth, async (c) => {
  await c.env.deepphilosophy_db.prepare('DELETE FROM chat_history WHERE user_id = ?').bind(c.get('uid')).run();
  return c.json({ success: true });
});

// ============ 批注笔记 ============
app.post('/api/notes/save', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  if (!b.book_id) return c.json({ error: 'book_id 必填', detail: 'book_id 必填' }, 400);
  await c.env.deepphilosophy_db.prepare(
    `INSERT INTO book_notes (user_id, book_id, note_text, updated_at)
     VALUES (?, ?, ?, datetime('now'))
     ON CONFLICT(user_id, book_id) DO UPDATE SET note_text = excluded.note_text, updated_at = datetime('now')`
  ).bind(uid, b.book_id, b.note_text || '').run();
  return c.json({ success: true });
});

// 新端点：ReaderPage 一直用 /notes/load?book_id= 但 Render 只有 /notes/{book_id} —— 此处补上
app.get('/api/notes/load', requireAuth, async (c) => {
  const uid = c.get('uid');
  const bookId = c.req.query('book_id') || '';
  const row = await c.env.deepphilosophy_db.prepare(
    'SELECT note_text FROM book_notes WHERE user_id = ? AND book_id = ?'
  ).bind(uid, bookId).first();
  return c.json({ note_text: row?.note_text || '' });
});

app.get('/api/notes/:book_id', requireAuth, async (c) => {
  const uid = c.get('uid');
  const row = await c.env.deepphilosophy_db.prepare(
    'SELECT note_text FROM book_notes WHERE user_id = ? AND book_id = ?'
  ).bind(uid, c.req.param('book_id')).first();
  return c.json({ note_text: row?.note_text || '' });
});

app.get('/api/notes', requireAuth, async (c) => {
  const uid = c.get('uid');
  const { results } = await c.env.deepphilosophy_db.prepare(
    'SELECT book_id, note_text FROM book_notes WHERE user_id = ?'
  ).bind(uid).all();
  const notes = {};
  for (const r of results) notes[r.book_id] = r.note_text;
  return c.json({ notes });
});

// ============ 书内 AI 对话 ============
app.post('/api/book-chat/save', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
  await c.env.deepphilosophy_db.prepare(
    'INSERT INTO book_chat (user_id, book_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)'
  ).bind(uid, b.book_id || '', b.role || 'user', b.content || '', now).run();
  return c.json({ success: true });
});

app.get('/api/book-chat/:book_id', requireAuth, async (c) => {
  const uid = c.get('uid');
  const { results } = await c.env.deepphilosophy_db.prepare(
    'SELECT role, content, created_at FROM book_chat WHERE user_id = ? AND book_id = ? ORDER BY id ASC LIMIT 50'
  ).bind(uid, c.req.param('book_id')).all();
  return c.json({ messages: results });
});

app.delete('/api/book-chat/:book_id', requireAuth, async (c) => {
  await c.env.deepphilosophy_db.prepare(
    'DELETE FROM book_chat WHERE user_id = ? AND book_id = ?'
  ).bind(c.get('uid'), c.req.param('book_id')).run();
  return c.json({ success: true });
});

// ============ 用户资料 ============
app.put('/api/user/profile', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  const newName = (b.username || '').trim();
  if (!newName) return c.json({ error: '用户名不能为空', detail: '用户名不能为空' }, 400);
  const db = c.env.deepphilosophy_db;
  const dup = await db.prepare('SELECT id FROM users WHERE username = ? AND id != ?').bind(newName, uid).first();
  if (dup) return c.json({ error: '用户名已被占用', detail: '用户名已被占用' }, 409);
  await db.prepare('UPDATE users SET username = ? WHERE id = ?').bind(newName, uid).run();
  return c.json({ status: 'ok', username: newName });
});

app.put('/api/user/password', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  if (!b.new_password || String(b.new_password).length < 4) {
    return c.json({ error: '新密码至少4位', detail: '新密码至少4位' }, 400);
  }
  const db = c.env.deepphilosophy_db;
  const user = await db.prepare('SELECT password_hash FROM users WHERE id = ?').bind(uid).first();
  if (!user) return c.json({ error: '未登录', detail: '未登录' }, 401);
  const pw = await checkPw(b.old_password || '', user.password_hash);
  if (pw === 'SCRYPT_LEGACY') {
    return c.json({ error: '该账号由旧系统迁移而来，密码体系已升级，请联系管理员重置密码后再登录', detail: '该账号由旧系统迁移而来，密码体系已升级，请联系管理员重置密码后再登录' }, 403);
  }
  if (!pw) return c.json({ error: '原密码错误', detail: '原密码错误' }, 403);
  const hash = await hashPwPBKDF2(b.new_password, crypto.randomUUID());   // PBKDF2 加固
  await db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').bind(hash, uid).run();
  return c.json({ status: 'ok' });
});

app.get('/api/user/avatar', requireAuth, async (c) => {
  const uid = c.get('uid');
  const user = await c.env.deepphilosophy_db.prepare('SELECT avatar FROM users WHERE id = ?').bind(uid).first();
  return c.json({ avatar: user?.avatar || '' });
});

app.post('/api/user/avatar', requireAuth, async (c) => {
  const uid = c.get('uid');
  const b = await c.req.json();
  await c.env.deepphilosophy_db.prepare('UPDATE users SET avatar = ? WHERE id = ?').bind(b.avatar || '', uid).run();
  return c.json({ status: 'ok' });
});

export default app;
