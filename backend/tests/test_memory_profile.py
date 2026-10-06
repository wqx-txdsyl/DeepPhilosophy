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


def test_dynamic_topics_nested_prose_and_contextual_questions(database):
    sources=[{'id':'one','text':'我在构建哲学阅读系统；我正在研究因果性'}]
    payload={'sections':[{'title':'概览','text':'你正在构建哲学阅读系统。','evidence':[{'source_id':'one','quote':'我在构建哲学阅读系统'}]},
        {'title':'哲学阅读系统','level':2,'text':'你的长期项目关注可验证的阅读。','evidence':[{'source_id':'one','quote':'构建哲学阅读系统'}]},
        {'title':'因果性研究','level':3,'text':'你正在研究因果性。','evidence':[{'source_id':'one','quote':'我正在研究因果性'}]}],
        'exploration':[{'section':'因果性研究','question':'因果性的讨论如何影响你的阅读系统？'}]}
    text,evidence=memory.validated_summary(payload,sources)
    assert '### 因果性研究' in text
    assert evidence.metadata['outline']==['概览','哲学阅读系统','因果性研究']
    assert evidence.metadata['exploration'][0]['section']=='因果性研究'
    payload['exploration'][0]['section']='不存在的主题'
    with pytest.raises(ValueError):memory.validated_summary(payload,sources)
    with pytest.raises(ValueError):memory.validated_summary({'sections':[{'title':'旧稿','text':'凭旧稿推断',
        'evidence':[{'source_id':'old','quote':'旧稿'}]}]},[{'id':'old','text':'旧稿','origin':'previous_summary'}])


def test_natural_correction_is_saved_and_survives_future_updates(database, monkeypatch):
    history()
    p=memory.save_profile(1,'## 阅读\n用户已经赞同康德',True,0)[1]
    async def summarize(sources):
        assert sources[-1]['origin']=='correction_request'
        return memory.validated_summary({'sections':[{'title':'阅读立场','text':'你正在比较观点，而非赞同康德。',
            'evidence':[{'source_id':'current-correction','quote':'我只是比较，并不赞同康德'}]}],
            'exploration':[{'section':'阅读立场','question':'康德与休谟的哪一个论证需要继续比较？'}]},sources)
    monkeypatch.setattr(memory,'summarize',summarize)
    ok,p=asyncio.run(memory.correct_profile(1,'我只是比较，并不赞同康德',p['revision']))
    assert ok and p['manual'] and p['corrections'][0]['request']=='我只是比较，并不赞同康德'
    assert p['metadata']['exploration'] and data.account_context(1)['memory_profile']==p['text']
    assert not asyncio.run(memory.correct_profile(1,'旧设备',0))[0]
    async def later(sources):
        assert any(s.get('origin')=='user_correction' and s['text']=='我只是比较，并不赞同康德' for s in sources)
        return '## 新探索\n你的更正仍被保留', memory.MemoryEvidence([],{'exploration':[]})
    monkeypatch.setattr(memory,'summarize',later)
    asyncio.run(memory.refresh(1,True))
    latest=memory.get_profile(1)
    assert latest['text']==p['text'] and latest['proposal'] and latest['corrections']==p['corrections']
    data.delete_account_data(1)
    with data.connection() as conn:assert not conn.execute('SELECT 1 FROM agent_memory_profile_details WHERE user_id=1').fetchone()


def test_failed_or_racing_corrections_never_overwrite(database, monkeypatch):
    p=memory.save_profile(1,'原文',True,0)[1]
    async def failed(sources):raise RuntimeError('provider fails')
    monkeypatch.setattr(memory,'summarize',failed)
    with pytest.raises(RuntimeError):asyncio.run(memory.correct_profile(1,'更正草稿',p['revision']))
    assert memory.get_profile(1)['text']=='原文'
    async def raced(sources):
        memory.save_profile(1,'另一台设备已更正',True,p['revision'])
        return '旧草稿生成结果',memory.MemoryEvidence([],{})
    monkeypatch.setattr(memory,'summarize',raced)
    assert not asyncio.run(memory.correct_profile(1,'更正草稿',p['revision']))[0]
    assert memory.get_profile(1)['text']=='另一台设备已更正'


def test_unreviewed_generated_summary_is_not_promoted_to_user_correction(database, monkeypatch):
    history()
    async def generated(*args):return '机器生成的旧稿',[]
    monkeypatch.setattr(memory,'summarize',generated)
    asyncio.run(memory.refresh(1))
    current=memory.get_profile(1)
    assert not current['manual']
    async def corrected(sources):
        old=next(s for s in sources if s['id']=='manual-profile')
        assert old['origin']=='previous_summary'
        return memory.validated_summary({'sections':[{'title':'阅读','text':'你只在比较观点。',
            'evidence':[{'source_id':'current-correction','quote':'只在比较观点'}]}]},sources)
    monkeypatch.setattr(memory,'summarize',corrected)
    assert asyncio.run(memory.correct_profile(1,'我只在比较观点',current['revision']))[0]
