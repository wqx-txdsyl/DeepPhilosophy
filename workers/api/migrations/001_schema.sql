-- 001_schema.sql — api worker 业务表（D1 deepphilosophy-db）
-- users 表由 auth worker 的 initDB 创建；created_at/profile 补列用单独命令容错执行：
--   wrangler d1 execute deepphilosophy-db --remote --command "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='created_at'" 先查再 ALTER
-- 所有表 CREATE TABLE IF NOT EXISTS，幂等。不建 tokens 表（随机 token 体系已废弃，统一 JWT）。

CREATE TABLE IF NOT EXISTS reading_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  book_id TEXT NOT NULL,
  book_title TEXT NOT NULL,
  book_author TEXT NOT NULL,
  progress_page INTEGER DEFAULT 1,
  progress_percent REAL DEFAULT 0,
  last_read_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  UNIQUE(user_id, book_id)
);

CREATE TABLE IF NOT EXISTS chat_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  sources TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS book_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  book_id TEXT NOT NULL,
  note_text TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, book_id)
);

CREATE TABLE IF NOT EXISTS book_chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  book_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
