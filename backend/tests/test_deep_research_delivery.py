"""Delivery-path regressions: spend, actual execution, reading and isolation."""
import asyncio
import os
import sys
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agent_runtime as runtime
import deep_agent_tools
from deep_research import DeepDuplicateGuard, DeepResearchDiscipline, debate_action
import engine_langgraph as engine
import research_discipline as discipline_module


def research(limit=1):
    result = DeepResearchDiscipline({"PRIMARY": limit, "SCHOLARLY": limit, "MIXED": limit, "NONE": 0})
    result.declare("PRIMARY", "核验目标原文的实际语境", source_dependent=True)
    return result


def state(discipline=None, hard_total=24):
    return {"agent": "general", "guard": DeepDuplicateGuard(), "discipline": discipline,
            "budget": runtime.ToolBudget(discipline_module.DISCIPLINE_RETRIEVAL_TOOLS,
                                         {"hard_total": hard_total, "hard_retrieval": hard_total}),
            "tool_count": 0, "messages": [], "raw_tool_log": []}


def batch(monkeypatch, current, calls, functions):
    monkeypatch.setattr(engine, "get_tools", lambda _agent: [
        SimpleNamespace(name=name, func=function) for name, function in functions.items()])
    current["messages"] = [AIMessage(content="", tool_calls=[
        {"name": name, "args": args, "id": f"call-{i}"} for i, (name, args) in enumerate(calls)])]
    out = asyncio.run(engine.tools_node(current))
    current["tool_count"] = out["tool_count"]
    return out["messages"]


def result(message):
    return message.additional_kwargs["_result_full"]


def test_parallel_exact_duplicates_spend_one_soft_slot(monkeypatch):
    calls = []
    d = research(1)
    current = state(d)
    msgs = batch(monkeypatch, current,
                 [("search_books", {"query": "原文"})] * 2,
                 {"search_books": lambda **args: calls.append(args) or {"results": [{"book_id": "book", "chapter_idx": 2}]}})
    assert len(calls) == 1
    assert d.retrieval_executed == 1 and d.pending_slots == 0
    assert result(msgs[0]) == result(msgs[1])
    assert msgs[1].additional_kwargs["_reused"] is True
    assert current["budget"].total_executed == 1


def test_parallel_bag_equivalent_queries_reuse_the_first_execution(monkeypatch):
    executions = []
    d = research(2)
    current = state(d)
    msgs = batch(monkeypatch, current,
                 [("search_books", {"query": "康德 自由意志", "limit": 3}),
                  ("search_books", {"query": "自由意志 康德", "limit": 3})],
                 {"search_books": lambda **args: executions.append(args) or {"results": [{"book_id": "book", "chapter_idx": 2}]}})
    assert len(executions) == 1
    assert d.retrieval_executed == 1
    assert result(msgs[0]) == result(msgs[1])
    assert msgs[1].additional_kwargs["_reused"] is True


def test_parallel_hard_budget_is_an_actual_execution_bound(monkeypatch):
    executions = []
    async def slow(**args):
        executions.append(args)
        await asyncio.sleep(0.01)
        return {"answer": "analysis"}
    current = state(None, hard_total=1)
    msgs = batch(monkeypatch, current,
                 [("analyze_argument", {"text": str(i)}) for i in range(4)],
                 {"analyze_argument": slow})
    assert len(executions) == 1
    assert current["budget"].total_executed == 1
    assert sum("RESOURCE_CEILING_REACHED" in str(result(message).get("error", "")) for message in msgs) == 3
    assert current["tool_count"] == 1


