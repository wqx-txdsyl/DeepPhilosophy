# 数据库规范（2026-08-14 统一后端后）

## 权威声明

- **生产用户数据唯一源 = Cloudflare D1 `deepphilosophy-db`**（Workers auth + api 读写）
- **本地开发 = SQLite**（`backend/data/users.db`，与 D1 同 schema，`migrate_users_to_d1.py` 导出）
- 两处 schema 必须保持一致：改表先改 `workers/api/migrations/001_schema.sql`，再同步 `backend/auth.py` 的 `init_db`（本地 SQLite 建表）

## users（auth worker initDB 创建）

| 列 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| username | TEXT UNIQUE NOT NULL | |
| password_hash | TEXT NOT NULL | `pbkdf2:{iter}:{salt}:{hex}`（2026-08-14 起）；旧格式 `{salt}:{sha256}` / `sha256:...` / `scrypt:...` 登录时自动升级 |
| avatar | TEXT DEFAULT '' | |
| created_at | TEXT | 补列命令见 001_schema.sql 头注释 |

## 业务表（D1 001_schema.sql = 权威）

- `reading_history(user_id, book_id UNIQUE, book_title, book_author, progress_page, progress_percent, last_read_at)`
- `chat_history(user_id, role, content, sources, created_at)`
- `book_notes(user_id, book_id UNIQUE, note_text, updated_at)`
- `book_chat(user_id, book_id, role, content, created_at)`

## 智能体记忆（非用户库）

- `backend/data/agent_memory.json` — 多轮修改记忆（作文/生图/思想实验/辩论），**按用户隔离**
  （key = `u{id}` / `ip:{ip}` / `default`），原子写（tmp+rename），见 `routes/agent.py::_mem_slot`
- 不属于 D1：体积小、本地敏感度低；未来上 VPS 可迁 SQLite 表

## 迁移流程（SQLite → D1）

1. `python backend/tools/migrate_users_to_d1.py` 生成 INSERT SQL
2. `wrangler d1 execute deepphilosophy-db --remote --file <sql>` 导入
3. 历史遗留（已废弃，勿再启用）：`auth.py::_sync_db` 整库上传 GitHub Release/OSS 的 last-writer-wins 逻辑
