"""Private Project records. Deliberately independent of Chat/history/memory."""
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SESSION = uuid.uuid4().hex


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    import auth
    conn = auth._get_conn()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS phi_projects (
            user_id INTEGER NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL,
            revision INTEGER NOT NULL, updated_at TEXT NOT NULL,
            PRIMARY KEY(user_id,id))''')
        conn.execute('''CREATE TABLE IF NOT EXISTS phi_project_runs (
            user_id INTEGER NOT NULL, project_id TEXT NOT NULL, id TEXT NOT NULL,
            data TEXT NOT NULL, PRIMARY KEY(user_id,project_id,id))''')
        conn.commit()
        yield conn
    finally:
        conn.close()


def unpack(row):
    return dict(id=row['id'], revision=row['revision'], updated_at=row['updated_at'], data=json.loads(row['data'])) if row else None


def get(uid, pid):
    with connection() as conn:
        return unpack(conn.execute('SELECT * FROM phi_projects WHERE user_id=? AND id=?', (uid, pid)).fetchone())


def listing(uid):
    with connection() as conn:
        return [dict(id=r['id'], revision=r['revision'], updated_at=r['updated_at'], title=json.loads(r['data'])['title'],
                     question=json.loads(r['data'])['question']) for r in conn.execute('SELECT * FROM phi_projects WHERE user_id=? ORDER BY updated_at DESC', (uid,))]


def save(uid, pid, data, revision, create=False):
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM phi_projects WHERE user_id=? AND id=?', (uid, pid)).fetchone()
        if (create and row) or (not create and (not row or row['revision'] != revision)):
            return False, unpack(row)
        stamp = now()
        if create:
            conn.execute('INSERT INTO phi_projects VALUES(?,?,?,?,?)', (uid, pid, json.dumps(data, ensure_ascii=False), 1, stamp))
        else:
            conn.execute('UPDATE phi_projects SET data=?,revision=revision+1,updated_at=? WHERE user_id=? AND id=?',
                         (json.dumps(data, ensure_ascii=False), stamp, uid, pid))
        conn.commit()
        return True, dict(id=pid, revision=(1 if create else revision+1), updated_at=stamp, data=data)


def delete(uid, pid):
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('DELETE FROM phi_project_runs WHERE user_id=? AND project_id=?', (uid,pid))
        conn.execute('DELETE FROM phi_projects WHERE user_id=? AND id=?', (uid,pid))
        conn.commit()


def delete_account(uid):
    with connection() as conn:
        conn.execute('DELETE FROM phi_project_runs WHERE user_id=?', (uid,))
        conn.execute('DELETE FROM phi_projects WHERE user_id=?', (uid,))
        conn.commit()


def runs(uid, pid):
    with connection() as conn:
        # Interrupted processes cannot leave an apparently running task forever.
        rows = [json.loads(r['data']) for r in conn.execute('SELECT data FROM phi_project_runs WHERE user_id=? AND project_id=?', (uid,pid))]
        for r in rows:
            if r['status'] in ('queued','running') and r.get('session') != SESSION:
                r.update(status='interrupted', error='服务重启，任务已中断；可重新发起。')
                conn.execute('UPDATE phi_project_runs SET data=? WHERE user_id=? AND project_id=? AND id=?', (json.dumps(r,ensure_ascii=False),uid,pid,r['id']))
        conn.commit()
        return sorted(rows, key=lambda r:r['created_at'], reverse=True)


def update_run(uid, pid, rid, transform):
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT data FROM phi_project_runs WHERE user_id=? AND project_id=? AND id=?', (uid,pid,rid)).fetchone()
        if not row: return None
        run = transform(json.loads(row['data']))
        conn.execute('UPDATE phi_project_runs SET data=? WHERE user_id=? AND project_id=? AND id=?', (json.dumps(run,ensure_ascii=False),uid,pid,rid))
        conn.commit()
        return run


def new_run(uid, pid, rid, expected_revision, object_id, instruction):
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        project = unpack(conn.execute('SELECT * FROM phi_projects WHERE user_id=? AND id=?', (uid,pid)).fetchone())
        if not project: return 'missing', None
        if project['revision'] != expected_revision: return 'conflict', project
        if not any(o['id'] == object_id for o in project['data']['objects']): return 'object', None
        all_runs = [json.loads(r[0]) for r in conn.execute('SELECT data FROM phi_project_runs WHERE user_id=? AND project_id=?', (uid,pid))]
        if any(r['status'] in ('queued','running') and r.get('session') == SESSION for r in all_runs): return 'busy', None
        run = dict(id=rid, object_id=object_id, instruction=instruction, base_revision=expected_revision,
                   status='queued', created_at=now(), session=SESSION, result='', error='')
        # Snapshot is temporary in-process input, not an undeletable duplicate of private sources.
        conn.execute('INSERT INTO phi_project_runs VALUES(?,?,?,?)', (uid,pid,rid,json.dumps(run,ensure_ascii=False)))
        conn.commit()
        return 'ok', (run,project)


def adopt(uid, pid, rid, revision):
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM phi_projects WHERE user_id=? AND id=?', (uid,pid)).fetchone()
        rr = conn.execute('SELECT data FROM phi_project_runs WHERE user_id=? AND project_id=? AND id=?', (uid,pid,rid)).fetchone()
        if not row or not rr: return 'missing', None
        p, r = unpack(row), json.loads(rr[0])
        if r['status'] == 'adopted': return 'ok', p  # Retry is idempotent.
        if r['status'] != 'completed': return 'invalid', None
        if p['revision'] != revision or r['base_revision'] != revision: return 'conflict', p
        target = next((o for o in p['data']['objects'] if o['id'] == r['object_id']), None)
        if not target: return 'missing', None
        target['versions'] = (target.get('versions', []) + [dict(content=target['content'], at=now())])[-10:]
        target['content'] = r['result']
        p['revision'] += 1
        p['updated_at'] = now()
        r['status'] = 'adopted'
        conn.execute('UPDATE phi_projects SET data=?,revision=?,updated_at=? WHERE user_id=? AND id=?', (json.dumps(p['data'],ensure_ascii=False),p['revision'],p['updated_at'],uid,pid))
        conn.execute('UPDATE phi_project_runs SET data=? WHERE user_id=? AND project_id=? AND id=?', (json.dumps(r,ensure_ascii=False),uid,pid,rid))
        conn.commit()
        return 'ok', p
