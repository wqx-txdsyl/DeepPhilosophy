import asyncio
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from phiagent_lab.app import create_app
from phiagent_lab.engine import build_graph, initial_state, check_citations
from phiagent_lab.library import execute_tool
from phiagent_lab.model import MockModel

def test_tool_boundary():
    assert execute_tool('search_library', {'query': '自由'})[0]['id'] == 'demo-freedom'
    with pytest.raises(ValueError):
        execute_tool('__import__', {})
    with pytest.raises(ValueError):
        execute_tool('read_passage', {'passage_id': '../../etc/passwd'})
    with pytest.raises(ValueError):
        execute_tool('search_library', {'query': '自由', 'limit': '3'})
    with pytest.raises(ValueError):
        execute_tool('search_library', {'query': '自由', 'unexpected': True})

def test_citations_are_from_read_material():
    with pytest.raises(ValueError):
        check_citations('结论 [made-up]', {'demo-freedom': {}})
    with pytest.raises(ValueError):
        check_citations('无引用', {'demo-freedom': {}})
    assert check_citations('概述 [demo-freedom]', {'demo-freedom': {}}) == ['demo-freedom']

def test_graph_full_cycle_and_empty_search():
    graph = build_graph(MockModel())
    result = asyncio.run(graph.ainvoke(initial_state('自由与责任有什么关系？')))
    assert 'demo-freedom' in result['evidence']
    assert '[demo-freedom]' in result['answer']
    result = asyncio.run(graph.ainvoke(initial_state('zzzzzzzz')))
    assert not result['evidence']
    assert '不足' in result['answer']

def parse_events(text):
    return [json.loads(frame[6:]) for frame in text.split('\n\n') if frame.startswith('data: ')]

def test_api_persistence_isolation_and_validation(tmp_path):
    app = create_app(model=MockModel(), db_path=tmp_path / 'test.sqlite3')
    cid = str(uuid.uuid4())
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        assert client.get('/api/health').json()['ok'] is True
        assert client.post('/api/chat', json={'conversation_id': cid, 'message': ' '}).status_code == 422
        assert client.post('/api/chat', json={'conversation_id': 'bad', 'message': '自由'}).status_code == 422
        response = client.post('/api/chat', json={'conversation_id': cid, 'message': '自由与责任'})
        events = parse_events(response.text)
        assert events[-1]['type'] == 'done'
        assert any(e['type'] == 'source' for e in events)
        assert len(client.get(f'/api/conversations/{cid}').json()) == 2
        assert client.get(f'/api/conversations/{uuid.uuid4()}').json() == []
        app.state.active.add(cid)
        assert client.post('/api/chat', json={'conversation_id': cid, 'message': '自由'}).status_code == 409
        app.state.active.remove(cid)
    with TestClient(create_app(model=MockModel(), db_path=tmp_path / 'test.sqlite3')) as client:
        assert len(client.get(f'/api/conversations/{cid}').json()) == 2

class BadCitationModel(MockModel):
    async def stream(self, messages):
        yield '未经核实的结论 [fabricated-source]'

def test_bad_answer_is_not_saved(tmp_path):
    app = create_app(model=BadCitationModel(), db_path=tmp_path / 'bad.sqlite3')
    with TestClient(app) as client:
        cid = str(uuid.uuid4())
        events = parse_events(client.post('/api/chat', json={'conversation_id': cid, 'message': '自由'}).text)
        assert events[-1]['type'] == 'error'
        assert client.get(f'/api/conversations/{cid}').json() == []
        assert not app.state.active

class EndlessModel(MockModel):
    async def decide(self, messages, tools):
        return {'role': 'assistant', 'content': '', 'tool_calls': [{
            'id': str(uuid.uuid4()), 'type': 'function',
            'function': {'name': 'search_library', 'arguments': '{"query":"自由"}'},
        }]}

def test_loop_is_bounded():
    result = asyncio.run(build_graph(EndlessModel(), max_rounds=2).ainvoke(initial_state('自由')))
    assert result['rounds'] == 2
    assert len([m for m in result['messages'] if m['role'] == 'tool']) == 2

class WrongArgsModel(MockModel):
    async def decide(self, messages, tools):
        if messages[-1]['role'] == 'tool':
            return {'role': 'assistant', 'content': '没有材料'}
        return {'role': 'assistant', 'content': '', 'tool_calls': [{
            'id': 'bad', 'type': 'function',
            'function': {'name': 'read_passage', 'arguments': '{"passage_id":"missing"}'},
        }]}

def test_tool_error_is_returned_to_model():
    result = asyncio.run(build_graph(WrongArgsModel()).ainvoke(initial_state('自由')))
    tool = next(m for m in result['messages'] if m['role'] == 'tool')
    assert 'error' in json.loads(tool['content'])
    assert not result['evidence']
