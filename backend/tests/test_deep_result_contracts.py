"""Reject actual empty fallbacks without judging useful short content or retrieval."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_context import current_memory_key
from deep_result_contracts import CHECKED_TOOLS, validate_general_result
from deep_stateful import execute_stateful
import deep_agent_tools as deep
from routes import agent_core as core, agent_tools_eval as evaluate, agent_tools_memory as memory


CASES = [
    ("compare_views", evaluate._exec_compare, {"a": "康德", "b": "休谟"}),
    ("advisor_council", evaluate._exec_council, {"question": "要不要坚持自己的选择"}),
    ("agent_council", evaluate._exec_agent_council, {"topic": "选择与责任"}),
    ("dialectic", evaluate._exec_dialectic, {"topic": "自由"}),
    ("confrontation", evaluate._exec_confrontation, {"a": "康德", "b": "休谟", "topic": "因果性"}),
    ("socratic_tutor", evaluate._exec_socratic, {"topic": "自由"}),
    ("thought_experiment", memory._exec_thought_exp, {"base": "一个人只能选择一个目标"}),
    ("philosopher_debate", deep.philosopher_debate, {"topic": "自由", "speakers": "康德,休谟", "mode": "step"}),
    ("write_essay", memory._exec_write_essay, {"topic": "自由的意义"}),
]


@pytest.fixture
def empty_provider(monkeypatch, tmp_path):
    empty = lambda *args, **kwargs: {"choices": [{"finish_reason": "length", "message": {"content": ""}}]}
    monkeypatch.setattr(evaluate, "llm_chat", empty)
    monkeypatch.setattr(memory, "llm_chat", empty)
    monkeypatch.setattr(memory, "_philosopher_profile", lambda name: None)
    monkeypatch.setitem(evaluate.TOOLS, "search_books", {"execute": lambda args: {"results": []}})
    monkeypatch.setitem(evaluate.TOOLS, "websearch", {"execute": lambda args: {"results": []}})
    monkeypatch.setattr(core, "_mem_all", {})
    monkeypatch.setattr(core, "MEM_FILE", tmp_path / "memory.json")


@pytest.mark.parametrize("name,execute,args", CASES)
def test_actual_empty_provider_fallbacks_are_errors_in_general_gate_only(name, execute, args, empty_provider):
    raw = execute(args)
    assert not raw.get("error")  # Reproduces the unchanged shared-tool contract.
    before = deepcopy(raw)
    checked = validate_general_result(name, args, raw)
    assert checked["error"] == "INCOMPLETE_TOOL_RESULT" and checked["tool"] == name
    assert checked["missing_fields"] and "confidence" not in checked
    assert raw == before


VALID = [
    ("compare_views", {"comparison_axes": [{"axis": "自由", "side_a": "理由", "side_b": "习惯"}], "citations": []}),
    ("compare_views", {"comparison_axes": [], "side_a_claims": [{"claim": "甲"}], "side_b_claims": [{"claim": "乙"}]}),
    ("compare_views", {"comparison_axes": [], "strongest_divergence": "两者对责任的判断条件不同。"}),
    ("advisor_council", {"council": {"perspectives": [{"advisor": "斯多葛", "advice": "失败不等于失去全部行动余地。"}]}}),
    ("agent_council", {"council": {"deep": "是。", "nietzsche": "否。", "synthesis": "仍有分歧。"}}),
    ("agent_council", {"council": {"deep": "提示“（深哲发言失败: 网络中断）”并不是一种哲学立场。",
                                   "nietzsche": "失败可以被重新解释。", "synthesis": "须区分两种失败。"}}),
    ("dialectic", {"movement": {"internal_tension": "承认失败也是继续尝试的条件。"}}),
    ("confrontation", {"stance_a": {"text": "是。"}, "stance_b": {"text": "否。"}, "citations": [], "exchanges": []}),
    ("socratic_tutor", {"next_question": "为什么？"}),
    ("socratic_tutor", {"next_question": "你说这话时, 心里把它当作什么?", "diagnosed_assumption": "用户将一个判断当成事实。", "question_purpose": "暴露隐含前提"}),
    ("thought_experiment", {"setting": "甲同意了。", "stance_projections": [], "revealed_problem": "同意是否出于自愿？"}),
    ("thought_experiment", {"setting": "甲同意了。", "stance_projections": [{"stance": "自主", "projection": "须能拒绝。"}], "revealed_problem": ""}),
    ("philosopher_debate", {"debate": ["甲: 是。", "乙：否。"]}),
    ("philosopher_debate", {"debate_summary": "分歧尚存。"}),
    ("write_essay", {"essay": "仍可再试。", "citations": []}),
    ("write_essay", {"essay": "屏幕显示“（生成失败，请重试）”，他决定继续写下去。"}),
]


@pytest.mark.parametrize("name,result", VALID)
def test_real_short_artifacts_and_failure_related_topics_are_returned_unchanged(name, result):
    before = deepcopy(result)
    assert validate_general_result(name, {}, result) is result
    assert result == before


@pytest.mark.parametrize("name,result", [
    ("compare_views", {"comparison_axes": [{"axis": "比较", "side_a": "", "side_b": ""}]}),
    ("advisor_council", {"council": {"perspectives": [{"advisor": "哲人", "advice": " "}]}}),
    ("dialectic", {"movement": {"internal_tension": "辩证运动生成失败——请主 Agent 直接自行剖析", "residual_tension": ""}}),
    ("confrontation", {"stance_a": {"text": "有立场。"}, "stance_b": {"text": ""}}),
    ("socratic_tutor", {"next_question": " "}),
    ("thought_experiment", {"setting": "照抄设定", "stance_projections": [], "revealed_problem": ""}),
    ("philosopher_debate", {"debate": ["甲: 有立场。", "乙: "]}),
    ("philosopher_debate", {"debate": ["甲： ", "乙： "]}),
    ("philosopher_debate", {"debate_summary": "", "map_text": "图不等于总结"}),
    ("write_essay", {"essay": "（修改失败，请重试）"}),
])
def test_partial_empty_fields_do_not_become_success_via_metadata(name, result):
    result.update(confidence=1.0, summary="已完成", note="正文见载荷")
    assert validate_general_result(name, {}, result)["error"] == "INCOMPLETE_TOOL_RESULT"


@pytest.mark.parametrize("name", sorted(CHECKED_TOOLS))
@pytest.mark.parametrize("result", [None, [], "done", {}, {"next_question": [], "council": [], "movement": []}])
def test_malformed_payloads_are_reported_without_exceptions(name, result):
    assert validate_general_result(name, {}, result)["error"] == "INCOMPLETE_TOOL_RESULT"


def test_empty_retrieval_and_existing_errors_pass_through_without_reclassification():
    for name in ("search_books", "websearch", "get_book_detail", "concept_trace"):
        result = {"results": [], "error": None}
        assert validate_general_result(name, {}, result) is result
    for name in CHECKED_TOOLS:
        for result in ({"error": "Provider unavailable"}, {"accepted": False, "reason": "blocked"}):
            assert validate_general_result(name, {}, result) is result


@pytest.mark.parametrize("provider_mode", ["exception", "empty"])
def test_actual_agent_council_all_failures_are_errors_only_in_general_registry(monkeypatch, provider_mode):
    import engine_langgraph as engine
    import deep_streaming as streaming

    def provider(*args, **kwargs):
        if provider_mode == "exception":
            raise RuntimeError("offline provider unavailable")
        return {"choices": [{"message": {"content": ""}}]}

    monkeypatch.setattr(evaluate, "llm_chat", provider)
    monkeypatch.setitem(evaluate.TOOLS, "search_books", {
        **evaluate.TOOLS["search_books"], "execute": lambda args: {"results": []}})
    general = next(tool for tool in engine._build_tools(general=True) if tool.name == "agent_council")
    legacy = next(tool for tool in engine._build_tools(general=False) if tool.name == "agent_council")
    checked = general.invoke({"topic": "选择与责任"})
    raw = legacy.invoke({"topic": "选择与责任"})
    assert not raw.get("error")  # Shared/persona registration remains unchanged.
    assert checked["error"] == "INCOMPLETE_TOOL_RESULT"
    assert checked["partial"] is False
    assert set(checked["missing_fields"]) == {"council.deep", "council.nietzsche", "council.synthesis"}
    assert streaming.tool_status(checked) == "error"
    assert checked["council"] == raw["council"]


@pytest.mark.parametrize("failed_member", ["deep", "nietzsche", "synthesis"])
def test_actual_partial_agent_council_preserves_successful_members_and_explicit_failure(monkeypatch, failed_member):
    import engine_langgraph as engine
    import deep_streaming as streaming

    def provider(messages, **kwargs):
        if len(messages) == 1:
            member = "synthesis"
        elif "待检验的分析立场" in messages[-1]["content"]:
            member = "deep"
        else:
            member = "nietzsche"
        if member == failed_member:
            raise RuntimeError("offline member unavailable")
        return {"choices": [{"message": {"content": member + "：已完成的实际发言。"}}]}

    monkeypatch.setattr(evaluate, "llm_chat", provider)
    monkeypatch.setitem(evaluate.TOOLS, "search_books", {
        **evaluate.TOOLS["search_books"], "execute": lambda args: {"results": []}})
    execute = engine._general_executor("agent_council", evaluate._exec_agent_council)
    checked = execute(topic="选择与责任")
    assert checked["error"] == "INCOMPLETE_TOOL_RESULT" and checked["partial"] is True
    assert checked["missing_fields"] == ["council." + failed_member]
    assert streaming.tool_status(checked) == "error"
    assert "失败" in checked["council"][failed_member]
    for member in ("deep", "nietzsche", "synthesis"):
        if member != failed_member:
            assert checked["council"][member] == member + "：已完成的实际发言。"
    assert validate_general_result("agent_council", {}, checked) is checked


STATEFUL_CASES = [case for case in CASES if case[0] in {
    "socratic_tutor", "thought_experiment", "philosopher_debate", "write_essay",
}] + [
    ("philosopher_debate", deep.philosopher_debate, {"topic": "总结", "action": "summary"}),
    ("write_essay", memory._exec_write_essay, {"topic": "自由的意义", "modify": "更简短"}),
]


@pytest.mark.parametrize("name,execute,args", STATEFUL_CASES)
def test_actual_failed_stateful_artifact_rolls_back_inside_transaction(name, execute, args, empty_provider):
    key = "u:general:artifact-rollback"
    baseline = {
        "essays": {"自由的意义": {"text": "保留已完成的作文。", "genre": "议论文", "word_count": 800}},
        "debate": {"topic": "旧论题", "speakers": ["康德", "休谟"], "mode": "step", "rounds_done": 1, "history": ["旧发言"]},
        "socratic": {"topic": "自由", "round": 1, "asked": ["先前的问题？"], "last_reply": ""},
        "experiment": {"base": "先前设定", "text": "先前推演"}, "image": None,
    }
    core._mem_all[key] = deepcopy(baseline)
    core._save_agent_memory()
    persisted = core.MEM_FILE.read_text()
    # Same placement as the general registry's execute wrapper: validation must
    # happen before execute_stateful sees and commits the returned artifact.
    def checked(**kwargs):
        return validate_general_result(name, kwargs, execute(kwargs))
    async def run():
        token = current_memory_key.set(key)
        try:
            return await execute_stateful(checked, args, 2)
        finally:
            current_memory_key.reset(token)
    result = asyncio.run(run())
    assert result["error"] == "INCOMPLETE_TOOL_RESULT"
    assert core._mem_all[key] == baseline
    assert core.MEM_FILE.read_text() == persisted
    assert json.loads(persisted)[key] == baseline
