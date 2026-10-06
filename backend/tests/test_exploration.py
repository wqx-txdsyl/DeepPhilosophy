import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deep_exploration import generate_exploration
from routes import agent_llm


def test_generated_questions_use_full_answer_and_avoid_static_or_repeated_entries(monkeypatch):
    calls=[]
    def llm(messages,**kw):
        calls.append((messages,kw))
        return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'questions':['检验反例？','已有的问题？','若没有回报期待，感谢还会产生义务吗？','拒绝礼物是否也可以承认对方的心意？']},ensure_ascii=False)}}]}
    monkeypatch.setattr(agent_llm,'llm_chat',llm)
    answer='完整正文'*1000+'末尾关键限制'
    result=generate_exploration('送礼是否表达尊重？',answer,previous=['已有的问题？'])
    assert result['status']=='ready' and len(result['suggestions'])==2
    assert json.loads(calls[0][0][1]['content'])['answer']==answer
    assert calls[0][1]['disable_thinking'] is True


def test_failed_generation_has_no_static_fallback(monkeypatch):
    monkeypatch.setattr(agent_llm,'llm_chat',lambda *a,**k:{'choices':[{'finish_reason':'length','message':{'content':'partial'}}]})
    assert generate_exploration('问题','回答')['status']=='unavailable'
    assert generate_exploration('请不要提供追问','回答')['status']=='disabled'


def test_regeneration_route_accepts_context_and_previous_questions(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes import agent_sse
    import deep_exploration
    monkeypatch.setenv('DEEP_AGENT_RUNTIME','bare')
    monkeypatch.setattr(agent_sse.guard,'resolve_user',lambda auth:None)
    monkeypatch.setattr(deep_exploration,'generate_exploration',lambda q,a,l,p:{'suggestions':[q+'？'],'status':'ready'})
    app=FastAPI();app.include_router(agent_sse.router)
    response=TestClient(app).post('/api/agent/exploration',json={'message':'具体难点','answer':'完整回答','previous_questions':['旧问题？'],'language':'zh'})
    assert response.status_code==200 and response.json()['suggestions']==['具体难点？']


def test_answer_done_precedes_questions_and_failure_does_not_change_answer(monkeypatch):
    import deep_bare_agent as bare
    from langchain_core.messages import AIMessageChunk
    class Model:
        def bind_tools(self,tools):return self
        async def astream(self,messages):yield AIMessageChunk(content='回答正文',response_metadata={'finish_reason':'stop'})
    async def tools():return []
    async def questions(*args):raise RuntimeError('optional metadata failure')
    monkeypatch.setattr(bare,'load_tools',tools)
    monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *a:([],None))
    monkeypatch.setattr(bare,'exploration_questions',questions)
    async def run():return [e async for e in bare.stream_bare_agent('问题',[])]
    events=asyncio.run(run());done=next(e for e in events if e['type']=='done')
    assert done['content']=='回答正文' and done['suggestions_status']=='pending'
    assert events[-1]=={'type':'suggestions','suggestions':[],'status':'unavailable'}
    assert not any(e['type']=='error' for e in events)
