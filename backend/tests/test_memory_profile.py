"""Narrative memory integration against disposable accounts; no model network."""
import asyncio
import json
import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth
import account_data as data
import account_memory_profile as memory
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes.agent_history import router
from auth_deps import auth_required


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path/'memory.db'
    monkeypatch.setattr(auth, 'DB_PATH', str(path))
    monkeypatch.setattr(auth, '_sync_db_from_cloud', lambda: pytest.fail('No live data'))
    with sqlite3.connect(path) as conn:
        conn.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,profile TEXT); INSERT INTO users VALUES(1,'a','{}'); INSERT INTO users VALUES(2,'b','{}');")
    memory._locks.clear()
    return path


def history(uid=1, text='我正在阅读康德', cid='one', revision=0):
    payload={'conversation_id':cid,'messages':[{'role':'user','message_id':'u','content':text},
        {'role':'assistant','message_id':'a','content':'assistant cannot establish beliefs','streaming':False}]}
    data.save_conversation(uid,cid,payload,revision)


def test_generate_persist_and_do_not_assume_beliefs(database, monkeypatch):
    history()
    history(2,'另一个账户私人内容')
    async def summarize(sources):
        assert len(sources)==1 and sources[0]['text']=='我正在阅读康德'
        return memory.validated_summary({'sections':[{'topic':'reading','text':'正在阅读康德。',
            'evidence':[{'source_id':sources[0]['id'],'quote':'我正在阅读康德'}]}]}, sources)
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1))
    saved=memory.get_profile(1)
    assert saved['text']=='## 阅读与研究\n正在阅读康德。'
    assert saved['revision']==1 and saved['sources'][0]['conversation_id']=='one'
    assert memory.get_profile(2)['text']==''
    assert data.account_context(1)['memory_profile']==saved['text']
    asyncio.run(memory.refresh(1))
    assert memory.get_profile(1)['revision']==1  # unchanged history is not billed again


def test_manual_correction_survives_update_and_blank_clear(database, monkeypatch):
    history()
    async def summarize(sources): return '## 阅读与研究\n自动摘要', []
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1))
    saved=memory.get_profile(1)
    ok, saved=memory.save_profile(1,'我是在比较观点，不认同康德。',True,saved['revision'])
    assert ok and saved['manual']
    history(text='请比较经验主义',cid='two')
    asyncio.run(memory.refresh(1))
    assert memory.get_profile(1)['text']=='我是在比较观点，不认同康德。'
    assert memory.get_profile(1)['proposal']=='## 阅读与研究\n自动摘要'
    assert not memory.save_profile(1,'旧设备',True,saved['revision'])[0]
    p=memory.get_profile(1)
    assert memory.save_profile(1,'',True,p['revision'])[0]
    asyncio.run(memory.refresh(1))
    assert memory.get_profile(1)['text']==memory.get_profile(1)['proposal']==''
    asyncio.run(memory.refresh(1,force=True))
    assert memory.get_profile(1)['text']=='' and memory.get_profile(1)['proposal']


def test_disabled_stops_generation_recall_and_preserves_data(database, monkeypatch):
    history(); data.remember(1,'用户原话')
    ok,p=memory.save_profile(1,'我在阅读康德',False,0)
    assert ok
    async def summarize(*args): pytest.fail('Disabled memory must not invoke a model')
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1,True))
    context=data.account_context(1)
    assert not context['memory_profile'] and not context['explicit_memories'] and not context['recent_questions']
    assert memory.get_profile(1)['text']=='我在阅读康德'
    from deep_context import current_account_id, current_request_question
    from account_memory_tools import recall_account_memory, remember_account_memory
    uid=current_account_id.set(1);question=current_request_question.set('请记住新信息')
    try:
        assert recall_account_memory()['error']=='MEMORY_DISABLED'
        assert remember_account_memory('新信息')['error']=='MEMORY_DISABLED'
    finally:
        current_account_id.reset(uid);current_request_question.reset(question)


