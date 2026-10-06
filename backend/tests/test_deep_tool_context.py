"""Offline tool-to-main-model transport checks, including provider serialization."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai.chat_models.base import _convert_message_to_dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import engine_langgraph as E
import deep_reasoning_tools as reasoning
import deep_tool_context as context
from tool_contracts import TOOL_TAXONOMY
from deep_research import DeepDuplicateGuard, DeepResearchDiscipline


def payload(name, size=900):
    if name == "analyze_argument":
        return {"conclusion": "CONCLUSION", "premises": [{"premise": "前提内容。" * size, "kind": "explicit"}],
                "hidden_assumptions": ["BRIDGE"], "fallacies": [],
                "counterexample": {"scenario": "COUNTER", "premises_still_hold": "STILL_HOLD", "conclusion_fails": "FAILS"},
                "strongest_reply": "REPLY", "weakest_point": "WEAK_POINT", "strengthening": ["CONDITION"],
                "question_fidelity": "FIDELITY"}
    return {"genre_judgment": "片段", "thesis": {"statement": "论点内容。" * size, "clarity": "clear", "originality": "new"},
            "structure": {"strengths": ["STRENGTH"], "weaknesses": ["WEAKNESS"]},
            "evidence": {"use": "EVIDENCE", "gaps": ["GAP"]}, "strongest_objection": "OBJECTION",
            "writing": "WRITING", "contribution": "CONTRIBUTION", "priority_actions": ["ACTION"]}


def install(monkeypatch, name, data):
    monkeypatch.setattr(reasoning, "llm_chat", lambda *args, **kwargs: {
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(data, ensure_ascii=False)}}]})
    registry = {tool.name: tool for tool in E._build_tools(general=True)}
    monkeypatch.setattr(E, "get_tools", lambda agent: [registry[name]])
    captured = []

    async def capture(agent, messages, **kwargs):
        captured.append([_convert_message_to_dict(m) for m in messages if isinstance(m, ToolMessage)])
        return AIMessage(content="离线捕获结束。"), 0

    monkeypatch.setattr(E, "_agent_llm_invoke", capture)
    return captured


def state_for(name, ids=("one",), agent="general"):
    call = AIMessage(content="", tool_calls=[{"name": name, "args": {"text": "待审读的离线论证"}, "id": i} for i in ids])
    return {"agent": agent, "language": "zh", "messages": [HumanMessage(content="固定原问题"), call],
            "guard": DeepDuplicateGuard(), "budget": E.AR.ToolBudget(set()),
            "discipline": DeepResearchDiscipline() if agent == "general" else None,
            "raw_tool_log": [], "tool_count": 0, "message_checkpoint": [], "request_message": "固定原问题"}


@pytest.mark.parametrize('name', sorted(context.PRIMARY_CONTEXT_TOOLS | context.SCHOLARLY_CONTEXT_TOOLS))
def test_primary_research_metadata_and_middle_passages_survive_transport_and_later_rounds(name):
    data = {'text': '前文。' * 850 + '中心原文不能丢失' + '后文。' * 850,
            'results': [{'book_id': 'actual-id', 'read_args': {'book_id': 'actual-id', 'chapter_idx': 9}}],
            'catalogue_matches': [{'book_id': 'author-work', 'book_title': '作者的原著'}]}
    content, delivery = context.tool_context(name, data, 'general')
    assert len(content) > 4000 and delivery['status'] == 'complete'
    message = ToolMessage(name=name, content=content, tool_call_id='read', additional_kwargs={'_result_full': data, '_context_delivery': delivery})
    messages = [HumanMessage(content='问题'), message, AIMessage(content='下一轮'), ToolMessage(name='probe', content='{}', tool_call_id='probe')]
    E._compact_consumed_tool_messages(messages, DeepResearchDiscipline(), agent='general')
    assert json.loads(_convert_message_to_dict(message)['content']) == data
    legacy, legacy_delivery = context.tool_context(name, data, 'nietzsche')
    assert legacy == content[:4000] and legacy_delivery is None


@pytest.mark.parametrize("name", ["analyze_argument", "paper_review"])
@pytest.mark.parametrize("size", [70, 900])
def test_fresh_and_later_main_wire_keep_the_complete_reasoning_object(monkeypatch, name, size):
    data = payload(name, size)
    captured = install(monkeypatch, name, data)
    field = "argument" if name == "analyze_argument" else "review"

    async def run():
        state = state_for(name)
        result = await E.tools_node(state)
        raw = deepcopy(result["messages"][0].additional_kwargs["_result_full"])
        assert raw[field] == data  # Actual provider JSON and scaffold are unchanged.
        state["messages"] += result["messages"]
        await E.agent_node(state)
        state["messages"] += [AIMessage(content="", tool_calls=[{"name": "probe", "args": {}, "id": "later"}]),
                              ToolMessage(content="{}", tool_call_id="later", name="probe")]
        await E.agent_node(state)
        for wire in (captured[0][0], captured[1][0]):
            assert set(wire) == {"role", "content", "tool_call_id"}
            assert json.loads(wire["content"]) == raw

    asyncio.run(run())


@pytest.mark.parametrize("reuse", ["guard", "batch", "bag"])
@pytest.mark.parametrize("name", ["analyze_argument", "paper_review"])
@pytest.mark.parametrize("size", [900, 10000])
def test_all_reuse_transport_paths_keep_the_same_complete_object(monkeypatch, name, reuse, size):
    install(monkeypatch, name, payload(name, size))
    # The two reasoning tools normally are not cacheable. Enable eligibility
    # only in this fixture to exercise every shared transport path without
    # changing production repeatability or lookup rules.
    monkeypatch.setattr(E.AR, "REUSE_SAFE_TOOLS", E.AR.REUSE_SAFE_TOOLS | {name})
    if reuse == "bag":
        monkeypatch.setattr(E.RD, "query_bag_fingerprint", lambda tool, args: "offline-bag" if tool == name else None)

    async def run():
        state = state_for(name, ("one", "two") if reuse == "batch" else ("one",))
        first = await E.tools_node(state)
        if reuse == "batch":
            messages = first["messages"]
        else:
            state["messages"] = state_for(name, ("two",))["messages"]
            second = await E.tools_node(state)
            messages = [first["messages"][0], second["messages"][0]]
        raw = messages[0].additional_kwargs["_result_full"]
        assert messages[1].additional_kwargs["_reused"] is True
        expected, delivery = context.tool_context(name, raw, "general")
        assert all(_convert_message_to_dict(m)["content"] == expected for m in messages)
        assert all(m.additional_kwargs["_context_delivery"] == delivery for m in messages)
        assert json.loads(expected) == raw if size == 900 else json.loads(expected)["context_delivery"] == "omitted"

    asyncio.run(run())


@pytest.mark.parametrize("name", ["analyze_argument", "paper_review"])
def test_oversized_context_is_explicit_complete_json_and_not_a_conclusion_only_fragment(monkeypatch, name):
    data = payload(name, 10000)
    captured = install(monkeypatch, name, data)

    async def run():
        state = state_for(name)
        result = await E.tools_node(state)
        full = result["messages"][0].additional_kwargs["_result_full"]
        state["messages"] += result["messages"]
        await E.agent_node(state)
        wire = captured[0][0]["content"]
        notice = json.loads(wire)
        assert len(wire) < 24000
        assert notice["error"] == "TOOL_CONTEXT_TOO_LARGE"
        assert notice["context_delivery"] == "omitted"
        assert notice["original_chars"] == len(json.dumps(full, ensure_ascii=False))
        field = "argument" if name == "analyze_argument" else "review"
        assert set(notice["omitted_fields"]) >= {field + "." + k for k in data}
        assert full[field] == data

    asyncio.run(run())


@pytest.mark.parametrize("name", ["analyze_argument", "paper_review"])
def test_nietzsche_retains_legacy_head_limits_and_later_compaction(monkeypatch, name):
    captured = install(monkeypatch, name, payload(name))

    async def run():
        state = state_for(name, agent="nietzsche")
        result = await E.tools_node(state)
        full = json.dumps(result["messages"][0].additional_kwargs["_result_full"], ensure_ascii=False)
        state["messages"] += result["messages"]
        await E.agent_node(state)
        assert captured[0][0]["content"] == full[:4000]
        state["messages"].append(AIMessage(content="下一轮"))
        await E.agent_node(state)
        assert "此前轮已提供完整结果" in captured[1][0]["content"]
        assert len(captured[1][0]["content"]) < 400

    asyncio.run(run())


@pytest.mark.parametrize("name", sorted(name for name, capability in TOOL_TAXONOMY.items()
    if capability.get("USES_INTERNAL_LLM") or capability.get("USER_VISIBLE_ARTIFACT")))
def test_all_existing_reasoning_and_generation_capabilities_keep_artifact_endings(name):
    raw = {"beginning": "正文。" * 2000, "ending": "FINAL_ARTIFACT_END", "objection": "LAST_OBJECTION"}
    before = deepcopy(raw)
    content, delivery = context.tool_context(name, raw, "general")
    assert json.loads(content) == raw and delivery["status"] == "complete"
    message = ToolMessage(content=content, name=name, tool_call_id="artifact",
                          additional_kwargs={"_result_full": raw, "_context_delivery": delivery})
    E._compact_consumed_tool_messages([message, AIMessage(content="下一轮")], None, agent="general")
    assert json.loads(message.content) == raw and raw == before
    legacy, metadata = context.tool_context(name, raw, "nietzsche")
    assert legacy == json.dumps(raw, ensure_ascii=False)[:4000] and metadata is None


def test_context_size_boundary_is_mechanical_and_omission_metadata_is_bounded():
    limit = context.MAX_ARTIFACT_CONTEXT_CHARS
    overhead = len(json.dumps({"text": ""}, ensure_ascii=False))
    exact = {"text": "x" * (limit - overhead)}
    content, delivery = context.tool_context("write_essay", exact, "general")
    assert len(content) == limit and json.loads(content) == exact and delivery["status"] == "complete"
    oversized = {"text": exact["text"] + "x"}
    content, delivery = context.tool_context("write_essay", oversized, "general")
    assert json.loads(content)["context_delivery"] == "omitted" and delivery["status"] == "omitted"
    many_keys = {(str(i) + "x" * 200): "v" * 300 for i in range(100)}
    notice = json.loads(context.tool_context("paper_review", many_keys, "general")[0])
    assert len(json.dumps(notice, ensure_ascii=False)) < limit
    assert notice["omitted_field_count"] == 100 and notice["omission_list_complete"] is False


def test_unprotected_retrieval_retains_legacy_budget_and_reuse_content():
    raw = {"text": "来源。" * 3000}
    for agent in ("general", "nietzsche"):
        content, metadata = context.tool_context("get_philosopher", raw, agent)
        if agent == 'general':
            assert json.loads(content) == raw and metadata['status'] == 'complete'
        else:
            assert content == json.dumps(raw, ensure_ascii=False)[:4000] and metadata is None
        reused, reuse_metadata = context.tool_context("get_philosopher", raw, agent, fallback_content="cached reference")
        if agent == 'general':
            assert json.loads(reused) == raw and reuse_metadata['status'] == 'complete'
        else:
            assert (reused, reuse_metadata) == ('cached reference', None)