def test_identified_reads_get_two_reserve_slots_and_duplicates_reuse(monkeypatch):
    executions = []
    d = research(1)
    d.retrieval_executed = 1
    d.record_locations("search_books", {"results": [
        {"book_id": "book", "chapter_idx": i} for i in range(3)]})
    current = state(d)
    read = lambda **args: executions.append(args) or {"text": "真实原文"}
    msgs = batch(monkeypatch, current,
                 [("get_chapter", {"book_id": "book", "chapter_idx": i}) for i in range(3)],
                 {"get_chapter": read})
    assert len(executions) == 2
    assert [result(message).get("error") for message in msgs] == [None, None, "SOFT_BUDGET_REACHED"]
    assert d.snapshot()["read_reserve_used"] == 2
    again = batch(monkeypatch, current, [("get_chapter", {"book_id": "book", "chapter_idx": 0})],
                  {"get_chapter": read})
    assert len(executions) == 2
    assert again[0].additional_kwargs["_reused"] is True


@pytest.mark.parametrize("tool, payload", [
    ("get_book_detail", {"id": "book", "chapters": [{"index": 2, "title": "学而篇"}]}),
    ("concept_trace", {"timeline": [{"book_id": "book", "chapter_idx": 2, "snippet": "实际命中"}]}),
])
def test_real_directory_and_concept_locations_authorize_completion_read(tool, payload):
    d = research(1)
    d.retrieval_executed = 1
    d.record_locations(tool, payload)
    assert d.gate_query("get_chapter", {"book_id": "book", "chapter_idx": 2}) is None


def test_reserve_cannot_reopen_closed_gap_or_read_invented_ids():
    d = research(1)
    d.retrieval_executed = 1
    d.record_locations("search_books", {"results": [{"book_id": "book", "chapter_idx": 2}]})
    assert d.gate_query("get_chapter", {"book_id": "invented", "chapter_idx": 2})["error"] == "SOFT_BUDGET_REACHED"
    d.declare(gap_filled=True)
    assert d.gate_query("get_chapter", {"book_id": "book", "chapter_idx": 2})["error"] == "EVIDENCE_GAP_FILLED_STOP"
    assert d.snapshot()["read_reserve_used"] == 0


def test_reserve_allows_next_window_of_an_identified_chapter_but_remains_bounded():
    d = research(1)
    d.retrieval_executed = 1
    d.record_locations("search_books", {"results": [{"book_id": "book", "chapter_idx": 2}]})
    for offset in (0, 2800):
        assert d.gate_query("get_chapter", {"book_id": "book", "chapter_idx": 2, "offset": offset}) is None
        d.reserve()
    assert d.gate_query("get_chapter", {"book_id": "book", "chapter_idx": 2, "offset": 5600})["error"] == "SOFT_BUDGET_REACHED"
    assert d.snapshot()["read_reserve_used"] == 2


def test_debate_start_reused_but_implicit_continue_executes(monkeypatch):
    executions = []
    current = state()
    function = lambda **args: executions.append(args) or {"debate": ["发言"]}
    start = {"topic": "自由", "speakers": "康德,尼采", "mode": "step"}
    batch(monkeypatch, current, [("philosopher_debate", start)] * 2, {"philosopher_debate": function})
    assert len(executions) == 1
    batch(monkeypatch, current, [("philosopher_debate", start)], {"philosopher_debate": function})
    assert len(executions) == 1
    for _ in range(2):
        batch(monkeypatch, current, [("philosopher_debate", {"topic": "继续"})], {"philosopher_debate": function})
    assert len(executions) == 3


def test_mentioning_end_or_continuation_in_a_real_topic_does_not_become_a_command():
    assert debate_action({"topic": "战争何时结束才算正义？"}) == "start"
    assert debate_action({"topic": "存在者为什么能够继续存在？"}) == "start"
    assert debate_action({"topic": "请继续辩论"}) == "continue"
    assert debate_action({"topic": "结束辩论"}) == "summary"


def test_general_tool_override_and_array_schema_are_isolated(monkeypatch):
    original = engine.AG.TOOLS["search_books"]["execute"]
    legacy = {tool.name: tool for tool in engine._build_tools()}
    general = {tool.name: tool for tool in engine._build_tools(general=True)}
    monkeypatch.setattr(deep_agent_tools, "_debate_with_speakers", lambda args, names: {
        "speakers": names, "debate": [f"{name}: 需要区分行动的约束与判断的自主。" for name in names]})
    assert general["philosopher_debate"].invoke({"topic": "自由", "speakers": ["康德", "尼采"]})["speakers"] == ["康德", "尼采"]
    assert legacy["philosopher_debate"].args_schema.model_json_schema()["properties"]["speakers"]["type"] == "string"
    assert engine.AG.TOOLS["search_books"]["execute"] is original


