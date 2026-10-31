"""Credential separation, per-request model ownership and Responses delivery."""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import model_providers as providers
import deep_bare_agent as bare
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import StructuredTool


@pytest.fixture
def configured(monkeypatch):
    from routes import agent_llm,agent_sse
    monkeypatch.setenv('OPENAI_API_KEY','fixture-openai-credential')
    monkeypatch.setenv('DEEP_AGENT_RUNTIME','bare')
    monkeypatch.setattr(agent_llm,'API_KEY','fixture-deepseek-credential')
    monkeypatch.setattr(agent_sse,'API_KEY','fixture-deepseek-credential')
    token=providers.current_provider.set('deepseek')
    yield
    providers.current_provider.reset(token)


def test_catalog_and_factory_never_mix_keys_or_reveal_them(configured):
    metadata=providers.catalog({'id':1})
    assert all(m['available'] for m in metadata['models'])
    assert metadata['models'][1]['model']=='gpt-6.1-terra'
    assert 'credential' not in json.dumps(metadata)
    assert providers.catalog()['models'][1]['reason']=='login_required'
    c=providers.config('openai');assert c.base_url=='https://api.openai.com/v1'
    assert 'fixture-openai-credential' not in repr(c)
    with pytest.raises(ValueError):providers.config('attacker')
    model=providers.openai_model()
    second=providers.openai_model()
    assert model.model_name=='gpt-6.1-terra' and model.use_responses_api is True and model.store is False
    assert not model.extra_body and model.output_version=='responses/v1'
    assert model.http_async_client is not second.http_async_client
    model.root_client.close();asyncio.run(model.root_async_client.close())
    assert not second.http_async_client.is_closed
    second.root_client.close();asyncio.run(second.root_async_client.close())


def test_missing_key_and_anonymous_openai_are_rejected_before_generation(configured,monkeypatch):
    from routes import agent_sse as sse
    import engine_langgraph
    monkeypatch.setattr(engine_langgraph,'stream_agent',lambda *a,**kw:pytest.fail('No provider request'))
    monkeypatch.setattr(sse.guard,'resolve_user',lambda token:None)
    app=FastAPI();app.include_router(sse.router);c=TestClient(app)
    assert c.post('/api/agent/stream_lg',json={'message':'test','model_provider':'openai'}).status_code==401
    assert c.post('/api/agent/stream_lg',json={'message':'test','model_provider':'arbitrary'}).status_code==422
    monkeypatch.setattr(sse.guard,'resolve_user',lambda token:{'id':1})
    monkeypatch.delenv('OPENAI_API_KEY')
    assert c.post('/api/agent/stream_lg',json={'message':'test','model_provider':'openai'}).status_code==503


def test_concurrent_sse_tasks_and_worker_threads_keep_their_provider(configured,monkeypatch):
    from routes import agent_sse as sse
    import engine_langgraph,auth
    monkeypatch.setattr(sse.guard,'resolve_user',lambda token:{'id':9})
    monkeypatch.setattr(auth,'get_user_by_token',lambda token:None)
    async def observe(*args,**kwargs):
        before=providers.current_provider.get()
        await asyncio.sleep(.02)
        thread=await asyncio.to_thread(providers.current_provider.get)
        yield {'type':'observed','before':before,'after':providers.current_provider.get(),'thread':thread}
    monkeypatch.setattr(engine_langgraph,'stream_agent',observe)
    app=FastAPI();app.include_router(sse.router)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as c:
            responses=await asyncio.gather(*[c.post('/api/agent/stream_lg',json={'message':'test','model_provider':p},headers={'authorization':'Bearer fixture'})for p in ['deepseek','openai']])
        for provider,response in zip(['deepseek','openai'],responses):
            assert response.status_code==200
            event=json.loads(next(l[6:] for l in response.text.splitlines() if l.startswith('data: ')))
            assert event['before']==event['after']==event['thread']==provider
        assert providers.current_provider.get()=='deepseek'
    asyncio.run(run());assert providers.current_provider.get()=='deepseek'


def test_responses_blocks_and_tool_roundtrip_preserve_public_text_only(configured,monkeypatch):
    tool=StructuredTool.from_function(lambda:{'text':'合成原典摘录'},name='probe',description='Fixture read')
    seen=[]
    class Model:
        n=0
        def bind_tools(self,tools,**kwargs):assert kwargs=={'strict':False};return self
        async def astream(self,messages):
            self.n+=1;seen.extend(messages)
            if self.n==1:
                yield AIMessageChunk(content=[{'type':'reasoning','summary':[],'encrypted_content':'opaque-fixture'}],additional_kwargs={'reasoning_content':'not-public'})
                yield AIMessageChunk(content=[{'type':'text','text':'先读材料。'}])
                yield AIMessageChunk(content=[],tool_call_chunks=[{'name':'probe','args':'{}','id':'call-fixture','index':0}])
            else:
                yield AIMessageChunk(content=[{'type':'text','text':'一个个案不能推出普遍结论。'}],response_metadata={'status':'completed','model_name':'gpt-6.1-terra'})
    async def tools():return [tool]
    monkeypatch.setattr(bare,'load_tools',tools);monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *args:([],None))
    async def run():return [e async for e in bare.stream_bare_agent('分析合成论证，不要追问。',[])]
    token=providers.current_provider.set('openai')
    try:events=asyncio.run(run())
    finally:providers.current_provider.reset(token)
    done=next(e for e in events if e['type']=='done')
    assert done['content']=='一个个案不能推出普遍结论。' and done['complete']
    assert done['release']['model_provider']=='openai' and done['release']['model']=='gpt-6.1-terra'
    assert any(e['type']=='tool' and e['name']=='probe' for e in events)
    assert not any(e['type']=='provider_reasoning_delta' for e in events)
    assert 'opaque-fixture' not in json.dumps(events,ensure_ascii=False)
    assert any(m.type=='tool' and m.tool_call_id=='call-fixture' for m in seen)


def test_incomplete_responses_are_not_marked_complete(configured,monkeypatch):
    class Model:
        def bind_tools(self,tools,**kwargs):return self
        async def astream(self,messages):
            yield AIMessageChunk(content=[{'type':'text','text':'未完成'}],response_metadata={'status':'incomplete'})
    async def tools():return []
    monkeypatch.setattr(bare,'load_tools',tools);monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *args:([],None))
    token=providers.current_provider.set('openai')
    try:
        async def run():return [e async for e in bare.stream_bare_agent('问题',[])]
        events=asyncio.run(run())
    finally:providers.current_provider.reset(token)
    assert next(e for e in events if e['type']=='done')['complete'] is False


def test_provider_errors_are_safe_and_do_not_claim_fallback():
    error=SimpleNamespace(status_code=429,code='insufficient_quota')
    result=providers.error_event(error)
    assert result['code']=='openai_insufficient_quota' and '额度不足' in result['content']
    assert providers.visible_text([{'type':'function_call','arguments':'private'},{'type':'reasoning','text':'private'},{'type':'text','text':'公开'}])=='公开'
