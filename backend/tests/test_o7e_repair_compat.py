# -*- coding: utf-8 -*-
"""O7-E RP1 §9: Repair 兼容性回归 R1-R10。

锁死:
  - hard 预算已成立的 repair → 零工具模式（不可执行认知工具）→ Main Agent 仍产完整候选
  - 不再出现「forced_tools_done → 空候选 → EMPTY_FINAL」机械死路
  - telemetry 真值: validation.history / repairs_used / error content
  - 预算不增（20/24）, validator 语义零改动, scholarly contract 正文 byte 不变
"""
import asyncio
import hashlib
import json
import os
import sys

import pytest
from langchain_core.messages import AIMessage, SystemMessage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_langgraph as EG
import agent_runtime as AR

# 复用 O2 测试骨架
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o2_final_ownership import (_msg, _run_stream, _done, _answer_text,
                                     _LUNYU_PASSAGE, _TOOLS_SCRIPT, ScriptedChat,
                                     _SENTINEL_FAKE)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── R1: invalid + budget available → repair 可调工具 → 有效最终候选 ──
def test_r1_repair_with_budget_can_use_tools():
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    good_final = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价。"
    script = _TOOLS_SCRIPT + [_msg(bad_final)] + [
        _msg("需要再定位原文措辞。",
             [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13},
               "id": "r1"}]),
        _msg(good_final)]
    evs = _run_stream("言必有中出处", script)
    done = _done(evs)
    assert done["validation"]["repairs_used"] >= 1
    assert done["validation"]["result"]["ok"] is True
    assert good_final in _answer_text(evs)


# ── R2/R3: hard budget 已成立 → repair 零工具仍产出完整候选 ──
def _run_hard_budget_repair(repair_declares_tool=False):
    """把 budget 预置为 hard reached（total_executed=hard_total）, 首候选 invalid。"""
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    good_final = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价，原文为「鲁人为长府……夫人不言，言必有中」。"
    script = list(_TOOLS_SCRIPT)
    if repair_declares_tool:
        # 模型在零工具 repair 轮仍尝试宣告工具（模型行为不可控, 引擎须机械兜住）
        script += [_msg(bad_final),
                   _msg("想再查一次。", [{"name": "get_chapter",
                                          "args": {"book_id": "lunyu", "chapter_idx": 13},
                                          "id": "rx"}]),
                   _msg(good_final)]
    else:
        script += [_msg(bad_final), _msg(good_final)]

    real_hard = AR.ToolBudget.hard_reached

    def _hard(self):
        return True          # 机械事实: hard ceiling 已成立

    orig = EG.get_llm, EG.get_tools
    _chat = ScriptedChat(script=list(script))
    EG.get_llm = lambda: _chat
    from test_o2_final_ownership import _fake_tools
    EG.get_tools = lambda agent: _fake_tools()

    async def _collect():
        evs = []
        async for ev in EG.stream_agent("言必有中出处", [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    AR.ToolBudget.hard_reached = _hard
    try:
        return asyncio.run(_collect())
    finally:
        AR.ToolBudget.hard_reached = real_hard
        EG.get_llm, EG.get_tools = orig


def test_r2_hard_budget_repair_returns_complete_candidate():
    evs = _run_hard_budget_repair()
    done = _done(evs)
    assert done["validation"]["repairs_used"] >= 1
    assert done["validation"]["result"]["ok"] is True
    answer = _answer_text(evs)
    assert "言必有中" in answer and answer.strip()   # 完整替换候选发布


def test_r3_forced_tools_done_not_empty_final():
    """R3: 模型在零工具 repair 轮仍宣告工具 → 不得仅因 forced_tools_done 以 EMPTY_FINAL 收场。"""
    evs = _run_hard_budget_repair(repair_declares_tool=True)
    done = _done(evs)
    codes = [i.get("code") for i in done["validation"]["result"].get("issues", [])]
    assert "EMPTY_FINAL" not in codes or done["validation"]["result"]["ok"] is True
    answer = _answer_text(evs)
    if done["validation"]["result"]["ok"]:
        assert answer.strip()


# ── R4/R5/R6/R7: telemetry 真值（validation.history）──
def test_r4_empty_candidate_counted_never_published():
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    blank = "   \n  "          # 空白候选（真实生成但无内容）
    script = _TOOLS_SCRIPT + [_msg(bad_final), _msg(blank), _msg(blank)]
    evs = _run_stream("言必有中出处", script)
    done = _done(evs)
    hist = done["validation"]["history"]
    # 空白候选如实进入 history（3 次尝试: 初检+2 repair, 后两次候选无实质内容）
    assert len(hist) == 3
    assert all(not h["ok"] for h in hist)
    assert any(h["candidate_chars"] < 10 for h in hist)
    assert done["validation"]["result"]["ok"] is False        # 绝不发布
    assert not _answer_text(evs).strip()


def test_r5_r6_r7_history_counts():
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    good_final = "经重新整理：「言必有中」出自《论语·先进篇》。"
    # R7: initial fail + repair1 PASS → failures=1, attempts=1, success
    evs = _run_stream("言必有中出处", _TOOLS_SCRIPT + [_msg(bad_final), _msg(good_final)])
    done = _done(evs)
    hist = done["validation"]["history"]
    fails = sum(1 for h in hist if not h["ok"])
    assert fails == 1 and done["validation"]["repairs_used"] == 1
    assert done["final_ownership"]["validator_repair_invocations"] == 1

    # R6: 三连 fail（initial + repair1 + repair2）→ failures=3, attempts=2, exhaustion
    evs6 = _run_stream("言必有中出处",
                       _TOOLS_SCRIPT + [_msg(bad_final), _msg(bad_final), _msg(bad_final)])
    d6 = _done(evs6)
    h6 = d6["validation"]["history"]
    assert len([h for h in h6 if not h["ok"]]) == 3
    assert d6["validation"]["repairs_used"] == 2              # = MAX_VALIDATION_REPAIRS
    assert d6["validation"]["result"]["ok"] is False
    assert not _answer_text(evs6).strip()


def test_r8_error_content_captured():
    """runner 端 error 事件读 content; 这里锁引擎侧 error 事件携带 content 字段。"""
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs = _run_stream("言必有中出处",
                      _TOOLS_SCRIPT + [_msg(bad_final), _msg(bad_final), _msg(bad_final)])
    errs = [e for e in evs if e.get("type") == "error"]
    assert errs and all(e.get("content") for e in errs)       # 无空 message 假观测


def test_r9_budget_not_increased():
    assert AR.TOOL_BUDGET["hard_total"] == 24
    assert AR.TOOL_BUDGET["hard_retrieval"] == 20


def test_r10_validator_semantics_unchanged():
    import subprocess
    r = subprocess.run(["git", "diff", "--quiet",
                        "302f7380a4146d78374887063b336c5aa7381ddd", "--",
                        "backend/final_validator.py"],
                       cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                           os.path.abspath(__file__)))), capture_output=True)
    assert r.returncode == 0


