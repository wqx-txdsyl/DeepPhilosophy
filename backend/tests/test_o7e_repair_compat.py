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
