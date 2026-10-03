"""Durable account data in the same database/identity authority as agent auth.

Per-conversation revisions and tombstones prevent stale devices from replacing
account history or resurrecting deleted conversations. No whole-list overwrite.
"""
import json
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    import auth
    conn = auth._get_conn()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS agent_conversation_records (
            user_id INTEGER NOT NULL, conversation_id TEXT NOT NULL,
            data TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
            deleted INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, conversation_id))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS agent_account_memory (
            user_id INTEGER NOT NULL, memory_id TEXT NOT NULL, text TEXT NOT NULL,
            created_at TEXT NOT NULL, PRIMARY KEY (user_id, memory_id))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS agent_memory_profile (
            user_id INTEGER PRIMARY KEY, text TEXT NOT NULL DEFAULT '',
            proposal TEXT NOT NULL DEFAULT '', manual INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1, revision INTEGER NOT NULL DEFAULT 0,
            source_hash TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'idle',
            updated_at TEXT NOT NULL DEFAULT '', sources TEXT NOT NULL DEFAULT '[]')""")
        conn.execute("""CREATE TABLE IF NOT EXISTS agent_memory_profile_details (
            user_id INTEGER PRIMARY KEY, metadata TEXT NOT NULL DEFAULT '{}',
            proposal_metadata TEXT NOT NULL DEFAULT '{}', corrections TEXT NOT NULL DEFAULT '[]')""")
        conn.execute("CREATE INDEX IF NOT EXISTS agent_conversation_recent ON agent_conversation_records(user_id,updated_at DESC)")
        conn.execute("""CREATE TABLE IF NOT EXISTS agent_history_migrations (
            user_id INTEGER PRIMARY KEY, last_chat_id INTEGER NOT NULL DEFAULT 0)""")
        conn.commit()
        yield conn
    finally:
        conn.close()


def record(row):
    return {"conversation_id": row["conversation_id"], "revision": row["revision"],
            "deleted": bool(row["deleted"]), "updated_at": row["updated_at"],
            "data": None if row["deleted"] else json.loads(row["data"])}


def migrate_legacy_history(user_id):
    """Expose this account's old flat chat history without inventing threads.

    Source rows remain untouched. Stable message IDs make retries idempotent;
    a deleted archive stays deleted, even when a stale client reconnects.
    """
    with connection() as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='chat_history'").fetchone():
            return
        conn.execute('BEGIN IMMEDIATE')
        checkpoint = conn.execute('SELECT last_chat_id FROM agent_history_migrations WHERE user_id=?', (user_id,)).fetchone()
        last_id = checkpoint[0] if checkpoint else 0
        rows = conn.execute('SELECT id,role,content,sources,created_at FROM chat_history WHERE user_id=? AND id>? ORDER BY id',
                            (user_id,last_id)).fetchall()
        if not rows:
            return
        cid = 'conv_legacy_account_chat'
        existing = conn.execute('SELECT * FROM agent_conversation_records WHERE user_id=? AND conversation_id=?', (user_id,cid)).fetchone()
        if not existing or not existing['deleted']:
            archive = json.loads(existing['data']) if existing else {
                'conversation_id':cid, 'title':'旧版历史对话', 'default_agent_id':'general',
                'created_at':rows[0]['created_at'], 'messages':[]}
            seen = {m['message_id'] for m in archive['messages']}
            for row in rows:
                mid = f"legacy_chat_{row['id']}"
                if mid in seen or row['role'] not in {'user','assistant'}:
                    continue
                msg = {'message_id':mid,'role':row['role'],'content':row['content'],
                       'created_at':row['created_at'],'conversation_id':cid}
                if row['role'] == 'assistant':
                    msg.update({'agent_id':'general','stream_state':'complete'})
                    try:
                        sources = json.loads(row['sources'] or '[]')
                        if isinstance(sources,list): msg['citations'] = [c for c in sources if isinstance(c,dict)]
                    except (ValueError,TypeError): pass
                archive['messages'].append(msg)
            archive['updated_at'] = rows[-1]['created_at']
            conn.execute("""INSERT INTO agent_conversation_records VALUES (?,?,?,?,0,?)
                ON CONFLICT(user_id,conversation_id) DO UPDATE SET data=excluded.data,
                revision=excluded.revision,updated_at=excluded.updated_at""",
                (user_id,cid,json.dumps(archive,ensure_ascii=False),(existing['revision'] if existing else 0)+1,archive['updated_at']))
        conn.execute('INSERT INTO agent_history_migrations VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET last_chat_id=excluded.last_chat_id',
                     (user_id,rows[-1]['id']))
        conn.commit()


def list_conversations(user_id, index_only=False):
    migrate_legacy_history(user_id)
    with connection() as conn:
        items = [record(row) for row in conn.execute(
            "SELECT * FROM agent_conversation_records WHERE user_id=? ORDER BY updated_at DESC",
            (user_id,)).fetchall()]
    if index_only:
        for item in items:
            if item['deleted']: continue
            data = item['data']
            item['data'] = {k:data[k] for k in ('conversation_id','title','default_agent_id','last_used_agent_id',
                          'created_at','updated_at','reading_context') if k in data}
            item['data'].update({'messages':[], 'messages_loaded':False, 'message_count':len(data.get('messages',[]))})
    return items


def save_conversation(user_id, conversation_id, data, expected_revision):
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM agent_conversation_records WHERE user_id=? AND conversation_id=?",
                           (user_id, conversation_id)).fetchone()
        if row and (row["deleted"] or row["revision"] != expected_revision):
            return False, record(row)
        if row is None and expected_revision != 0:
            return False, None
        revision = expected_revision + 1
        stamp = now()
        conn.execute("""INSERT INTO agent_conversation_records VALUES (?,?,?,?,0,?)
            ON CONFLICT(user_id, conversation_id) DO UPDATE SET
            data=excluded.data, revision=excluded.revision, updated_at=excluded.updated_at""",
            (user_id, conversation_id, json.dumps(data, ensure_ascii=False), revision, stamp))
        conn.commit()
        return True, {"conversation_id": conversation_id, "revision": revision,
                      "deleted": False, "updated_at": stamp, "data": data}


def delete_conversation(user_id, conversation_id):
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""INSERT INTO agent_conversation_records VALUES (?,?,'{}',1,1,?)
            ON CONFLICT(user_id,conversation_id) DO UPDATE SET data='{}', deleted=1,
            revision=agent_conversation_records.revision+1, updated_at=excluded.updated_at""",
            (user_id, conversation_id, now()))
        from account_memory_profile import invalidate_generated
        invalidate_generated(conn, user_id)
        conn.commit()
        return record(conn.execute(
            "SELECT * FROM agent_conversation_records WHERE user_id=? AND conversation_id=?",
            (user_id, conversation_id)).fetchone())


