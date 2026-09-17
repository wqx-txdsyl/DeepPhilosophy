import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deep_reasoning_tools as tools
import engine_langgraph as engine
from routes import agent_tools_eval as legacy


def response(content, finish="stop"):
    return {"choices": [{"finish_reason": finish, "message": {"content": content}}]}


def test_truncated_or_empty_model_output_cannot_be_success(monkeypatch):
    for value in (response("", "length"), response(""), response("{}")):
        monkeypatch.setattr(tools, "llm_chat", lambda *a, **kw: value)
        result = tools.analyze_argument({"text": "所有同意都是自愿的，所以同意就足够。"})
        assert result["error"] and "confidence" not in result


def test_argument_checks_use_visible_budget_and_preserve_input_and_counterexample(monkeypatch):
    data = {"conclusion": "同意就足够", "premises": [{"premise": "所有同意都是自愿的", "kind": "explicit"}],
            "hidden_assumptions": [], "fallacies": [], "strongest_reply": "需要证明同意是自由作出的",
            "strengthening": [], "question_fidelity": "原问题被保留",
            "weakest_point": "前提过强", "counterexample": {"scenario": "受威胁时同意", "premises_still_hold": "原前提不成立，因此这是针对前提的质疑而非有效反例", "conclusion_fails": "不能由同意推出自愿"}}
    calls = []
    def invoke(messages, **kwargs):
        calls.append((messages, kwargs))
        return response(json.dumps(data, ensure_ascii=False))
    monkeypatch.setattr(tools, "llm_chat", invoke)
    result = tools.analyze_argument({"text": "所有同意都是自愿的，所以同意就足够。", "question": "这句话成立吗？"})
    assert result["argument"] == data and result["kind"] == "argument_structure"
    assert calls[0][1]["thinking"] is True and calls[0][1]["max_tokens"] == 16384
    assert calls[0][1]["reasoning_effort"] == "low"
    assert "这句话成立吗" in calls[0][0][1]["content"]
    assert "仍须检查" in result["summary"]  # Structural validity does not claim philosophical truth.
    assert "confidence" not in result and result["validation_scope"] == "structure_only"


def test_incomplete_counterexample_is_rejected(monkeypatch):
    monkeypatch.setattr(tools, "llm_chat", lambda *a, **kw: response(json.dumps({
        "conclusion": "某个结论", "premises": [], "weakest_point": "缺理由", "counterexample": {"scenario": "故事"},
        "hidden_assumptions": [], "fallacies": [], "strongest_reply": "应给出理由", "strengthening": [], "question_fidelity": ""})))
    assert tools.analyze_argument({"text": "某个结论"})["error"] == "INVALID_COUNTEREXAMPLE"


def test_paper_review_empty_fallback_is_not_success(monkeypatch):
    monkeypatch.setattr(tools, "llm_chat", lambda *a, **kw: response("", "length"))
    monkeypatch.setattr(legacy, "llm_chat", lambda *a, **kw: response("", "length"))
    assert tools.paper_review({"text": "待评审的短文"})["error"] == "INCOMPLETE_PAPER_REVIEW"
    # The shared legacy function still has its original result for persona callers.
    assert legacy._exec_paper_review({"text": "待评审的短文"})["kind"] == "structured_review"


def test_malformed_json_and_partial_thesis_are_not_repaired_into_success(monkeypatch):
    for value in ('{"conclusion":"结论","premises":[],"counterexample":null,"weakest_point":"缺口"',
                  '{"thesis":{"statement":"只有开头论点"}'):
        monkeypatch.setattr(tools, "llm_chat", lambda *a, **kw: response(value))
        assert tools.analyze_argument({"text": "一个论证"})["error"]
        assert tools.paper_review({"text": "一个论证"})["error"]
    monkeypatch.setattr(tools, "llm_chat", lambda *a, **kw: response('{"thesis":{"statement":"只有论点"}}'))
    assert tools.paper_review({"text": "一个论证"})["error"] == "INVALID_PAPER_REVIEW"


def test_general_only_override_and_zero_argument_tool_schema():
    general = {tool.name: tool for tool in engine._build_tools(general=True)}
    assert "execute" not in general["phti_test"].args
    assert "question" in general["analyze_argument"].args
    assert "question" not in {tool.name: tool for tool in engine.TOOLS_LG}["analyze_argument"].args


def test_real_request_tail_and_long_argument_reach_analysis_without_head_truncation(monkeypatch):
    from deep_context import current_request_question
    # The UI places the actual follow-up after an attachment or selected answer.
    question = "【附件】\n" + "这是一份供分析的材料。" * 1500 + "\n本次追问：请检查文末结论是否偷换了主体。"
    argument = "前提说明。" * 1500 + "\n最后结论：所有义务都只由个人偏好决定。"
    calls = []
    data = {"conclusion": "候选结论", "premises": [], "hidden_assumptions": [], "fallacies": [],
            "counterexample": None, "strongest_reply": "需要解释桥梁前提", "weakest_point": "缺理由",
            "strengthening": [], "question_fidelity": "已保留当前追问"}
    def invoke(messages, **kwargs):
        calls.append(messages)
        return response(json.dumps(data, ensure_ascii=False))
    monkeypatch.setattr(tools, "llm_chat", invoke)
    token = current_request_question.set(question)
    try:
        result = tools.analyze_argument({"text": argument, "question": "调用者改写的问题"})
    finally:
        current_request_question.reset(token)
    assert question in calls[0][1]["content"] and argument in calls[0][1]["content"]
    assert "调用者改写的问题" not in calls[0][1]["content"]
    assert result["question_context_truncated"] is False


def test_oversized_question_preserves_both_ends_and_discloses_missing_middle():
    question = "原问题开头" + "中间材料" * 12000 + "本次追问在末尾"
    visible, truncated = tools._question_context(question)
    assert truncated and visible.startswith("原问题开头") and visible.endswith("本次追问在末尾")
    assert "不能据此认定已核对全部材料" in visible
    assert len(visible) < tools.QUESTION_CONTEXT_CHARS + 100


def test_over_limit_argument_does_not_review_a_different_truncated_claim(monkeypatch):
    monkeypatch.setattr(tools, "llm_chat", lambda *_a, **_k: pytest.fail("Must not analyze an incomplete argument"))
    text = "前提" * 11000 + "结论在最后。"
    result = tools.analyze_argument({"text": text})
    assert result["error"] == "ARGUMENT_INPUT_TOO_LONG"
    assert result["input_chars"] == len(text)
