import asyncio
import json
import httpx
import pytest
from phiagent_lab.model import HttpModel

def model_for(monkeypatch, handler):
    monkeypatch.setenv('PHI_API_KEY', 'test-only-not-a-real-key')
    monkeypatch.setenv('PHI_MODEL', 'fixture-model')
    monkeypatch.setenv('PHI_API_BASE', 'https://api.deepseek.com')
    model = HttpModel()
    model.client = lambda: httpx.AsyncClient(base_url=model.base+'/', transport=httpx.MockTransport(handler))
    return model

async def collect(model):
    return ''.join([part async for part in model.stream([{'role':'user','content':'自由'}])])

def test_http_decision_contract(monkeypatch):
    def handle(request):
        payload = json.loads(request.content)
        assert request.url.path == '/chat/completions'
        assert payload['thinking'] == {'type':'disabled'}
        assert payload['tools'] == []
        return httpx.Response(200,json={'choices':[{'message':{'role':'assistant','content':'ok','ignored':'value'}}]})
    model = model_for(monkeypatch, handle)
    assert asyncio.run(model.decide([],[])) == {'role':'assistant','content':'ok'}

def test_http_stream_success(monkeypatch):
    content = 'data: {"choices":[{"delta":{"content":"自由"}}]}\n\ndata: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
    model = model_for(monkeypatch, lambda request: httpx.Response(200,text=content))
    assert asyncio.run(collect(model)) == '自由'

@pytest.mark.parametrize('status',[401,429,500])
def test_http_error_status(monkeypatch,status):
    model = model_for(monkeypatch, lambda request: httpx.Response(status,text='failure'))
    with pytest.raises(httpx.HTTPStatusError): asyncio.run(collect(model))

@pytest.mark.parametrize('content',[
    'data: {"choices":[{"delta":{"content":"半截"}}]}\n\n',
    'data: {"choices":[{"delta":{},"finish_reason":"length"}]}\n\ndata: [DONE]\n\n',
    'data: {"error":{"message":"bad"}}\n\n',
])
def test_incomplete_or_failed_stream(monkeypatch,content):
    model = model_for(monkeypatch, lambda request: httpx.Response(200,text=content))
    with pytest.raises(RuntimeError): asyncio.run(collect(model))