def list_memories(user_id):
    with connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT memory_id,text,created_at FROM agent_account_memory WHERE user_id=? ORDER BY created_at",
            (user_id,)).fetchall()]


def get_conversation(user_id, conversation_id):
    with connection() as conn:
        row = conn.execute("SELECT * FROM agent_conversation_records WHERE user_id=? AND conversation_id=? AND deleted=0",
                           (user_id, conversation_id)).fetchone()
        return record(row)["data"] if row else None


def search_history(user_id, query):
    migrate_legacy_history(user_id)
    pattern = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    with connection() as conn:
        rows = conn.execute("""SELECT c.conversation_id, json_extract(c.data,'$.title') AS title,
            json_extract(m.value,'$.role') AS role, json_extract(m.value,'$.content') AS content,
            json_extract(m.value,'$.message_id') AS message_id
            FROM agent_conversation_records c, json_each(c.data,'$.messages') m
            WHERE c.user_id=? AND c.deleted=0 AND json_extract(m.value,'$.content') LIKE ? ESCAPE '\\'
            ORDER BY c.updated_at DESC, m.key DESC LIMIT 12""", (user_id, pattern)).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        content = item.pop('content') or ''
        start = max(0, content.lower().find(query.lower()) - 180)
        item.update({"excerpt": content[start:start + 1200], "excerpt_offset": start})
        output.append(item)
    return output


def remember(user_id, text):
    with connection() as conn:
        existing = conn.execute("SELECT memory_id,text,created_at FROM agent_account_memory WHERE user_id=? AND text=?",
                                (user_id, text)).fetchone()
        if existing:
            return dict(existing)
        item = {"memory_id": uuid.uuid4().hex, "text": text, "created_at": now()}
        conn.execute("INSERT INTO agent_account_memory VALUES (?,?,?,?)",
                     (user_id, item["memory_id"], text, item["created_at"]))
        conn.commit()
        return item


def forget(user_id, memory_id):
    with connection() as conn:
        cur = conn.execute("DELETE FROM agent_account_memory WHERE user_id=? AND memory_id=?",
                           (user_id, memory_id))
        if cur.rowcount:
            from account_memory_profile import invalidate_generated
            invalidate_generated(conn, user_id)
        conn.commit()
        return cur.rowcount > 0


def delete_account_data(user_id):
    with connection() as conn:
        for table in ("agent_account_memory", "agent_memory_profile", "agent_memory_profile_details", "agent_conversation_records", "agent_history_migrations"):
            conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
        conn.commit()


def account_context(user_id, conversation_id=None):
    """Explicit memory and previous questions, never inferred beliefs."""
    import auth
    profile = auth.get_profile(user_id)
    questions = []
    with connection() as conn:
        recent = [record(row) for row in conn.execute(
            "SELECT * FROM agent_conversation_records WHERE user_id=? AND deleted=0 AND conversation_id!=? "
            "ORDER BY updated_at DESC LIMIT 8", (user_id, conversation_id or "")).fetchall()]
    for item in recent:
        if item["deleted"] or item["conversation_id"] == conversation_id:
            continue
        for message in reversed(item["data"].get("messages", [])):
            if message.get("role") == "user" and message.get("content"):
                questions.append({"conversation_id": item["conversation_id"],
                                  "question": message["content"][:1500]})
                break
        if len(questions) == 4:
            break
    from account_memory_profile import get_profile
    memory = get_profile(user_id)
    return {"explicit_memories": list_memories(user_id) if memory['enabled'] else [],
            "memory_profile": memory['text'] if memory['enabled'] else '',
            "memory_profile_user_edited": memory['manual'] if memory['enabled'] else False,
            "profile": {key: profile[key] for key in ("about",) if profile.get(key)},
            "user_settings": {key:profile[key] for key in ('nickname','occupation','about','custom_instructions') if profile.get(key)},
            "recent_questions": questions if memory['enabled'] else []}
