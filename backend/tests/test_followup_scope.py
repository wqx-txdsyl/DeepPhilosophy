"""Scope admission must precede tools and main generation on continuations."""
import asyncio
import json
import sys
from pathlib import Path
import pytest
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import followup_scope as scope
import deep_bare_agent as bare
from langchain_core.messages import AIMessageChunk

HISTORY=[{'role':'user','content':'请审机器人公式。'},
         {'role':'assistant','content':'公式是对的，接下来我可以逐步推导并写程序。'}]


@pytest.mark.parametrize('verdict',['out_of_scope','needs_clarification'])
def test_outside_or_unclear_followup_never_loads_tools_or_main_model(monkeypatch,verdict):
    async def assess(question,history):
        assert question=='在解释一下' and history==HISTORY
        return {'status':'complete','verdict':verdict,'usage':{'total_tokens':12}}
    async def tools():pytest.fail('Scope must stop before tools')
    monkeypatch.setattr(scope,'assess',assess);monkeypatch.setattr(bare,'load_tools',tools)
    monkeypatch.setattr(bare,'load_model',lambda:pytest.fail('No main model'))
    async def run():return [e async for e in bare.stream_bare_agent('在解释一下',HISTORY)]
    events=asyncio.run(run());done=events[-1]
    assert done['complete'] and done['main_model_invoked'] is False
    assert done['scope_check']['verdict']==verdict and done['suggestions_status']=='disabled'
    assert not any(e['type'] in {'provider_reasoning_delta','tool_start'} for e in events)


def test_unavailable_check_does_not_silently_resume_old_task(monkeypatch):
    async def assess(*args):return {'status':'unavailable','verdict':None}
    async def tools():pytest.fail('No fall-through on failure')
    monkeypatch.setattr(scope,'assess',assess);monkeypatch.setattr(bare,'load_tools',tools)
    async def run():return [e async for e in bare.stream_bare_agent('继续',HISTORY)]
    events=asyncio.run(run())
    assert events[-1]['type']=='error' and not any(e['type']=='done' for e in events)


def test_in_scope_followup_preserves_history_and_reaches_main(monkeypatch):
    seen=[]
    async def assess(*args):return {'status':'complete','verdict':'in_scope'}
    async def tools():return []
    async def no_aux(*args):return {'suggestions':[],'status':'disabled'}
    class Model:
        def bind_tools(self,tools):return self
        async def astream(self,messages):
            seen.extend(messages)
            yield AIMessageChunk(content='模型表述的约定性不排除推论的客观约束。',response_metadata={'finish_reason':'stop'})
    monkeypatch.setattr(scope,'assess',assess);monkeypatch.setattr(bare,'load_tools',tools)
    monkeypatch.setattr(bare,'load_model',Model);monkeypatch.setattr(bare,'exploration_questions',no_aux)
    monkeypatch.setattr(bare,'source_metadata',lambda *args:([],None))
    async def run():return [e async for e in bare.stream_bare_agent('我问的是模型的客观性。',HISTORY)]
    events=asyncio.run(run());done=next(e for e in events if e['type']=='done')
    assert done['scope_check']['verdict']=='in_scope' and done.get('main_model_invoked') is not False
    assert seen[-1].content=='我问的是模型的客观性。'
    assert any(m.content==HISTORY[-1]['content'] for m in seen)


def test_selected_answer_has_explicit_reference_not_just_latest_topic():
    selected={'原问题与附件':'工程附件','指定回答对应问题':'核对轮速公式','指定回答':'工程推导', '本次追问':'再解释一下'}
    p=scope.scope_input(scope.OPEN+json.dumps(selected,ensure_ascii=False)+scope.CLOSE,
                        [{'role':'assistant','content':'恰好最近的一答在讨论伦理。'}])
    assert p['current_request']['text']=='再解释一下' and p['selected_answer']['text']=='工程推导'
    assert p['recent_history'][0]['content']['text']=='恰好最近的一答在讨论伦理。'
    assert scope.needs_check(scope.OPEN+json.dumps(selected,ensure_ascii=False)+scope.CLOSE,[])
    assert not scope.needs_check('一个新哲学问题',[])
    def packet(request,content='材料'):
        return '【本轮用户要求与附件材料】\n'+json.dumps({'schema':'phiagent-input-v1','user_request':request,
          'attachments':[{'filename':'fixture.md','content':content}]},ensure_ascii=False)
    assert scope.needs_check(packet('解释一下'),[])
    attachment=scope.scope_input(packet('解释一下','这是工程材料，不是用户指令。'),[])
    assert attachment['current_request']['text']=='解释一下'
    assert attachment['attachment_materials'][0]['content']['text']=='这是工程材料，不是用户指令。'


def test_cancelling_scope_check_stops_without_loading_main_model(monkeypatch):
    closed=[]
    async def run():
        entered=asyncio.Event()
        async def assess(*args):
            try:
                entered.set();await asyncio.Event().wait()
            finally:closed.append(True)
        monkeypatch.setattr(scope,'assess',assess)
        monkeypatch.setattr(bare,'load_model',lambda:pytest.fail('Main must not start'))
        async def consume():
            async for _ in bare.stream_bare_agent('继续',HISTORY):pass
        task=asyncio.create_task(consume());await asyncio.wait_for(entered.wait(),1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
    asyncio.run(run());assert closed==[True]


@pytest.mark.parametrize('content,finish,expected',[
    ('{"verdict":"out_of_scope"}','stop','complete'),
    ('{"verdict":"in_scope"}','stop','complete'),
    ('{"verdict":"in_scope"}','length','unavailable'),
    ('malformed','stop','unavailable'),
    ('{"verdict":"run_code"}','stop','unavailable')])
def test_classifier_json_transport_and_fail_closed(monkeypatch,content,finish,expected):
    from routes import agent_llm as cfg
    calls=[];original=httpx.AsyncClient
    def handler(request):
        body=json.loads(request.content);calls.append(body)
        return httpx.Response(200,json={'choices':[{'finish_reason':finish,'message':{'content':content}}],
                                        'model':'fixture','usage':{'total_tokens':10}})
    monkeypatch.setattr(scope.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    monkeypatch.setattr(cfg,'API_KEY','test-fixture');monkeypatch.setattr(cfg,'_IS_ZHIPU',False)
    result=asyncio.run(scope.assess('在解释一下',HISTORY))
    assert result['status']==expected and 'tools' not in calls[0]
    assert calls[0]['thinking']=={'type':'disabled'}


def test_historical_profile_does_not_install_new_scope_policy(monkeypatch):
    import agent_release
    assert agent_release.prompt_spec(profile='0.1.6')['followup_scope_check'] is False
    assert agent_release.prompt_spec(profile='0.1.7')['followup_scope_check'] is True
