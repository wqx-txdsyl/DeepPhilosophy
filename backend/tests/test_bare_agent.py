"""Offline wiring only; no provider request or philosophical answer evaluation."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import StructuredTool
import deep_bare_agent as bare


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
    assert events[-1]['content'] == final and events[-1]['validation'] == {'enabled':False}
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
