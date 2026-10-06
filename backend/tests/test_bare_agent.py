"""Offline wiring only; no provider request or philosophical answer evaluation."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import StructuredTool
import deep_bare_agent as bare
import pytest


@pytest.fixture(autouse=True)
def no_real_exploration_requests(monkeypatch):
    async def no_suggestions(*args):return {'suggestions':[], 'status':'unavailable'}
    monkeypatch.setattr(bare,'exploration_questions',no_suggestions)


def test_no_round_budget_dedup_context_truncation_or_answer_rewrite(monkeypatch):
    executions = []
    seen = []
    payload = '资料' * 20000
    def read(query: str):
        executions.append(query)
        return {'text': payload}
    tool = StructuredTool.from_function(read, name='search_books', description='Fixture')
    final = '🧭 > 未核验的原话【《虚构书籍》·第九章】'
    class Model:
        index = 0
        def bind_tools(self, tools):
            assert tools == [tool]
            return self
        async def astream(self, messages):
            seen.append(list(messages))
            self.index += 1
            if self.index <= 35:
                for i in range(2):
                    yield AIMessageChunk(content='', tool_call_chunks=[{'name':'search_books',
                        'args':'{"query":"重复查询"}', 'id':f'call-{self.index}-{i}', 'index':i}])
            else:
                yield AIMessageChunk(content=final, response_metadata={'finish_reason':'stop'})
    async def tools():return [tool]
    monkeypatch.setattr(bare, 'load_tools', tools)
    monkeypatch.setattr(bare, 'load_model', Model)
    monkeypatch.setattr(bare, 'source_metadata', lambda *args: ([], None))
    async def run():
        return [e async for e in bare.stream_bare_agent('问题', [{'role':'user','content':f'history-{i}'} for i in range(30)])]
    events = asyncio.run(run())
    assert len(executions) == 70  # exceeds both former tool and graph limits
    assert len(seen) == 36
    assert all(sum(m.type == 'system' for m in ms) == 1 for ms in seen)
    assert seen[0][1].content == 'history-0'
    assert json.loads(next(m.content for m in seen[-1] if m.type == 'tool'))['text'] == payload
    done=next(e for e in events if e['type']=='done')
    assert done['content'] == final and done['validation'] == {'enabled':False}
    assert not any(e['type'] == 'validation_failed' for e in events)


def test_provider_stream_cancellation_closes_generator(monkeypatch):
    closed = []
    class Model:
        def bind_tools(self, tools):return self
        async def astream(self, messages):
            try:
                yield AIMessageChunk(content='已输出')
                await asyncio.Event().wait()
            finally:
                closed.append(True)
    async def tools():return []
    monkeypatch.setattr(bare, 'load_tools', tools)
    monkeypatch.setattr(bare, 'load_model', Model)
    async def run():
        stream = bare.stream_bare_agent('问题', [])
        async for event in stream:
            if event['type'] == 'answer_preview':break
        await stream.aclose()
    asyncio.run(run())
    assert closed == [True]


def test_interim_answers_are_committed_before_tools_and_not_lost(monkeypatch):
    class Model:
        index = 0
        def bind_tools(self, tools):return self
        async def astream(self, messages):
            self.index += 1
            yield AIMessageChunk(content='', additional_kwargs={'reasoning_content': f'思考{self.index}'})
            if self.index <= 2:
                yield AIMessageChunk(content=f'中间回答{self.index}。')
                yield AIMessageChunk(content='', tool_call_chunks=[{'name':'probe','args':'{}','id':f'call{self.index}','index':0}])
                # Providers can place more content beside/after tool fragments.
                yield AIMessageChunk(content='补充一句。')
            else:
                yield AIMessageChunk(content='最终回答。', response_metadata={'finish_reason':'stop'})
    tool=StructuredTool.from_function(lambda: {'text':'材料'}, name='probe', description='Fixture')
    async def tools():return [tool]
    monkeypatch.setattr(bare,'load_tools',tools)
    monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *a:([],None))
    async def run():return [e async for e in bare.stream_bare_agent('问题',[])]
    events=asyncio.run(run())
    notes={}
    for index,event in enumerate(events):
        if event['type']=='assistant_commentary':
            if event['id'] not in notes:
                assert events[index+1]['type']=='answer_preview_reset'
            notes[event['id']]=event['content']
    assert list(notes.values())==['中间回答1。补充一句。','中间回答2。补充一句。']
    assert not any(e['type']=='thinking_summary' for e in events)
    assert next(e for e in events if e['type']=='done')['content']=='最终回答。'


def test_general_route_bypasses_request_quotas_only_in_bare_mode(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes import agent_sse
    import engine_langgraph
    monkeypatch.setenv('DEEP_AGENT_RUNTIME','bare')
    monkeypatch.setattr(agent_sse,'API_KEY','offline')
    monkeypatch.setattr(agent_sse.guard,'resolve_user',lambda auth: None)
    def old_guard(*args):raise AssertionError('Old request quota executed')
    monkeypatch.setattr(agent_sse.guard,'agent_guard',old_guard)
    async def stream(*args,**kwargs):yield {'type':'done','content':'offline','complete':True}
    monkeypatch.setattr(engine_langgraph,'stream_agent',stream)
    app=FastAPI();app.include_router(agent_sse.router)
    response=TestClient(app).post('/api/agent/stream_lg',json={'message':'offline','agent':'general'})
    assert response.status_code == 200 and 'offline' in response.text


def test_resumed_reasoning_preserves_spoken_text_without_a_tool(monkeypatch):
    class Model:
        def bind_tools(self, tools):return self
        async def astream(self, messages):
            yield AIMessageChunk(content='',additional_kwargs={'reasoning_content':'第一段思考'})
            yield AIMessageChunk(content='先回应一句。')
            yield AIMessageChunk(content='',additional_kwargs={'reasoning_content':'再想一下'})
            yield AIMessageChunk(content='最终结论。',response_metadata={'finish_reason':'stop'})
    async def tools():return []
    monkeypatch.setattr(bare,'load_tools',tools)
    monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *a:([],None))
    async def run():return [e async for e in bare.stream_bare_agent('问题',[])]
    events=asyncio.run(run())
    note=next(e for e in events if e['type']=='assistant_commentary')
    assert note['content']=='先回应一句。'
    assert len({e['id'] for e in events if e['type']=='provider_reasoning_delta'})==2
    assert next(e for e in events if e['type']=='done')['content']=='最终结论。'


def test_saved_preferences_reach_bare_model_without_replacing_identity_or_current_question(monkeypatch):
    seen=[]
    class Model:
        def bind_tools(self, tools):return self
        async def astream(self, messages):
            seen.extend(messages)
            yield AIMessageChunk(content='fixture answer', response_metadata={'finish_reason':'stop'})
    async def tools():return []
    monkeypatch.setattr(bare,'load_tools',tools);monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *args:([],None))
    async def run():return [e async for e in bare.stream_bare_agent('这次请深入展开',[],custom_instructions='通常简短回答')]
    asyncio.run(run())
    assert len([m for m in seen if m.type=='system'])==1
    assert '通常简短回答' in seen[1].content and '当前请求优先' in seen[1].content
    assert seen[-1].content=='这次请深入展开'


def test_production_general_dispatch_forwards_saved_preferences(monkeypatch):
    import engine_langgraph
    received=[]
    async def fake(question, history, **kwargs):
        received.append((question,history,kwargs))
        yield {'type':'done','content':'fixture'}
    monkeypatch.setenv('DEEP_AGENT_RUNTIME','bare')
    monkeypatch.setattr(bare,'stream_bare_agent',fake)
    async def run():return [event async for event in engine_langgraph.stream_agent('现在展开理由',[],custom_instructions='通常简洁')]
    asyncio.run(run())
    assert received[0][2]['custom_instructions']=='通常简洁'
    assert received[0][0]=='现在展开理由'