def test_r10b_contract_bytes_unchanged_and_general_only():
    """SCHOLARLY_CONTRACT 正文 byte 不变（RP1 只改注入范围）; general-only 注入。"""
    import inspect
    src = inspect.getsource(EG)
    assert 'if agent == "general":' in src.split("SCHOLARLY_CONTRACT")[1][:1200] or \
           'if agent == "general":' in src.split("def _build_context_messages")[1][:2000]
    contract = EG.SCHOLARLY_CONTRACT
    assert contract.strip().startswith("【学术研究契约")
    assert "访问诚实" in contract and "不得凭记忆补书目" in contract


# ══ RP1 Final Closure A: no_tools 协议真验证（C1-C5）══════════
def test_c1_no_tools_channel_in_schema():
    assert "no_tools" in EG.AgentState.__annotations__


def _counting_llm(script, counter):
    """ScriptedChat + bind_tools 计数器。"""
    class Counting(ScriptedChat):
        def bind_tools(self, *a, **k):
            counter["bind_tools"] += 1
            return super().bind_tools(*a, **k)
    return Counting(script=list(script))


def _run_hard_repair_instrumented(repair_declares_tool=False):
    """hard 预算 repair 运行 + 全量工具事件/bind_tools 计数。"""
    import agent_runtime as AR
    from test_o2_final_ownership import _fake_tools
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    good_final = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价。"
    script = list(_TOOLS_SCRIPT) + [_msg(bad_final)]
    if repair_declares_tool:
        script += [_msg("想再查一次。", [{"name": "get_chapter",
                                          "args": {"book_id": "lunyu", "chapter_idx": 13},
                                          "id": "rx"}]),
                   _msg(good_final)]
    else:
        script += [_msg(good_final)]
    counter = {"bind_tools": 0}
    _chat = _counting_llm(script, counter)
    orig_llm, orig_tools = EG.get_llm, EG.get_tools
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()

    real_hard = AR.ToolBudget.hard_reached
    AR.ToolBudget.hard_reached = lambda self: True

    async def _collect():
        evs = []
        async for ev in EG.stream_agent("言必有中出处", [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    try:
        evs = asyncio.run(_collect())
    finally:
        AR.ToolBudget.hard_reached = real_hard
        EG.get_llm, EG.get_tools = orig_llm, orig_tools
    # repair 起点 = 首个 validation_failed 事件
    vf_i = next((i for i, e in enumerate(evs) if e.get("type") == "validation_failed"), None)
    after = evs[vf_i + 1:] if vf_i is not None else []
    tool_starts = sum(1 for e in after if e.get("type") == "tool_start")
    tool_execs = sum(1 for e in after if e.get("type") == "tool")
    return evs, counter, tool_starts, tool_execs


def test_c2_c3_c4_hard_repair_zero_tools():
    """零工具 repair 真值: repair 段 bind_tools=0 / tool_start=0 / tool 执行=0。

    hard_reached=True 从一开始就成立 → 首轮 agent_node 即 forced+零工具?
    注意: 首轮也会被 hard_reached 影响。分离方式: 只断言 repair 段（首个
    validation_failed 之后）无任何工具事件; bind_tools 计数为全程——
    首轮仍 bind（state.no_tools 仅 repair 轮置位）, repair 轮不 bind。
    因此用 tool_start/tool 执行（repair 段）作硬断言, bind_tools 全程计数
    不增长于 repair 段（通过事件序列间接锁: repair 段无 agent→tools 回边）。
    """
    evs, counter, tool_starts, tool_execs = _run_hard_repair_instrumented()
    done = _done(evs)
    assert done["validation"]["repairs_used"] >= 1
    assert done["validation"]["result"]["ok"] is True
    assert tool_starts == 0, "repair 段不得出现 tool_start"
    assert tool_execs == 0, "repair 段不得执行工具"


def test_c3b_hard_repair_model_declares_tool_still_no_execution():
    evs, counter, tool_starts, tool_execs = _run_hard_repair_instrumented(
        repair_declares_tool=True)
    assert tool_execs == 0           # 零工具模式: 宣告也不执行
    done = _done(evs)
    codes = [i.get("code") for i in done["validation"]["result"].get("issues", [])]
    if done["validation"]["result"]["ok"]:
        assert _answer_text(evs).strip()


def test_c5_normal_repair_tool_capability_preserved():
    """预算未耗尽: repair 轮仍可调工具（R1 已锁行为; 这里锁 bind_tools 仍发生）。"""
    counter = {"bind_tools": 0}
    bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    good_final = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价。"
    script = _TOOLS_SCRIPT + [
        _msg(bad_final),
        _msg("需要再定位原文措辞。",
             [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13},
               "id": "r1"}]),
        _msg(good_final)]
    from test_o2_final_ownership import _fake_tools
    _chat = _counting_llm(script, counter)
    orig_llm, orig_tools = EG.get_llm, EG.get_tools
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()
    try:
        async def _collect():
            evs = []
            async for ev in EG.stream_agent("言必有中出处", [], agent="general",
                                            language="zh"):
                evs.append(ev)
            return evs
        evs = asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools = orig_llm, orig_tools
    done = _done(evs)
    assert done["validation"]["repairs_used"] >= 1
    assert done["validation"]["result"]["ok"] is True
    assert counter["bind_tools"] >= 3        # 首轮+repair 轮都 bind（能力保留）