def test_undeclared_cross_channel_batch_has_three_slots_without_invented_declarations(monkeypatch):
    d = DeepResearchDiscipline()
    current = state(d)
    executed = []
    fn = lambda **args: executed.append(args) or {"results": [{"url": "https://example.org/page"}]}
    msgs = batch(monkeypatch, current, [
        ("search_books", {"query": "原文"}), ("search_scholarship", {"query": "paper"}),
        ("websearch", {"query": "website"}), ("search_books", {"query": "其他原文"})],
        {name: fn for name in ("search_books", "search_scholarship", "websearch")})
    assert len(executed) == d.retrieval_executed == 3 and d.pending_slots == 0
    assert result(msgs[-1])["error"] == "SOFT_BUDGET_REACHED"
    snap = d.snapshot()
    assert snap["active_class"] is None and snap["evidence_gap"] == "" and snap["declarations"] == []
    assert [row["channel"] for row in snap["tool_choice_admissions"]] == ["CORPUS", "SCHOLARLY", "WEB"]
    assert all(row["stage"] == "research_gate_admitted" and "executed" not in row for row in snap["tool_choice_admissions"])
    d.declare("PRIMARY", "明确核验原文", source_dependent=True)
    assert d.retrieval_executed == 3
    assert d.gate_query("search_books", {"query": "新目标"})["error"] == "SOFT_BUDGET_REACHED"
    d.declare("MIXED", "多个来源对读", source_dependent=True)
    assert d.retrieval_executed == 3 and d._soft_limit() == 6
    following = batch(monkeypatch, current, [("search_books", {"query": f"新目标{i}"}) for i in range(4)], {"search_books": fn})
    assert len(executed) == d.retrieval_executed == 6
    assert result(following[-1])["error"] == "SOFT_BUDGET_REACHED"
    assert len(d.tool_choice_admissions) == 3


@pytest.mark.parametrize("declaration, code", [
    ({"research_need": "NONE"}, "RESEARCH_NEED_NONE_NO_RETRIEVAL"),
    ({"gap_filled": True}, "EVIDENCE_GAP_FILLED_STOP"),
    ({"research_need": "PRIMARY", "evidence_gap": "", "source_dependent": False}, "RESEARCH_NEED_DECLARATION_REQUIRED"),
    ({"research_need": "BOGUS"}, "RESEARCH_NEED_DECLARATION_REQUIRED"),
])
def test_any_same_batch_declaration_attempt_precedes_tool_choice_admission(monkeypatch, declaration, code):
    d = DeepResearchDiscipline()
    executed = []
    msgs = batch(monkeypatch, state(d), [
        ("search_books", {"query": "先列出的检索"}), ("declare_research_need", declaration)],
        {"search_books": lambda **args: executed.append(args) or {"results": []}})
    assert not executed and result(msgs[0])["error"] == code
    assert d.declarations and d.tool_choice_admissions == []


@pytest.mark.parametrize("name,args", [
    ("get_chapter", {"book_id": "known", "chapter_idx": 2}),
    ("get_scholarly_source", {"source_record_id": "known"}),
    ("websearch", {"url": "https://example.org/known", "offset": 0}),
])
def test_undeclared_known_id_reads_are_admitted_without_fabricating_a_gap(monkeypatch, name, args):
    d = DeepResearchDiscipline()
    msgs = batch(monkeypatch, state(d), [(name, args)], {name: lambda **kw: {"text": "实际读取内容"}})
    assert not result(msgs[0]).get("error") and d.retrieval_executed == 1
    assert d.declarations == [] and d.active_class is None and d.evidence_gap == ""


