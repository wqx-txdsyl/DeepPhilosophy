"""
开发者管理后台 —— 访问统计 + 用户管理（GitHub Release 持久化）
"""
import os, json, time, sqlite3, urllib.request, urllib.parse, logging, threading
from datetime import datetime

_log = logging.getLogger("admin")

STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "admin_stats.json")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
# 生产环境必须设置 ADMIN_PASSWORD 环境变量，否则管理后台不可用
_GITHUB_REPO = os.getenv("GITHUB_REPO", "wqx-txdsyl/DeepPhilosophy")
_GITHUB_TAG = "stats-v1"
_GITHUB_ASSET = "admin_stats.json"
_GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
# 无代理 opener（跳过 urllib 代理检测: proxy_bypass_registry → socket.getfqdn 反向 DNS 可达 11s 超时）
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
# GitHub 备份节流（避免每次访问都打 GitHub API, 也防限流）
_last_backup_ts = 0.0
_backup_lock = threading.Lock()


def _gh_request(method, path, body=None, json_body=True, host="api.github.com"):
    url = f"https://{host}{path}"
    headers = {"Authorization": f"Bearer {_GH_TOKEN}", "Accept": "application/vnd.github+json"}
    data = None
    if body is not None:
        if json_body:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        else:
            data = body
            headers["Content-Type"] = "application/octet-stream"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _OPENER.open(req, timeout=60) as resp:
            raw = resp.read()
            if raw: return resp.status, json.loads(raw)
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        _log.warning(f"GitHub API error: {e}")
        return 0, None


def _gh_backup_stats(stats_json_bytes):
    """备份统计到 GitHub Release"""
    if not _GH_TOKEN: return False
    try:
        # Get or create release
        status, result = _gh_request("GET", f"/repos/{_GITHUB_REPO}/releases/tags/{_GITHUB_TAG}")
        release_id = result.get("id") if result and status == 200 else None

        if not release_id:
            status, result = _gh_request("POST", f"/repos/{_GITHUB_REPO}/releases", body={
                "tag_name": _GITHUB_TAG, "name": "Stats Backup",
                "body": "Auto backup of admin stats", "draft": False, "prerelease": False
            })
            release_id = result.get("id") if result and status == 201 else None

        if not release_id: return False

        # Upload asset
        path = f"/repos/{_GITHUB_REPO}/releases/{release_id}/assets?name={urllib.parse.quote(_GITHUB_ASSET)}"
        status, _ = _gh_request("POST", path, body=stats_json_bytes, json_body=False, host="uploads.github.com")
        return status == 201
    except Exception as e:
        _log.warning(f"Stats backup error: {e}")
        return False


def _gh_restore_stats():
    """从 GitHub Release 恢复统计"""
    if not _GH_TOKEN: return None
    try:
        status, result = _gh_request("GET", f"/repos/{_GITHUB_REPO}/releases/tags/{_GITHUB_TAG}")
        if status != 200 or not result: return None
        assets = result.get("assets", [])
        for a in assets:
            if a.get("name") == _GITHUB_ASSET:
                url = a.get("browser_download_url")
                if url:
                    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_GH_TOKEN}", "User-Agent": "DP/1.2"})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log.warning(f"Stats restore error: {e}")
    return None


# ── 访问统计（S14, audit 2026-08-17）────────────────────────
# 原实现每请求整文件读改写（load_stats→record_visit→save_stats, 无锁, 并发计数丢失 + 磁盘写）。
# 改为: 内存聚合（单锁保护, O(1)）+ 定时落盘（daemon 线程周期 flush, 有变化才写盘）。
STATS_LOCK = threading.Lock()
_stats = None          # 内存统计 dict（首次访问时从本地文件 / GitHub 恢复）
_stats_loaded = False
_stats_dirty = False
STATS_FLUSH_SECONDS = float(os.getenv("ADMIN_STATS_FLUSH_SECONDS", "60"))


def _ensure_loaded_locked():
    """内存统计初始化（调用方须持有 STATS_LOCK）: 本地文件 → GitHub 恢复 → 全新"""
    global _stats, _stats_loaded, _stats_dirty
    if _stats_loaded:
        return
    _stats = None
    # 1. Try local file first
    try:
        with open(STATS_FILE, "r") as f:
            _stats = json.load(f)
    except Exception as e:
        _log.warning(f"Stats local load failed: {e}")
    # 2. Try GitHub backup
    if _stats is None:
        restored = _gh_restore_stats()
        if restored:
            _stats = restored
            _stats_dirty = True  # 恢复值随首次 flush 落盘本地
            _log.info("Stats restored from GitHub Release")
    # 3. Fresh start
    if _stats is None:
        _stats = {
            "total_visits": 0,
            "daily_visits": {},
            "page_views": {},
            "started_at": datetime.now().isoformat(),
        }
    _stats_loaded = True


def load_stats():
    """返回统计深拷贝（管理后台读取; 内存聚合版, 不再每请求读盘）"""
    with STATS_LOCK:
        _ensure_loaded_locked()
        return json.loads(json.dumps(_stats, ensure_ascii=False))


def save_stats(stats):
    """兼容入口: 整份写入统计（替换内存并标记落盘; 旧版直写磁盘行为由 flush 承接）"""
    global _stats, _stats_loaded, _stats_dirty
    with STATS_LOCK:
        _stats = stats
        _stats_loaded = True
        _stats_dirty = True


def record_visit(path="/"):
    """内存聚合访问计数（单锁保护; 标记 dirty, 由定时线程落盘, 请求路径零磁盘 IO）"""
    global _stats_dirty
    with STATS_LOCK:
        _ensure_loaded_locked()
        _stats["total_visits"] += 1
        today = datetime.now().strftime("%Y-%m-%d")
        _stats["daily_visits"][today] = _stats["daily_visits"].get(today, 0) + 1
        _stats["page_views"][path] = _stats["page_views"].get(path, 0) + 1
        _stats_dirty = True


def flush_stats():
    """内存统计 → 本地文件（+ GitHub 备份, 60s 节流）; 无变化不写盘"""
    global _stats_dirty
    with STATS_LOCK:
        _ensure_loaded_locked()
        if not _stats_dirty:
            return
        snap = json.dumps(_stats, ensure_ascii=False, indent=2)
        _stats_dirty = False
    try:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, "w") as f:
            f.write(snap)
    except Exception as e:
        _log.warning(f"Stats local save failed: {e}")
    # GitHub 备份（60s 节流, best-effort）
    global _last_backup_ts
    with _backup_lock:
        now = time.time()
        if now - _last_backup_ts < 60:
            return
        _last_backup_ts = now
    try:
        _gh_backup_stats(snap.encode("utf-8"))
    except Exception as e:
        _log.warning(f"Stats GitHub backup failed: {e}")


def _flush_loop():
    """定时落盘线程（daemon）: 每 STATS_FLUSH_SECONDS 秒 flush 一次"""
    while True:
        time.sleep(STATS_FLUSH_SECONDS)
        try:
            flush_stats()
        except Exception:
            _log.warning("Stats flush failed", exc_info=True)


threading.Thread(target=_flush_loop, daemon=True).start()

def get_users():
    db_path = os.path.join(os.path.dirname(__file__), "data", "users.db")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT id, username, created_at FROM users ORDER BY id").fetchall()
        return [{"id": r[0], "username": r[1], "created_at": r[2]} for r in rows]
    finally:
        conn.close()