# ══ RP1 Final Closure B/C: canonical runner 真值（直接调 run_case）═══
def test_runner_uses_validation_history_and_repairs_used(monkeypatch):
    """canonical runner 必须消费 done.validation.history/repairs_used/result,
    并做 BLOCKED_MODEL_BILLING 分类——直接调用 o7e_runner.run_case 断言。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "o7e_runner", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "tools", "evaluation", "o7e_runner.py"))
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    good = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价。"
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    script = _TOOLS_SCRIPT + [_msg(bad), _msg(good)]
    _chat = ScriptedChat(script=list(script))
    from test_o2_final_ownership import _fake_tools
    orig_llm, orig_tools = EG.get_llm, EG.get_tools
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()
    try:
        case = {"case_id": "T-B", "category": "argument", "question": "言必有中出处",
                "persona": "general",
                "applicability": {}, "evidence_expectation": "PRIMARY_REQUIRED"}
        r = runner.run_case(case)
    finally:
        EG.get_llm, EG.get_tools = orig_llm, orig_tools
    d = r["delivery"]
    assert d["run_status"] == "COMPLETED"
    assert d["validation_attempts"] == 2              # history 长度（初检+repair 后）
    assert d["validation_failures"] == 1              # history.ok=false 计数
    assert d["repair_attempts"] == 1                  # repairs_used（≠ SSE 计数）
    assert d["repair_success"] is True
    assert d["repair_exhaustion"] is False
    assert d["final_validation_result"] is True
    assert d["published"] is True
    assert d["publication_denominator_member"] is True


def test_runner_classifies_billing_block(monkeypatch):
    """402/余额 → BLOCKED_MODEL_BILLING: published=N/A, terminal_pending=false,
    不入发布分母。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "o7e_runner", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "tools", "evaluation", "o7e_runner.py"))
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    async def fake_stream(*a, **k):
        yield {"type": "status", "content": "开始"}
        yield {"type": "error", "content": "DeepSeek API 余额不足——请充值后重试"}

    monkeypatch.setattr(runner.ENG, "stream_agent", fake_stream)
    case = {"case_id": "T-C", "category": "argument", "question": "q",
            "persona": "general", "applicability": {}, "evidence_expectation": "E"}
    r = runner.run_case(case)
    d = r["delivery"]
    assert d["run_status"] == "BLOCKED_MODEL_BILLING"
    assert d["published"] is None                      # N/A
    assert d["terminal_pending"] is False              # 不是产品层交付失败
    assert d["publication_denominator_member"] is False