def test_invalid_quotes_rejected_and_failure_keeps_old_memory(database, monkeypatch):
    history();sources,_=memory.history_sources(1)
    for evidence in [{'source_id':'wrong','quote':'康德'}, {'source_id':sources[0]['id'],'quote':'我是康德主义者'}]:
        with pytest.raises(ValueError):
            memory.validated_summary({'sections':[{'topic':'background','text':'胡说','evidence':[evidence]}]},sources)
    assert memory.save_profile(1,'用户更正',True,0)[0]
    async def failed(*args): raise RuntimeError('402 private provider details')
    monkeypatch.setattr(memory,'summarize',failed)
    asyncio.run(memory.refresh(1))
    saved=memory.get_profile(1)
    assert saved['status']=='error' and saved['text']=='用户更正' and '402' not in json.dumps(saved)


def test_delete_while_generating_cannot_resurrect(database, monkeypatch):
    history()
    async def summarize(*args):
        data.delete_account_data(1)
        with auth._get_conn() as conn: conn.execute('DELETE FROM users WHERE id=1')
        return 'account should not return',[]
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1))
    with data.connection() as conn: assert not conn.execute('SELECT 1 FROM agent_memory_profile WHERE user_id=1').fetchone()


def test_history_delete_and_quote_forget_invalidate_generated_summary(database, monkeypatch):
    history();m=data.remember(1,'我在读康德')
    async def summarize(*args): return '## 阅读与研究\n正在读康德',[]
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1))
    assert data.forget(1,m['memory_id'])
    assert memory.get_profile(1)['text']==''
    asyncio.run(memory.refresh(1))
    data.delete_conversation(1,'one')
    assert memory.get_profile(1)['text']==''
    assert memory.history_sources(1)[0]==[]


def test_edit_during_generation_remains_manual_and_concurrent_calls_coalesce(database, monkeypatch):
    history()
    async def summarize(*args):
        p=memory.get_profile(1)
        assert memory.save_profile(1,'正在编辑的更正',True,p['revision'])[0]
        await memory.refresh(1)  # no recursive wait or duplicate model request
        return '新生成内容',[]
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1))
    p=memory.get_profile(1)
    assert p['text']=='正在编辑的更正' and p['proposal']=='新生成内容'


def test_api_private_revision_conflicts_and_identity(database, monkeypatch):
    history()
    async def summarize(*args): return '## 阅读与研究\n测试摘要',[]
    monkeypatch.setattr(memory,'summarize',summarize)
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[auth_required]=lambda:{'id':1}
    client=TestClient(app)
    result=client.get('/api/agent/memory/profile')
    assert result.headers['cache-control']=='private, no-store'
    p=client.get('/api/agent/memory/profile').json()['profile']
    update=client.put('/api/agent/memory/profile',json={'text':'我自己修改', 'enabled':True,'expected_revision':p['revision']})
    assert update.status_code==200
    assert client.put('/api/agent/memory/profile',json={'text':'过时草稿','enabled':True,'expected_revision':p['revision']}).status_code==409
    app.dependency_overrides[auth_required]=lambda:{'id':2}
    assert client.get('/api/agent/memory/profile').json()['profile']['text']==''


def test_new_history_arriving_during_update_is_eventually_included(database, monkeypatch):
    history();calls=[]
    async def summarize(sources):
        calls.append(sources)
        if len(calls)==1:
            history(text='我开始阅读亚里士多德',cid='two')
            await memory.refresh(1)
        return f'摘要包含{len(sources)}条历史',[]
    monkeypatch.setattr(memory,'summarize',summarize)
    asyncio.run(memory.refresh(1))
    assert len(calls)==2
    assert memory.get_profile(1)['text']=='摘要包含2条历史'
    assert memory.get_profile(1)['source_hash']==memory.history_sources(1)[1]


def test_conversation_sync_only_schedules_memory_after_completed_answer(database, monkeypatch):
    calls=[]
    async def refresh(uid,*args): calls.append(uid)
    monkeypatch.setattr(memory,'refresh',refresh)
    app=FastAPI();app.include_router(router);app.dependency_overrides[auth_required]=lambda:{'id':1}
    client=TestClient(app)
    payload={'conversation_id':'test','messages':[{'role':'user','message_id':'u','content':'问题'},
        {'role':'assistant','message_id':'a','content':'正在回答','streaming':True}]}
    assert client.put('/api/agent/conversations/test',json={'data':payload,'expected_revision':0}).status_code==200
    assert not calls
    payload['messages'][-1].update(streaming=False,stream_state='complete')
    assert client.put('/api/agent/conversations/test',json={'data':payload,'expected_revision':1}).status_code==200
    assert calls==[1]
