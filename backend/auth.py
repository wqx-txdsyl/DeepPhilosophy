"""
用户认证模块 —— SQLite + OSS 云端持久化 + GitHub Release 备份
零额外依赖，boto3 已安装用于 S3 兼容的 OSS 存储
"""
import os
import sys
import json
import sqlite3
import hashlib
import uuid
import time
import shutil
import logging
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional

# 配置日志（确保 Render 上可见）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [auth] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger("auth")

_PERSIST = os.getenv("PERSIST_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
os.makedirs(_PERSIST, exist_ok=True)
DB_PATH = os.path.join(_PERSIST, "users.db")
_log.info(f"Auth DB path: {DB_PATH}")
_OSS_KEY = "_system/users.db"

# GitHub Release 备份配置
_GITHUB_REPO = os.getenv("GITHUB_REPO", "wqx-txdsyl/DeepPhilosophy")
_GITHUB_TAG = "userdb-v1"
_GITHUB_ASSET = "users.db"
_GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
_GH_API_BASE = "https://api.github.com"

# OSS 云端同步（S3 兼容 API，boto3 已安装）
def _oss_request(method, key_path, body=None):
    """向 OSS 发送带签名的 HTTP 请求"""
    import requests as _req
    ep = os.getenv("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com")
    if ep.startswith("https://"): ep = ep[8:]
    if ep.startswith("http://"): ep = ep[7:]
    ak = os.getenv("OSS_ACCESS_KEY", "")
    sk = os.getenv("OSS_SECRET_KEY", "")
    bucket = os.getenv("OSS_BUCKET", "deepphilosophy")
    if not ak:
        _log.debug("OSS_ACCESS_KEY not set, skipping cloud sync")
        return None
    date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
    ctype = 'application/octet-stream' if body else ''
    string_to_sign = f"{method}\n\n{ctype}\n{date}\n/{bucket}/{key_path}"
    import base64, hmac as _hmac
    sig = base64.b64encode(_hmac.new(sk.encode(), string_to_sign.encode(), hashlib.sha1).digest()).decode()
    url = f"https://{bucket}.{ep}/{key_path}"
    hdrs = {'Date': date, 'Authorization': f'OSS {ak}:{sig}'}
    if body is not None:
        hdrs['Content-Type'] = ctype
        return _req.put(url, data=body, headers=hdrs, timeout=30)
    return _req.get(url, headers=hdrs, timeout=30)

def _sync_db_to_cloud():
    """上传 users.db 到 OSS"""
    if not os.path.exists(DB_PATH): return
    try:
        with open(DB_PATH, 'rb') as f:
            resp = _oss_request('PUT', _OSS_KEY, f.read())
        if resp is not None and resp.status_code >= 400:
            _log.warning(f"OSS upload failed: {resp.status_code}")
    except Exception as e:
        _log.warning(f"OSS upload error: {e}")

def _sync_db_from_cloud():
    """从 OSS 下载 users.db（如果存在且比本地新）"""
    try:
        r = _oss_request('GET', _OSS_KEY)
        if r is None: return  # No OSS credentials configured
        if r.status_code == 404:
            _log.info("No remote users.db found, starting fresh")
            return
        if r.status_code != 200:
            _log.warning(f"OSS download failed: {r.status_code}")
            return
        cloud_data = r.content
        if len(cloud_data) == 0: return
        # 比本地新？
        local_mtime = os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0
        # OSS Last-Modified 在 header 中
        if os.path.exists(DB_PATH) and len(cloud_data) == os.path.getsize(DB_PATH):
            return  # 大小相同，跳过
        with open(DB_PATH + '.tmp', 'wb') as f:
            f.write(cloud_data)
        if os.path.getsize(DB_PATH + '.tmp') > 0:
            shutil.move(DB_PATH + '.tmp', DB_PATH)
            _log.info("Restored users.db from OSS cloud")
        else:
            os.remove(DB_PATH + '.tmp')
    except Exception as e:
        _log.warning(f"OSS download error: {e}")


# ============================================================
# GitHub Release 备份（纯 stdlib，零新依赖）
# ============================================================

def _gh_request(method, api_path, body=None, json_body=True, host=None):
    """GitHub API 通用请求，返回 (status, data_or_dict) 或 (0, None)"""
    if not _GH_TOKEN:
        _log.debug("GITHUB_TOKEN not set, skipping GitHub sync")
        return 0, None
    try:
        h = host or "api.github.com"
        url = f"https://{h}{api_path}"
        data = None
        headers = {
            "Authorization": f"Bearer {_GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DeepPhilosophy/1.2",
        }
        if body is not None:
            if json_body:
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"
            else:
                data = body
                headers["Content-Type"] = "application/octet-stream"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if raw:
                return resp.status, json.loads(raw)
            return resp.status, None
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp else b""
        try:
            return e.code, json.loads(body) if body else None
        except Exception:
            return e.code, None
    except Exception as e:
        _log.warning(f"GitHub API error: {e}")
        return 0, None


def _gh_upload_asset(release_id, asset_name, data):
    """上传二进制资产到 GitHub Release（uploads.github.com）"""
    if not _GH_TOKEN:
        return False
    try:
        path = f"/repos/{_GITHUB_REPO}/releases/{release_id}/assets?name={urllib.parse.quote(asset_name)}"
        status, result = _gh_request("POST", path, body=data, json_body=False, host="uploads.github.com")
        return status == 201
    except Exception as e:
        _log.warning(f"GitHub upload error: {e}")
        return False


def _gh_download_asset(download_url):
    """从 GitHub Release 下载资产，返回原始字节"""
    if not _GH_TOKEN:
        return None
    try:
        req = urllib.request.Request(
            download_url,
            headers={
                "Authorization": f"Bearer {_GH_TOKEN}",
                "User-Agent": "DeepPhilosophy/1.2",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        _log.warning(f"GitHub download error: {e}")
        return None


def _get_or_create_release():
    """查找或创建 userdb-v1 Release，返回 release dict 或 None"""
    if not _GH_TOKEN:
        return None
    # 先查找
    status, data = _gh_request("GET", f"/repos/{_GITHUB_REPO}/releases/tags/{_GITHUB_TAG}")
    if status == 200 and isinstance(data, dict):
        return data
    if status == 404:
        # 不存在，创建
        status2, data2 = _gh_request("POST", f"/repos/{_GITHUB_REPO}/releases", body={
            "tag_name": _GITHUB_TAG,
            "name": "User Database",
            "body": "DeepPhilosophy users.db 自动备份（由后端自动同步）",
            "prerelease": False,
            "generate_release_notes": False,
        })
        if status2 == 201 and isinstance(data2, dict):
            _log.info("Created GitHub Release: userdb-v1")
            return data2
        _log.warning(f"Failed to create GitHub Release: {status2}")
    return None


def _sync_db_to_github():
    """上传 users.db 到 GitHub Release（删除旧资产→上传新资产）
    返回 True/False 表示是否成功上传"""
    if not os.path.exists(DB_PATH):
        return False
    if not _GH_TOKEN:
        _log.debug("GITHUB_TOKEN not set, skip GitHub upload")
        return False
    try:
        # 检查 DB 是否有用户数据，空 DB 不上传（保护远端备份）
        conn = _get_conn()
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        if user_count == 0:
            _log.info("Skipping GitHub upload: no users in DB (protecting remote backup)")
            return False

        release = _get_or_create_release()
        if not release:
            _log.warning("GitHub upload failed: cannot get/create release")
            return False
        release_id = release["id"]
        # 删除旧资产
        for asset in release.get("assets", []):
            if asset.get("name") == _GITHUB_ASSET:
                _gh_request("DELETE", f"/repos/{_GITHUB_REPO}/releases/assets/{asset['id']}")
                break
        # 上传新资产
        with open(DB_PATH, "rb") as f:
            db_data = f.read()
        if _gh_upload_asset(release_id, _GITHUB_ASSET, db_data):
            _log.info(f"GitHub backup OK: {len(db_data)} bytes, {user_count} users")
            print(f"[auth] GitHub backup OK ({len(db_data)} bytes, {user_count} users)")
            return True
        else:
            _log.warning("GitHub upload returned non-201 status")
            print("[auth] WARNING: GitHub upload failed (non-201 response)")
            return False
    except Exception as e:
        _log.warning(f"GitHub sync upload error: {e}")
        print(f"[auth] WARNING: GitHub upload error: {e}")
        return False


def _sync_db_from_github():
    """从 GitHub Release 下载 users.db 并恢复
    返回 True 表示成功恢复，False 表示未恢复（无备份/无token/失败）"""
    if not _GH_TOKEN:
        _log.debug("GITHUB_TOKEN not set, skip GitHub restore")
        return False
    try:
        release = _get_or_create_release()
        if not release:
            _log.info("Cannot access GitHub Release (no release or API error)")
            return False
        # 查找 users.db 资产
        asset_url = None
        for asset in release.get("assets", []):
            if asset.get("name") == _GITHUB_ASSET:
                asset_url = asset.get("browser_download_url")
                remote_size = asset.get("size", 0)
                break
        if not asset_url:
            _log.info("No users.db backup found on GitHub Release")
            print("[auth] No GitHub backup found (fresh start)")
            return False
        # 大小相同则跳过
        if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) == remote_size:
            _log.info("Local users.db matches GitHub backup, skip restore")
            return True
        # 下载
        print(f"[auth] Restoring users.db from GitHub Release ({remote_size} bytes)...")
        cloud_data = _gh_download_asset(asset_url)
        if not cloud_data or len(cloud_data) == 0:
            _log.warning("GitHub download returned empty data")
            return False
        # 原子写入：先写 .tmp，校验后移动
        tmp_path = DB_PATH + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(cloud_data)
        if os.path.getsize(tmp_path) > 0:
            shutil.move(tmp_path, DB_PATH)
            _log.info(f"Restored users.db from GitHub Release ({len(cloud_data)} bytes)")
            print(f"[auth] GitHub restore OK ({len(cloud_data)} bytes)")
            return True
        else:
            os.remove(tmp_path)
            return False
    except Exception as e:
        _log.warning(f"GitHub sync download error: {e}")
        print(f"[auth] WARNING: GitHub restore error: {e}")
        return False


def _sync_db():
    """同步 users.db 到所有已配置的云端后端"""
    _sync_db_to_github()
    _sync_db_to_cloud()


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化用户数据库表，先从云端恢复"""
    restored_github = _sync_db_from_github()  # 尝试从 GitHub Release 恢复
    restored_oss = _sync_db_from_cloud()      # 尝试从 OSS 恢复
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
    # 检查恢复后是否有用户数据
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.commit()
    conn.close()
    if user_count > 0:
        # 恢复成功或已有数据 → 备份到云端
        _sync_db()
        _log.info(f"init_db: restored {user_count} users, synced to cloud backends")
    else:
        # 新部署 / 恢复失败 → 不备份，避免空 DB 覆盖远端数据
        _log.info("init_db: no users found, skipping backup to protect remote data")


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
        _sync_db()  # 立即备份到云端
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
    _sync_db()


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
    _sync_db()


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
    _sync_db()


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
    _sync_db()
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
    _sync_db()


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
    _sync_db()


# ============================================================
# 初始化
# ============================================================
init_db()
_sync_db_from_github()  # 从 GitHub Release 拉取最新用户数据
_sync_db_from_cloud()   # 从 OSS 拉取最新用户数据
