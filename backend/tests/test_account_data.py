"""Temporary DB tests only; never read real accounts or call an LLM."""
import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth
import account_data as data
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes.agent_history import router
from auth_deps import auth_required


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / 'accounts.db'
    monkeypatch.setattr(auth, 'DB_PATH', str(path))
    monkeypatch.setattr(auth, '_sync_db_from_cloud', lambda: pytest.fail('live DB must not be replaced'))
    with sqlite3.connect(path) as conn:
        conn.executescript("CREATE TABLE users (id INTEGER PRIMARY KEY,username TEXT,profile TEXT); INSERT INTO users VALUES(1,'fixture-a','{}'); INSERT INTO users VALUES(2,'fixture-b','{}');")
    return path


def conversation(mid='one', content='问题'):
    return {'conversation_id': 'fixture', 'messages': [{'message_id': mid, 'role': 'user', 'content': content}]}


def test_relogin_new_connection_restart_and_account_isolation(database):
    assert data.save_conversation(1, 'fixture', conversation(), 0)[0]
    assert data.list_conversations(2) == []
    assert data.list_conversations(1)[0]['data'] == conversation()
    # Reinitialize/reopen the DB as a restarted process; no startup restore.
    auth.init_db()
    assert data.list_conversations(1)[0]['data'] == conversation()
    assert data.save_conversation(2, 'fixture', conversation(content='另一个账号'), 0)[0]
    assert data.list_conversations(1)[0]['data'] == conversation()


def test_stale_device_conflict_and_deleted_conversation_cannot_return(database):
    assert data.save_conversation(1, 'fixture', conversation(), 0)[0]
    good, latest = data.save_conversation(1, 'fixture', conversation('two'), 1)
    assert good and latest['revision'] == 2
    good, latest = data.save_conversation(1, 'fixture', conversation('stale'), 1)
    assert not good and latest['data'] == conversation('two')
    tombstone = data.delete_conversation(1, 'fixture')
    assert tombstone['deleted']
    assert not data.save_conversation(1, 'fixture', conversation('revive'), tombstone['revision'])[0]
    assert data.list_conversations(1)[0]['data'] is None


def test_memory_survives_new_conversation_with_provenance_and_can_be_forgotten(database):
    memory = data.remember(1, '请记住，我正在比较康德和休谟')
    assert data.list_memories(2) == []
    assert data.remember(1, memory['text']) == memory
    data.save_conversation(1, 'fixture', conversation(content='因果律是什么？'), 0)
    context = data.account_context(1, 'new-conversation')
    assert context['explicit_memories'] == [memory]
    assert context['recent_questions'][0]['conversation_id'] == 'fixture'
    assert data.account_context(1, 'fixture')['recent_questions'] == []
    assert not data.forget(2, memory['memory_id'])
    assert data.forget(1, memory['memory_id'])
    data.delete_account_data(1)
    assert data.list_conversations(1) == []


def test_routes_reject_unauthenticated_and_client_selected_owner(database):
    app = FastAPI(); app.include_router(router)
    client = TestClient(app)
    assert client.get('/api/agent/conversations').status_code == 401
    app.dependency_overrides[auth_required] = lambda: {'id': 1}
    payload = {'data': conversation(), 'expected_revision': 0}
    assert client.put('/api/agent/conversations/fixture', json={**payload, 'user_id': 2}).status_code == 422
    assert client.put('/api/agent/conversations/fixture', json=payload).status_code == 200
    assert client.put('/api/agent/conversations/fixture', json=payload).status_code == 409
    assert data.list_conversations(2) == []
    app.dependency_overrides[auth_required] = lambda: {'id': 2}
    assert client.get('/api/agent/conversations').json() == {'records': []}


def test_memory_tool_requires_user_request_and_exact_quote(database):
    from account_memory_tools import remember_account_memory, recall_account_memory
    from deep_context import current_account_id, current_request_question
    uid = current_account_id.set(1)
    question = current_request_question.set('请记住：我在读《纯粹理性批判》')
    try:
        assert remember_account_memory('他是康德主义者')['error'] == 'EXPLICIT_MEMORY_REQUEST_REQUIRED'
        assert 'memory' in remember_account_memory('我在读《纯粹理性批判》')
        assert recall_account_memory()['memories'][0]['text'] == '我在读《纯粹理性批判》'
    finally:
        current_account_id.reset(uid); current_request_question.reset(question)


