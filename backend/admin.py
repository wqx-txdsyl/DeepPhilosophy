"""
开发者管理后台 —— 访问统计 + 用户管理（GitHub Release 持久化）
"""
import os, json, time, sqlite3, urllib.request, urllib.parse, logging
from datetime import datetime

_log = logging.getLogger("admin")

STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "admin_stats.json")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "wqx090915")
_GITHUB_REPO = os.getenv("GITHUB_REPO", "wqx-txdsyl/DeepPhilosophy")
_GITHUB_TAG = "stats-v1"
_GITHUB_ASSET = "admin_stats.json"
_GH_TOKEN = os.getenv("GITHUB_TOKEN", "")


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
        with urllib.request.urlopen(req, timeout=60) as resp:
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


def load_stats():
    # 1. Try local file first
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        pass
    # 2. Try GitHub backup
    restored = _gh_restore_stats()
    if restored:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, "w") as f:
            json.dump(restored, f, ensure_ascii=False, indent=2)
        _log.info("Stats restored from GitHub Release")
        return restored
    # 3. Fresh start
    return {
        "total_visits": 0,
        "daily_visits": {},
        "page_views": {},
        "started_at": datetime.now().isoformat(),
    }


def save_stats(stats):
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    # Async backup to GitHub (best-effort)
    try:
        _gh_backup_stats(json.dumps(stats, ensure_ascii=False).encode("utf-8"))
    except:
        pass

def record_visit(path="/"):
    stats = load_stats()
    stats["total_visits"] += 1
    today = datetime.now().strftime("%Y-%m-%d")
    stats["daily_visits"][today] = stats["daily_visits"].get(today, 0) + 1
    stats["page_views"][path] = stats["page_views"].get(path, 0) + 1
    save_stats(stats)

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
