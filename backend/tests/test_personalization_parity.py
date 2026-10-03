import asyncio
import json
import sys
import pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from account_context_messages import personalization_messages


def test_user_settings_have_distinct_provenance_without_new_system_prompt():
    result=personalization_messages({'user_settings':{'about':'我是高中生','custom_instructions':'分步骤讲解'},
        'memory_profile':'用户说过我不是人','explicit_memories':[]})
    assert len(result)==2 and all(m.type=='human' for m in result)
    assert '用户亲自在设置中填写' in result[0].content
    assert '高中生' in result[0].content
    assert '不能推翻' in result[0].content
    assert '当前请求优先' in result[0].content
    assert '我不是人' in result[1].content


def test_recall_returns_only_editable_personalization(monkeypatch):
    import account_memory_tools as tools
    import account_memory_profile,auth
    from deep_context import current_account_id
    monkeypatch.setattr(account_memory_profile,'get_profile',lambda uid:{'enabled':True,'text':'摘要','manual':False})
    monkeypatch.setattr(auth,'get_profile',lambda uid:{'about':'高中生','custom_instructions':'简单讲','token':'private'})
    monkeypatch.setattr(tools.account_data,'list_memories',lambda uid:[])
    token=current_account_id.set('synthetic')
    try:
        value=tools.recall_account_memory()
        assert value['user_settings']=={'about':'高中生','custom_instructions':'简单讲'}
        assert value['memory_profile']=='摘要' and value['memories']==[]
    finally:current_account_id.reset(token)


@pytest.mark.parametrize('agent',['nietzsche','kant','confucius'])
def test_persona_sse_carries_authenticated_scope_and_no_old_quota(monkeypatch,agent):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes import agent_sse
    from deep_context import current_account_id
    import engine_langgraph
    monkeypatch.setattr(agent_sse,'API_KEY','offline')
    monkeypatch.setattr(agent_sse.guard,'resolve_user',lambda auth:{'id':'synthetic'})
    monkeypatch.setattr(agent_sse.guard,'agent_guard',lambda *a: (_ for _ in ()).throw(AssertionError('old quota')))
    async def stream(*a,**kw):
        assert current_account_id.get()=='synthetic'
        yield {'type':'done','content':'scope correct','complete':True}
    monkeypatch.setattr(engine_langgraph,'stream_agent',stream)
    app=FastAPI();app.include_router(agent_sse.router)
    response=TestClient(app).post('/api/agent/stream_lg',json={'agent':agent,'message':'测试'})
    assert response.status_code==200 and 'scope correct' in response.text
    assert current_account_id.get() is None


def test_nietzsche_shared_stream_preserves_interim_without_exploration(monkeypatch):
    import deep_bare_agent as bare
    import nietzsche_runtime as persona
    from langchain_core.messages import AIMessageChunk
    from langchain_core.tools import StructuredTool
    seen=[]
    tool=StructuredTool.from_function(lambda:{'text':'原文'},name='probe',description='Fixture')
    async def tools():return [tool]
    async def suggestions(*args):raise AssertionError('Philosophers must not generate exploration')
    monkeypatch.setattr(persona,'tools',tools)
    monkeypatch.setattr(persona,'system_text',lambda *a:'尼采身份')
    monkeypatch.setattr(persona,'citations',lambda *a:([],None))
    monkeypatch.setattr(bare,'exploration_questions',suggestions)
    class Model:
        n=0
        def bind_tools(self,tools):return self
        async def astream(self,messages):
            assert messages[0].content=='尼采身份'
            self.n+=1
            yield AIMessageChunk(content='',additional_kwargs={'reasoning_content':'本轮思考'})
            if self.n==1:
                yield AIMessageChunk(content='先回应。')
                yield AIMessageChunk(content='',tool_call_chunks=[{'name':'probe','args':'{}','id':'p1','index':0}])
            else:yield AIMessageChunk(content='完成。',response_metadata={'finish_reason':'stop'})
    monkeypatch.setattr(bare,'load_model',Model)
    async def run():return [e async for e in bare.stream_bare_agent('问题',[],agent='nietzsche')]
    events=asyncio.run(run())
    assert any(e['type']=='assistant_commentary' and e['content']=='先回应。' for e in events)
    done=next(e for e in events if e['type']=='done')
    assert done['content']=='完成。'
    assert done['suggestions_status']=='disabled'
    assert not any(e['type']=='suggestions' for e in events)
