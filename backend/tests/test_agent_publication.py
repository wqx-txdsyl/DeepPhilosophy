"""Approved public roster, retirement enforcement, and preserved persona data."""
import asyncio
import sys
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from soul_agents import catalog, active_catalog, published_philosophers, is_soul_agent, is_retired_agent, soul_prompt

APPROVED = set('''confucius laozi zhuangzi mencius xunzi mozi han_fei zhu_xi wang_yangming
mao_zedong buddha socrates plato aristotle epicurus marcus_aurelius augustine aquinas
machiavelli francis_bacon descartes hobbes spinoza locke leibniz hume rousseau adam_smith
kant hegel schopenhauer marx nietzsche js_mill heidegger sartre beauvoir russell
wittgenstein foucault'''.split())
RETIRED = set(catalog()) - APPROVED


def test_approved_forty_and_preserved_eighty():
    assert len(APPROVED) == 40 and set(published_philosophers()) == APPROVED
    assert len(active_catalog()) == 39 and len(RETIRED) == 80
    assert len(catalog()) == 119
    assert all(is_soul_agent(key) for key in APPROVED - {'nietzsche'})
    for key in RETIRED:
        assert is_retired_agent(key) and not is_soul_agent(key)
        assert catalog()[key]['name'] in soul_prompt(key)  # Retain data, not publication.


def test_public_endpoint_exposes_exactly_forty_one_and_is_not_cached(monkeypatch):
    from routes.agent import router
    import routes.agent_core as core
    import agents
    monkeypatch.setattr(agents, 'PHILO_AGENTS', {**agents.PHILO_AGENTS,
        'arendt':{'name':'阿伦特', 'title':'不应通过旧注册表重新上架'}})
    monkeypatch.setattr(core, 'get_books', lambda:[])
    app=FastAPI();app.include_router(router)
    response=TestClient(app).get('/api/agents')
    assert response.status_code == 200
    rows=response.json()['agents']
    assert len(rows) == 41 and {r['key'] for r in rows} == APPROVED | {'general'}
    assert response.headers['Cache-Control'] == 'no-store'
    assert not RETIRED.intersection(r['key'] for r in rows)


@pytest.mark.parametrize('key', sorted(RETIRED))
def test_retired_api_calls_are_gone_before_auth_quota_or_model(monkeypatch, key):
    from routes import agent_sse
    import engine_langgraph
    def forbidden(*args, **kwargs): raise AssertionError('Retired agent must not execute')
    monkeypatch.setattr(agent_sse.guard, 'resolve_user', forbidden)
    monkeypatch.setattr(agent_sse.guard, 'agent_guard', forbidden)
    monkeypatch.setattr(engine_langgraph, 'stream_agent', forbidden)
    app=FastAPI();app.include_router(agent_sse.router)
    client=TestClient(app)
    for endpoint in ('stream_lg','exploration'):
        response=client.post('/api/agent/'+endpoint, json={'agent':key,'message':'继续', 'answer':'旧答复'})
        assert response.status_code == 410 and '已下架' in response.json()['detail']


@pytest.mark.parametrize('key', sorted(RETIRED))
def test_retired_engine_and_adapter_calls_cannot_fall_back_to_general(monkeypatch, key):
    import engine_langgraph
    import soul_agent_runtime
    import deep_bare_agent
    def forbidden(): raise AssertionError('No model for retired agents')
    monkeypatch.setattr(deep_bare_agent, 'load_model', forbidden)
    async def collect():
        for stream in (engine_langgraph.stream_agent('继续',[],key),
                       soul_agent_runtime.stream_soul_agent('继续',[],key)):
            events=[e async for e in stream]
            assert len(events) == 1 and events[0]['code'] == 'agent_retired'
            assert events[0]['type'] == 'error'
    asyncio.run(collect())


def test_unknown_agent_cannot_fall_back_to_general_at_public_api():
    from routes.agent_sse import router
    app=FastAPI();app.include_router(router)
    response=TestClient(app).post('/api/agent/stream_lg',json={'agent':'not_registered','message':'你好'})
    assert response.status_code == 404
