"""Test model-facing tool wiring, not only underlying implementation functions."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def test_map_relations_survive_actual_langchain_boundary():
    from engine_langgraph import _build_tools
    tool=next(t for t in _build_tools(general=True) if t.name=='conceptual_map')
    result=tool.invoke({'concept':'推理','map_type':'ARGUMENT_GRAPH','nodes':['前提','结论'],
                        'relations':[{'from':'前提','to':'结论','label':'支持'}]})
    assert not result.get('error')
    assert '支持' in str(result) and '前提' in str(result) and '结论' in str(result)
    schema=tool.args_schema.model_json_schema()
    assert {'from','to'} <= set(schema['properties']['relations']['items']['properties'])


def test_unknown_arguments_are_not_silently_ignored():
    import pytest
    from pydantic import ValidationError
    from engine_langgraph import _build_tools
    tool=next(t for t in _build_tools(general=True) if t.name=='conceptual_map')
    with pytest.raises(ValidationError):tool.invoke({'concept':'图','edges':[]})
    result=tool.invoke({'concept':'图','nodes':['甲','乙'],'relations':[]})
    assert result['graph']['edges']==[]
    failed=tool.invoke({'concept':'图','nodes':['甲','乙'],'relations':[{'source':'甲','target':'乙'}]})
    assert failed['error']=='INVALID_GRAPH_RELATIONS'


def test_candidate_prompt_does_not_leak_old_reinforcement(monkeypatch):
    from engine_langgraph import _build_context_messages,get_system_prompt
    old=get_system_prompt('general')
    monkeypatch.setenv('DEEP_PROMPT_VERSION','v2')
    candidate=get_system_prompt('general')
    assert len(candidate)<len(old)
    reminder='\n'.join(m.content for m in _build_context_messages('general','zh',reinforce=True))
    assert '日常反思优先写成' not in reminder
    assert '思考' in reminder and '中文' in reminder
    assert get_system_prompt('nietzsche') != candidate


def test_tool_enum_rejects_invalid_access_before_execution():
    import pytest
    from pydantic import ValidationError
    from engine_langgraph import _build_tools
    tool=next(t for t in _build_tools(general=True) if t.name=='get_scholarly_source')
    with pytest.raises(ValidationError):
        tool.invoke({'source_record_id':'irrelevant','requested_access':'FULL_TEXT'})


def test_school_alias_and_ambiguity(tmp_path,monkeypatch):
    import json
    from routes import agent_tools_retrieval as retrieval
    monkeypatch.setattr(retrieval,'SCHOOLS_DIR',tmp_path)
    (tmp_path/'a.json').write_text(json.dumps({'name':'斯多葛学派'}))
    assert retrieval._exec_school({'name':'斯多葛主义'})['name']=='斯多葛学派'
    (tmp_path/'b.json').write_text(json.dumps({'name':'新斯多葛学派'}))
    assert retrieval._exec_school({'name':'斯多葛'})['error']=='流派名称不唯一'


def test_generated_image_route_returns_file_not_spa(tmp_path,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes import agent_assets
    monkeypatch.setattr(agent_assets,'AGNES_IMG_DIR',tmp_path)
    content=b'\x89PNG\r\n\x1a\nfixture'
    (tmp_path/'0123456789ab.png').write_bytes(content)
    app=FastAPI();app.include_router(agent_assets.router)
    client=TestClient(app)
    response=client.get('/agent_images/0123456789ab.png')
    assert response.content==content and response.headers['content-type']=='image/png'
    assert client.get('/agent_images/ffffffffffff.png').status_code==404
    assert client.get('/agent_images/.env').status_code==404


def test_single_system_preserves_policy_and_tool_history_without_mutation():
    from engine_langgraph import _consolidate_system_messages
    from langchain_core.messages import SystemMessage,HumanMessage,AIMessage,ToolMessage
    original=[SystemMessage(content='主策略'),HumanMessage(content='问题'),AIMessage(content='',tool_calls=[{'name':'read','args':{},'id':'t'}]),ToolMessage(content='原文',tool_call_id='t'),SystemMessage(content='每轮提醒')]
    result=_consolidate_system_messages(original)
    assert sum(isinstance(m,SystemMessage) for m in result)==1
    assert result[0].content=='主策略\n\n每轮提醒'
    assert result[1:]==original[1:4] and original[0].content=='主策略'


def test_book_list_metadata_is_not_cut_into_invalid_json():
    import json
    from deep_tool_context import tool_context
    result={'books':[{'id':str(i),'title':'书目'+str(i),'summary':'材料'*90} for i in range(30)]}
    content,delivery=tool_context('list_books',result,'general')
    assert len(content)>4000 and json.loads(content)==result and delivery['status']=='complete'
