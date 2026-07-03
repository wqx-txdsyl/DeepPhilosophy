"""
开发者管理后台 —— 访问统计 + 用户管理
"""
import os, json, time, sqlite3
from datetime import datetime

STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "admin_stats.json")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "wqx090915")

def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
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
