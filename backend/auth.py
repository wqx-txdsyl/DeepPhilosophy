"""
用户认证模块 —— SQLite + Token 认证
零额外依赖，纯 Python 标准库实现
"""
import os
import sqlite3
import hashlib
import uuid
import time
from datetime import datetime
from typing import Optional

_PERSIST = os.getenv("PERSIST_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
os.makedirs(_PERSIST, exist_ok=True)
DB_PATH = os.path.join(_PERSIST, "users.db")


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化用户数据库表"""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS reading_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id TEXT NOT NULL,
            book_title TEXT NOT NULL,
            book_author TEXT NOT NULL,
            progress_page INTEGER DEFAULT 1,
            progress_percent REAL DEFAULT 0,
            last_read_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, book_id)
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS book_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id TEXT NOT NULL,
            note_text TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, book_id)
        );

        CREATE TABLE IF NOT EXISTS book_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """密码哈希（SHA-256 + salt）"""
    if salt is None:
        salt = uuid.uuid4().hex
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return h, salt


def register(username: str, password: str) -> dict:
    """用户注册"""
    if not username or not password:
        return {"success": False, "error": "用户名和密码不能为空"}
    if len(username) < 2:
        return {"success": False, "error": "用户名至少2个字符"}
    if len(password) < 4:
        return {"success": False, "error": "密码至少4个字符"}

    conn = _get_conn()
    try:
        pw_hash, salt = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, pw_hash, salt),
        )
        conn.commit()
        return {"success": True, "message": "注册成功"}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "用户名已存在"}
    finally:
        conn.close()


def login(username: str, password: str) -> dict:
    """用户登录，返回 token"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, password_hash, salt FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if not row:
            return {"success": False, "error": "用户名或密码错误"}

        pw_hash, _ = _hash_password(password, row["salt"])
        if pw_hash != row["password_hash"]:
            return {"success": False, "error": "用户名或密码错误"}

        # 生成 token（7天有效）
        token = uuid.uuid4().hex + uuid.uuid4().hex
        expires = datetime.now().timestamp() + 7 * 24 * 3600

        conn.execute(
            "INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, row["id"], datetime.fromtimestamp(expires).isoformat()),
        )
        # 清理旧 token
        conn.execute(
            "DELETE FROM tokens WHERE user_id = ? AND expires_at < datetime('now')",
            (row["id"],),
        )
        conn.commit()

        return {
            "success": True,
            "token": token,
            "username": username,
            "message": "登录成功",
        }
    finally:
        conn.close()


def get_user_by_token(token: str) -> Optional[dict]:
    """通过 token 验证用户身份"""
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT u.id, u.username, t.expires_at
               FROM tokens t JOIN users u ON t.user_id = u.id
               WHERE t.token = ?""",
            (token,),
        ).fetchone()

        if not row:
            return None
        if datetime.fromisoformat(row["expires_at"]).timestamp() < time.time():
            return None

        return {"id": row["id"], "username": row["username"]}
    finally:
        conn.close()


# ============================================================
# 阅读历史
# ============================================================

def save_reading_progress(user_id: int, book_id: str, book_title: str,
                          book_author: str, page: int = 1, percent: float = 0):
    """保存/更新阅读进度"""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO reading_history (user_id, book_id, book_title, book_author, progress_page, progress_percent, last_read_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
           ON CONFLICT(user_id, book_id) DO UPDATE SET
           progress_page=excluded.progress_page,
           progress_percent=excluded.progress_percent,
           last_read_at=datetime('now')""",
        (user_id, book_id, book_title, book_author, page, percent),
    )
    conn.commit()
    conn.close()


def get_reading_history(user_id: int, limit: int = 50) -> list[dict]:
    """获取阅读历史"""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT book_id, book_title, book_author, progress_page, progress_percent, last_read_at
           FROM reading_history WHERE user_id = ?
           ORDER BY last_read_at DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 聊天历史
# ============================================================

def save_chat_message(user_id: int, role: str, content: str, sources: Optional[str] = None):
    """保存聊天消息"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_history (user_id, role, content, sources) VALUES (?, ?, ?, ?)",
        (user_id, role, content, sources),
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id: int, limit: int = 100) -> list[dict]:
    """获取聊天历史"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, sources, created_at FROM chat_history "
        "WHERE user_id = ? ORDER BY created_at ASC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_chat_history(user_id: int):
    """清空聊天历史"""
    conn = _get_conn()
    conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ============================================================
# 批注笔记（按书+用户）
# ============================================================

def save_book_note(user_id: int, book_id: str, note_text: str) -> bool:
    """保存/更新批注"""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO book_notes (user_id, book_id, note_text, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(user_id, book_id) DO UPDATE SET
            note_text = excluded.note_text,
            updated_at = datetime('now')
    """, (user_id, book_id, note_text))
    conn.commit()
    conn.close()
    return True


def get_book_note(user_id: int, book_id: str) -> str:
    """获取批注内容"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT note_text FROM book_notes WHERE user_id = ? AND book_id = ?",
        (user_id, book_id),
    ).fetchone()
    conn.close()
    return row["note_text"] if row else ""


def get_all_book_notes(user_id: int) -> dict:
    """获取用户所有批注"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT book_id, note_text FROM book_notes WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {r["book_id"]: r["note_text"] for r in rows}


# ============================================================
# 书内 AI 对话（按书+用户）
# ============================================================

def save_book_chat(user_id: int, book_id: str, role: str, content: str):
    """保存书内AI对话消息"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO book_chat (user_id, book_id, role, content) VALUES (?, ?, ?, ?)",
        (user_id, book_id, role, content),
    )
    conn.commit()
    conn.close()


def get_book_chat(user_id: int, book_id: str, limit: int = 50) -> list[dict]:
    """获取书内AI对话历史"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, created_at FROM book_chat WHERE user_id = ? AND book_id = ? ORDER BY id ASC LIMIT ?",
        (user_id, book_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_book_chat(user_id: int, book_id: str):
    """清空书内AI对话"""
    conn = _get_conn()
    conn.execute("DELETE FROM book_chat WHERE user_id = ? AND book_id = ?", (user_id, book_id))
    conn.commit()
    conn.close()


# ============================================================
# 初始化
# ============================================================
init_db()