def test_new_general_conversation_reads_account_memory_without_changing_system_prompt(database, monkeypatch):
    import asyncio
    import deep_bare_agent as bare
    from deep_context import current_account_id
    from langchain_core.messages import AIMessageChunk
    data.remember(1, '我在研究康德与休谟')
    seen = []
    class Model:
        def bind_tools(self, tools): return self
        async def astream(self, messages):
            seen.extend(messages)
            yield AIMessageChunk(content='fixture answer', response_metadata={'finish_reason':'stop'})
    async def tools(): return []
    async def no_questions(*args): return {'suggestions': [], 'status': 'unavailable'}
    monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'load_tools',tools)
    monkeypatch.setattr(bare,'source_metadata',lambda *args:([],None))
    monkeypatch.setattr(bare,'exploration_questions',no_questions)
    async def run():
        token = current_account_id.set(1)
        try: return [event async for event in bare.stream_bare_agent('新问题', [], conversation_id='new')]
        finally: current_account_id.reset(token)
    assert next(e for e in asyncio.run(run()) if e['type']=='done')['content'] == 'fixture answer'
    assert len([m for m in seen if m.type=='system']) == 1
    assert '我在研究康德与休谟' in seen[1].content
    assert seen[-1].content == '新问题'


def test_older_history_search_and_read_stay_in_account(database):
    data.save_conversation(1, 'fixture', conversation(content='过去讨论康德因果论'), 0)
    data.save_conversation(2, 'fixture', conversation(content='康德，另一个账号'), 0)
    found = data.search_history(1, '康德')
    assert len(found) == 1 and found[0]['excerpt'] == '过去讨论康德因果论'
    assert data.search_history(1, '%') == []
    assert data.search_history(1, "' OR 1=1 --") == []
    assert data.get_conversation(1,'fixture')['messages'][0]['content'] == '过去讨论康德因果论'
    assert data.get_conversation(2,'missing') is None
    data.delete_conversation(1,'fixture')
    assert data.search_history(1,'康德') == []
    assert data.get_conversation(1,'fixture') is None


def test_legacy_account_history_restores_once_without_cross_account_or_resurrection(database):
    with auth._get_conn() as conn:
        conn.execute('CREATE TABLE chat_history(id INTEGER PRIMARY KEY,user_id INTEGER,role TEXT,content TEXT,sources TEXT,created_at TEXT)')
        conn.executemany('INSERT INTO chat_history VALUES(?,?,?,?,?,?)',[
            (1,1,'user','旧问题',None,'2026-09-01T10:00:00Z'),
            (2,1,'assistant','旧回答','[]','2026-09-01T10:01:00Z'),
            (3,2,'user','其他账号',None,'2026-09-01T10:00:00Z')])
    records=data.list_conversations(1)
    assert len(records)==1 and len(records[0]['data']['messages'])==2
    assert records[0]['data']['title']=='旧版历史对话'
    assert len(data.list_conversations(1)[0]['data']['messages'])==2
    assert data.search_history(1,'其他账号')==[]
    cid=records[0]['conversation_id']
    data.delete_conversation(1,cid)
    with auth._get_conn() as conn: conn.execute('INSERT INTO chat_history VALUES(4,1,\'user\',\'新旧版问题\',NULL,\'2026-09-02\')')
    assert data.list_conversations(1)[0]['deleted']
    with auth._get_conn() as conn: assert conn.execute('SELECT count(*) FROM chat_history').fetchone()[0]==4


def test_lightweight_directory_lazy_detail_and_compression(database):
    app=FastAPI(); app.include_router(router)
    app.dependency_overrides[auth_required]=lambda:{'id':1}
    client=TestClient(app)
    payload=conversation(content='正文'*30000)
    payload['messages'][0]['tool_events']=[{'result':'工具轨迹'*20000}]
    data.save_conversation(1,'fixture',payload,0)
    index=client.get('/api/agent/conversations?index=true').json()['records'][0]['data']
    assert index['messages']==[] and index['messages_loaded'] is False and index['message_count']==1
    full=client.get('/api/agent/conversations/fixture',headers={'Accept-Encoding':'gzip'})
    assert full.json()['record']['data']==payload
    assert full.headers['content-encoding']=='gzip' and int(full.headers['content-length'])<3000
    assert full.headers['cache-control']=='private, no-store'
    app.dependency_overrides[auth_required]=lambda:{'id':2}
    assert client.get('/api/agent/conversations/fixture').status_code==404


def test_disconnect_cleanup_does_not_reset_another_task_context():
    import contextvars
    from deep_context import reset_owned_context
    variable=contextvars.ContextVar('fixture',default=None)
    original=contextvars.Context(); foreign=contextvars.Context()
    token=original.run(variable.set,'original')
    foreign.run(variable.set,'other request')
    assert foreign.run(reset_owned_context,variable,token) is False
    assert foreign.run(variable.get)=='other request'
    assert original.run(reset_owned_context,variable,token) is True
    assert original.run(variable.get) is None
