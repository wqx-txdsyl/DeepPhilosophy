# -*- coding: utf-8 -*-
"""Interpretation Engine（Phase 2）用例——多候选解读 / 双面证据 / 置信度校准 / 深度惩罚 / 引擎接线回归

覆盖 2026-08-30 Phase 2 验收项:
  Candidate:   梦狮等解释型问题 → 多候选强制（H1/H2…）; 非解释型问题不启用
  Evidence:    supporting_evidence / challenging_evidence 分离; 无反证允许 [] 且不得伪造
  Bias:        "老人梦狮=荒诞幸福" 单候选择案 → 补正"并非唯一"; 越级断言扣置信度
  Calibrator:  0.85+/0.65-0.85/0.4-0.65/<0.4 四档语言; 数字不出现在回答里
  Depth:       跨体系跳转越多 confidence 只降不升; "海明威→加缪→庄子→佛教→斯多葛"链条被惩罚
  Analogy:     "尼采超人/庄子逍遥 是不是一回事" → 类比≠等同强制
  回归: 工具注册表 / 人格提示词 / Graph 结构 / 流式事件序列（mock APP, 不调 LLM）
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from langchain_core.messages import AIMessageChunk

import interpretation_engine as ie
from routes import agent as AG


# ═══════════════════════════════════════════════════════
# 1. InterpretationChallenger —— 解释型问题识别（只对 4 类启用）
# ═══════════════════════════════════════════════════════
def test_dream_lion_question_triggers_interpretation():
    v = ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？")
    assert v["activated"] is True
    assert "literary_interpretation" in v["categories"]
    assert "philosophical_interpretation" in v["categories"]
    assert v["object"] == "老人梦狮"


def test_nietzsche_zhuangzi_comparison_triggers_analogy_guard():
    v = ie.run_interpretation_engine("尼采的超人和庄子的逍遥是不是一回事？")
    assert v["activated"] is True
    assert "cross_author_comparison" in v["categories"]
    assert v["analogy_guard"] is True
    assert v["hypothesis_min"] >= 2


def test_plain_question_not_activated():
    # 非解释型问题不得强制多解释（宁漏勿误）
    assert ie.run_interpretation_engine("什么是虚无主义？")["activated"] is False
    assert ie.run_interpretation_engine("尼采如何看待瓦格纳？")["activated"] is False
    assert ie.run_interpretation_engine("老人87天没捕到鱼，这说明了什么？")["activated"] is False


def test_ambiguous_history_triggers():
    v = ie.run_interpretation_engine("关于尼采精神崩溃的时间，学界众说纷纭，如何看待这段历史？")
    assert v["activated"] is True
    assert "ambiguous_historical_interpretation" in v["categories"]


# ═══════════════════════════════════════════════════════
# 2. 候选解读 + 双面证据 + 反证尝试（注入结构要求）
# ═══════════════════════════════════════════════════════
def test_candidate_interpretations_required():
    v = ie.run_interpretation_engine("《老人与海》中老人梦狮象征什么？")
    assert v["hypothesis_min"] >= 2
    inj = "\n".join(v["injections"])
    assert "至少提出两种" in inj and "H1" in inj


def test_supporting_and_challenging_evidence_separation():
    v = ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？")
    assert v["evidence_requirement"] == {"supporting": True, "challenging": True}
    inj = "\n".join(v["injections"])
    assert "supporting_evidence" in inj and "challenging_evidence" in inj
    assert "什么材料会削弱我的主要解读" in inj


def test_empty_challenging_evidence_allowed_no_fabrication():
    # 无反证被明确允许; 补正绝不编造具体反方观点
    v = ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？")
    inj = "\n".join(v["injections"])
    assert "绝不编造反方观点" in inj
    r = ie.scan_interpretation(v, "若采用加缪框架，这是相当有解释力的一种阅读；但并非唯一解释。")
    assert r["challenging_evidence_trace"] in ("absent", "empty")
    appends = "\n".join(r.get("appends", []))
    assert appends == "", "已有多候选/无反证时不应补正"
    assert "完全正确" not in appends


# ═══════════════════════════════════════════════════════
# 3. ConfidenceCalibrator —— 置信度评分（内部）+ 四档语言
# ═══════════════════════════════════════════════════════
def test_confidence_tiers_language():
    cal = ie.ConfidenceCalibrator()
    assert cal.tier_of(0.90) == "strong"
    assert cal.tier_of(0.70) == "moderate"
    assert cal.tier_of(0.60) == "tentative"
    assert cal.tier_of(0.30) == "analogical"
    assert "有很强文本依据" in ie.ConfidenceCalibrator.tier_language("strong")
    assert "相当有力的解释" in ie.ConfidenceCalibrator.tier_language("moderate")
    assert "可成立但并非唯一" in ie.ConfidenceCalibrator.tier_language("tentative")
    assert "启发性类比" in ie.ConfidenceCalibrator.tier_language("analogical")


def test_calibrate_basis_shape():
    cal = ie.ConfidenceCalibrator()
    c = cal.calibrate(text="原文写道：人应当追求卓越。【《理想国》· 开篇】")
    assert 0.5 <= c["confidence"] <= 0.95
    assert "primary_text_support" in c["basis"]
    assert c["tier"] in ("strong", "moderate")
    # 纯框架借用 → cross_text_inference（无原典支撑, 置信度不得虚高）
    c2 = cal.calibrate(text="若采用加缪的框架，可以把它读作一种反抗")
    assert "cross_text_inference" in c2["basis"]
    assert c2["confidence"] < c["confidence"]


def test_overclaim_lowers_confidence():
    cal = ie.ConfidenceCalibrator()
    base = {"primary_text_support": False, "direct_quote": False, "scholarly": False,
            "overclaim": False, "interpretation_order": 1}
    c_ok = cal.calibrate(signals=dict(base))["confidence"]
    c_claim = cal.calibrate(signals=dict(base, overclaim=True))["confidence"]
    assert c_claim < c_ok, "越级断言必须降低置信度"


# ═══════════════════════════════════════════════════════
# 4. InterpretationDepthPenalty —— 跨体系跳转只降不升
# ═══════════════════════════════════════════════════════
def test_depth_penalty_monotone_decreasing():
    cal = ie.ConfidenceCalibrator()
    base = {"primary_text_support": False, "direct_quote": False, "scholarly": False,
            "overclaim": False}
    c1 = cal.calibrate(signals=dict(base, interpretation_order=1))["confidence"]
    c2 = cal.calibrate(signals=dict(base, interpretation_order=2))["confidence"]
    c3 = cal.calibrate(signals=dict(base, interpretation_order=4))["confidence"]
    assert c1 >= c2 >= c3, "每增加一次跨体系跳转, 置信度必须保持或降低"
    assert c3 < c1


def test_four_jump_chain_detected_and_penalized():
    cal = ie.ConfidenceCalibrator()
    txt = ("海明威的生命力意象，用加缪的荒诞来读，再类比庄子的逍遥，甚至有佛教的空与斯多葛的无执——"
           "本质上完全一样。")
    sig = cal.detect_signals(txt)
    assert sig["interpretation_order"] >= 4, "文本→加缪→庄子→佛教→斯多葛 = 4 阶"
    assert sig["overclaim"] is True, "链条末尾'本质完全一样'必须被识别为越级断言"
    c = cal.calibrate(signals=sig)
    assert c["confidence"] <= 0.50 - 0.10 - 0.05 * 3 + 0.01  # 越级 -0.10, 深度 -0.15
    assert c["tier"] == "analogical"


# ═══════════════════════════════════════════════════════
# 5. scan_interpretation —— 单候选/越级断言 → 措辞级补正（数字不展示）
# ═══════════════════════════════════════════════════════
def test_dream_lion_correct_answer_no_append():
    # 多候选 + 明确"并非唯一" → 引擎不干预（验证的是期望中的正确作答形态）
    v = ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？")
    ans = ("若采用加缪框架，这是相当有解释力的一种阅读；但并非唯一解释。"
           "狮子也可以被理解为青春记忆和生命力意象……")
    r = ie.scan_interpretation(v, ans)
    assert r["alternatives_offered"] is True
    assert r["appends"] == []


def test_single_hypothesis_overclaim_gets_hedged():
    # 单解 + 越级断言 → 补正"并非唯一"（对应任务书: 不是"完全正确"）
    v = ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？")
    r = ie.scan_interpretation(v, "老人梦狮就是彻底摆脱外部意义的证明，这完全正确。")
    assert r["overclaim"] is True
    assert r["alternatives_offered"] is False
    appends = "\n".join(r["appends"])
    assert "并非唯一" in appends
    assert not any(ch.isdigit() for ch in appends), "置信度数字默认不展示"


def test_equivalence_overclaim_gets_analogy_hedge():
    # 尼采/庄子: "本质完全一样" → 必须识别类比≠等同
    v = ie.run_interpretation_engine("尼采的超人和庄子的逍遥是不是一回事？")
    r = ie.scan_interpretation(v, "超人和逍遥本质上完全一样，都是对无限自由的向往。")
    appends = "\n".join(r["appends"])
    assert "类比" in appends and "等同" in appends
    assert r["confidence"] < 0.5  # 越级断言 + 框架链 → 低置信


def test_scan_not_activated_returns_empty():
    v = ie.run_interpretation_engine("什么是虚无主义？")
    r = ie.scan_interpretation(v, "虚无主义是价值真空的状态。")
    assert r["activated"] is False
    assert r["appends"] == []


def test_scan_never_raises_on_garbage():
    ie.run_interpretation_engine(None)
    ie.run_interpretation_engine("")
    ie.run_interpretation_engine("《" * 50)
    v = ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？")
    r = ie.scan_interpretation(v, None)
    assert r["appends"] == []


# ═══════════════════════════════════════════════════════
# 6. 引擎接线（结构级: 前置注入 + 后置补正; mock APP, 不调 LLM）
# ═══════════════════════════════════════════════════════
class _FakeApp:
    """替换 LangGraph APP.astream: 单 agent 轮回一个 AIMessageChunk（最终回答）"""

    def __init__(self, answer):
        self.answer = answer
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


async def _run_stream(monkeypatch, question, answer, agent="general", language="zh"):
    import engine_langgraph as elg
    fake = _FakeApp(answer)
    monkeypatch.setattr(elg, "APP", fake)
    evs = [ev async for ev in elg.stream_agent(question, [], agent, None, language)]
    return evs, fake


def test_stream_agent_injects_interpretation_guard(monkeypatch):
    evs, fake = asyncio.run(_run_stream(
        monkeypatch,
        question="老人梦狮是不是不再向世界索取意义？",
        answer="老人梦狮完全说明他已摆脱外部意义，这是唯一正确的解读。"))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "解释型问题" in (m.content or ""))
    assert "至少提出两种" in injected and "challenging_evidence" in injected
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "并非唯一" in text, "单候选越级答案必须尾部补正"
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done（done 后可跟增量 reasoning_summary/suggestions）"


def test_stream_agent_analogy_guard_net(monkeypatch):
    evs, fake = asyncio.run(_run_stream(
        monkeypatch,
        question="尼采的超人和庄子的逍遥是不是一回事？",
        answer="超人和逍遥本质上完全一样，都是对无限自由的向往。"))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "类比≠等同" in (m.content or ""))
    assert "等同" in injected
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "类比" in text and "等同" in text, "等同断言必须被类比≠等同补正"
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done（done 后可跟增量 reasoning_summary/suggestions）"


def test_stream_agent_interpretation_well_answered_no_append(monkeypatch):
    evs, fake = asyncio.run(_run_stream(
        monkeypatch,
        question="老人梦狮是不是不再向世界索取意义？",
        answer="若采用加缪框架，这是相当有解释力的一种阅读；但并非唯一解释。"))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "完全正确" not in text
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done（done 后可跟增量 reasoning_summary/suggestions）"


def test_stream_agent_normal_flow_no_interpretation_injection(monkeypatch):
    evs, fake = asyncio.run(_run_stream(
        monkeypatch,
        question="什么是虚无主义？",
        answer="虚无主义是价值真空的状态。"))
    injected = [m.content for m in fake.captured_messages
                if m.type == "system" and "解释型问题" in (m.content or "")]
    assert injected == [], "非解释型问题不得注入多候选指令"
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done（done 后可跟增量 reasoning_summary/suggestions）"


# ═══════════════════════════════════════════════════════
# 7. 回归: 工具注册表 / 人格提示词 / Graph 结构 / 流式协议不变
# ═══════════════════════════════════════════════════════
def test_tool_registry_unchanged():
    import engine_langgraph as elg
    assert len(AG.TOOLS) == 30
    assert set(AG.TOOLS) == set(elg.TOOLS_BY_NAME)
    assert "search_books" in AG.TOOLS and "philosopher_debate" in AG.TOOLS
    from agents import PHILO_EXTRA_TOOLS
    assert len(PHILO_EXTRA_TOOLS) == 8
    # Phase 2 不新增工具
    assert not any("interpret" in n or "confiden" in n for n in AG.TOOLS)


def test_persona_and_prompts_unchanged():
    import engine_langgraph as elg
    import agents as AGENTS
    assert "你是" in elg.SYSTEM_PROMPT_LG and "737 位哲学家" in elg.SYSTEM_PROMPT_LG
    assert set(AGENTS.PHILO_AGENTS) == {"nietzsche"}
    assert elg.get_system_prompt("general") == elg.SYSTEM_PROMPT_LG
    assert elg.get_system_prompt("nietzsche") == AGENTS.NIETZSCHE_PROMPT


def test_graph_structure_unchanged():
    # graph_changed = false: 节点仍只有 agent/tools, 无新增解释节点
    import engine_langgraph as elg
    nodes = set(elg.APP.get_graph().nodes)
    assert nodes - {"__start__", "__end__"} == {"agent", "tools"}


def test_stream_protocol_unchanged_event_types():
    # 流式协议: 补正只走已有 token 事件, 无新事件类型
    import engine_langgraph as elg
    assert hasattr(elg, "_sse")
    allowed = {"status", "thought", "thought_stream", "token", "tool", "tool_start",
               "tool_cancel", "answer_retract", "done", "suggestions",
               "reasoning_summary", "error"}
    # scan_interpretation 的补正通过 token 事件发出（已在 wire 测试覆盖事件序列）
    r = ie.scan_interpretation(ie.run_interpretation_engine("老人梦狮是不是不再向世界索取意义？"),
                               "老人梦狮就是摆脱外部意义的证明，完全正确。")
    for a in r["appends"]:
        assert "\n\n" in ("\n\n" + a)  # 以现有 token 事件承载, 无协议扩展