def test_tool_choice_admission_does_not_claim_execution_or_bypass_hard_limit(monkeypatch):
    d = DeepResearchDiscipline()
    executed = []
    current = state(d, hard_total=1)
    msgs = batch(monkeypatch, current, [("search_books", {"query": str(i)}) for i in range(3)],
                 {"search_books": lambda **args: executed.append(args) or {"results": [{"book_id": "known", "chapter_idx": 2}]}})
    assert len(executed) == d.retrieval_executed == current["budget"].total_executed == 1
    assert len(d.tool_choice_admissions) == 3  # Research gate admission is not actual execution.
    assert sum(result(m).get("error") == "RESOURCE_CEILING_REACHED" for m in msgs) == 2
    assert current["tool_count"] == 1


def test_undeclared_search_to_read_and_duplicate_keep_shared_bounded_accounting(monkeypatch):
    d = DeepResearchDiscipline()
    current = state(d)
    search = lambda **args: {"results": [{"book_id": "known", "chapter_idx": 2}]}
    batch(monkeypatch, current, [("search_books", {"query": "原文"})] * 2, {"search_books": search})
    read_args = {"book_id": "known", "chapter_idx": 2}
    batch(monkeypatch, current, [("get_chapter", read_args)] * 2, {"get_chapter": lambda **args: {"text": "原文"}})
    assert d.retrieval_executed == 2 and len(d.tool_choice_admissions) == 2 and d.pending_slots == 0


def test_undeclared_empty_result_still_blocks_similar_queries_without_blocking_another_channel(monkeypatch):
    d = DeepResearchDiscipline()
    current = state(d)
    batch(monkeypatch, current, [("search_books", {"query": "历物十事原文与出处"})], {"search_books": lambda **args: {"results": []}})
    assert d.gate_query("search_books", {"query": "历物十事原文与出处考订"})["error"] == "NO_NEW_INFORMATION_LOOP"
    assert d.gate_query("websearch", {"query": "历物十事原文与出处"}) is None
    d.declare("PRIMARY", "", source_dependent=False)
    assert d.gate_query("websearch", {"query": "其他来源"})["error"] == "RESEARCH_NEED_DECLARATION_REQUIRED"


@pytest.mark.parametrize("located", [
    {"results": [{"url": "https://example.org/page"}]},
    {"mode": "read", "url": "https://example.org/page", "requested_url": "https://example.org/redirect"},
])
def test_web_url_windows_use_only_two_known_location_read_reserves(located):
    d = DeepResearchDiscipline()
    d.retrieval_executed = 3
    d.record_locations("websearch", located)
    assert d.gate_query("websearch", {"query": "ordinary search"})["error"] == "SOFT_BUDGET_REACHED"
    assert d.gate_query("websearch", {"url": "https://example.org/unknown"})["error"] == "SOFT_BUDGET_REACHED"
    first_url = located.get("requested_url") or "https://example.org/page"
    for args in ({"url": first_url, "offset": 0}, {"url": "https://example.org/page", "offset": 2800}):
        assert d.gate_query("websearch", args) is None
        d.reserve()
    assert d.gate_query("websearch", {"url": "https://example.org/page", "offset": 5600})["error"] == "SOFT_BUDGET_REACHED"
    assert len(d.read_reserve) == 2


def test_web_read_reserve_does_not_override_declared_channel_none_or_closed_gap():
    d = research(1)
    d.retrieval_executed = 1
    d.record_locations("websearch", {"results": [{"url": "https://example.org/page"}]})
    args = {"url": "https://example.org/page"}
    assert d.gate_query("websearch", args)["error"] == "CHANNEL_MISMATCH"
    d.declare("NONE")
    assert d.gate_query("websearch", args)["error"] == "RESEARCH_NEED_NONE_NO_RETRIEVAL"
    d.declare(gap_filled=True)
    assert d.gate_query("websearch", args)["error"] == "EVIDENCE_GAP_FILLED_STOP"
    assert d.read_reserve == []
