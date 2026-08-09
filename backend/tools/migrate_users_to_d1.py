# -*- coding: utf-8 -*-
"""旧 users.db → D1 导入 SQL 生成器（workers/api/migrations/002_import.sql）

数据源: 优先 GitHub Release userdb-v1（生产真身，Render 免费实例无持久盘，公开下载 URL 无需 token），
        失败用本地 backend/data/users.db；两者 users 行数取多者。

密码格式转换（D1 users.password_hash，auth worker checkPw 将支持）：
  - 旧 SHA-256 格式（64hex）:  → "sha256:{salt}:{hash}"（WebCrypto 可免费验证，原密码继续可用）
  - 旧 scrypt 格式           :  → 原样 "scrypt:{salt}:{hash}"（路径 B: Worker 401 提示重置；
                                      将来 Workers Paid 启用 verifyScrypt 后自动可登录）
  - --reset-admin <新密码>   :  管理员(txdsyl_) 覆盖为 Worker 原生格式 "{salt}:{sha256hex}"

用法: python backend/tools/migrate_users_to_d1.py [--reset-admin <密码>]
"""
import base64, hashlib, json, os, sqlite3, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
OUT_SQL = os.path.join(REPO, 'workers', 'api', 'migrations', '002_import.sql')
LOCAL_DB = os.path.join(HERE, 'data', 'users.db')
RELEASE_URL = 'https://github.com/wqx-txdsyl/DeepPhilosophy/releases/download/userdb-v1/users.db'


def fetch_remote_db():
    """下载生产 users.db（公开 Release 资产），返回临时路径或 None"""
    try:
        tmp = os.path.join(HERE, 'data', '_userdb_prod.db')
        req = urllib.request.Request(RELEASE_URL, headers={'User-Agent': 'migrate-users-to-d1'})
        with urllib.request.urlopen(req, timeout=15) as r:
            with open(tmp, 'wb') as f:
                f.write(r.read())
        return tmp
    except Exception as e:
        print('⚠ 远程下载失败（%s），用本地库' % e)
        return None


def q(v):
    """SQL 字符串转义"""
    if v is None:
        return 'NULL'
    return "'" + str(v).replace("'", "''") + "'"


def main():
    reset_admin = None
    if '--reset-admin' in sys.argv:
        reset_admin = sys.argv[sys.argv.index('--reset-admin') + 1]

    remote = fetch_remote_db()
    db_path = remote if remote and os.path.exists(remote) else LOCAL_DB
    db = sqlite3.connect(db_path)

    def rows(t):
        try:
            return db.execute('SELECT * FROM %s' % t).fetchall()
        except Exception:
            return []

    users = rows('users')
    if remote and os.path.exists(remote):
        local = sqlite3.connect(LOCAL_DB)
        n_local = local.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        n_remote = len(users)
        print('数据源: 远程 %d 用户 vs 本地 %d 用户 → 取 %s' % (n_remote, n_local, '远程' if n_remote >= n_local else '本地'))
        if n_local > n_remote:
            db_path = LOCAL_DB
            db = sqlite3.connect(db_path)
            users = rows('users')
        local.close()
    else:
        print('数据源: 本地 users.db（%d 用户）' % len(users))

    print('导出: users=%d reading_history=%d chat_history=%d book_notes=%d book_chat=%d'
          % (len(users), len(rows('reading_history')), len(rows('chat_history')),
             len(rows('book_notes')), len(rows('book_chat'))))

    lines = ['-- 002_import.sql 生成于 %s (migrate_users_to_d1.py)' % __import__('datetime').datetime.now().isoformat(timespec='seconds'),
             '-- 幂等: 全部 INSERT OR IGNORE（users 主键 / reading_history+book_notes UNIQUE(user_id,book_id)）']
    n_sha, n_scrypt, n_admin = 0, 0, 0

    for u in users:
        uid, username, ph, salt, created_at, avatar, profile = u[0], u[1], u[2], u[3], u[4], u[5], u[6]
        if ph and len(ph) == 64 and all(c in '0123456789abcdef' for c in ph.lower()):
            new_ph = 'sha256:%s:%s' % (salt, ph)   # 旧 SHA-256 → 可验证格式
            n_sha += 1
        else:
            new_ph = ph  # scrypt:... 原样
            n_scrypt += 1
        if reset_admin and username == 'txdsyl_':
            rnd = base64.b64encode(os.urandom(16)).decode()
            new_ph = rnd + ':' + hashlib.sha256((reset_admin + rnd).encode()).hexdigest()
            n_admin += 1
        lines.append('INSERT OR IGNORE INTO users (id, username, password_hash, avatar, created_at, profile) VALUES (%d, %s, %s, %s, %s, %s);'
                     % (uid, q(username), q(new_ph), q(avatar or ''), q(created_at), q(profile or '{}')))

    # 数据表（id 显式插入保证 FK 关系，INSERT OR IGNORE 幂等）
    for t in ('reading_history', 'chat_history', 'book_notes', 'book_chat'):
        for r in rows(t):
            cols = ['id', 'user_id'] + [d[1] for d in db.execute('PRAGMA table_info(%s)' % t)][2:]
            vals = ', '.join(q(v) for v in r)
            lines.append('INSERT OR IGNORE INTO %s (%s) VALUES (%s);' % (t, ', '.join(cols), vals))

    os.makedirs(os.path.dirname(OUT_SQL), exist_ok=True)
    with open(OUT_SQL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('写入 %s（%d 条 INSERT；sha256 迁移 %d / scrypt 保留 %d / 管理员重置 %d）'
          % (OUT_SQL, len(lines) - 2, n_sha, n_scrypt, n_admin))


if __name__ == '__main__':
    main()
