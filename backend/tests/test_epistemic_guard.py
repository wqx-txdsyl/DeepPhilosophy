# -*- coding: utf-8 -*-
"""Epistemic Guard（Phase 1）用例——前提校正 / Claim 认知分级 / 反事实边界 / 引擎接线回归

覆盖 2026-08-30 Phase 1 验收项:
  Premise:    87天→84 / 尼采1889写反基督→1888 / 《存在与时间》里尼采→海德格尔 / 价值判断不核验
  Claim Type: 狮子意味着生命力→TEXTUAL_INFERENCE / "一定完成转变"→ 不得 SOURCE_FACT
  Counterfactual: 加缪怎么看《老人与海》→ COUNTERFACTUAL / 尼采怎么看AI→ COUNTERFACTUAL
  回归: 工具注册表 / 人格提示词 / 流式事件序列（mock APP, 不调 LLM）
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from langchain_core.messages import AIMessageChunk

import epistemic_guard as eg
from routes import agent as AG


# ═══════════════════════════════════════════════════════
# 1. PremiseVerifier —— 用户事实前提校正（非阻塞）
# ═══════════════════════════════════════════════════════
def test_oldman_87_days_corrected_to_84():
    checks = eg.PremiseVerifier().check("老人87天没捕到鱼，这说明了什么？")
    assert checks, "应检出 87 天前提错误"
    c = checks[0]
    assert c["status"] == "contradicted"
    assert c["claim_type"] == "textual_fact"
    assert c["verification_required"] is True
    assert "84" in c["corrected_value"]
    assert c["evidence"], "校正必须带证据来源"
    assert c["nonblocking"] is True   # 先校正, 不拒绝问题


def test_antichrist_year_premise():
    checks = eg.PremiseVerifier().check("尼采1889年写《反基督》时已经处于精神崩溃边缘")
    assert checks
    c = checks[0]
    assert c["status"] == "contradicted"
    assert "1888" in c["corrected_value"]   # 写于 1888 年（1889 才出版）


def test_antichrist_published_year_not_flagged():
    # "出版"是正确表述, 不得误伤（写 vs 出版是两个时间点）
    assert eg.PremiseVerifier().check("尼采的《反基督》于1889年出版") == []


def test_being_and_time_attribution_corrected():
    checks = eg.PremiseVerifier().check("《存在与时间》里尼采认为人是向死而生的")
    assert checks
    c = checks[0]
    assert c["status"] == "contradicted"
    assert "海德格尔" in c["corrected_value"]
    assert c["claim_type"] == "textual_fact"


def test_attribution_not_flagged_when_correct():
    # 正确归属不得误伤（经 books.json + 精配表校验）
    assert eg.PremiseVerifier().check("《存在与时间》里海德格尔认为人是向死而生的") == []
    assert eg.PremiseVerifier().check("海德格尔的《存在与时间》") == []


def test_value_judgment_not_verified():
    # 价值判断不执行 PremiseVerifier
    assert eg.PremiseVerifier().check("自由比安全更重要，你怎么看？") == []
    assert eg.PremiseVerifier().check("尼采的哲学是悲观的吗？") == []


# ═══════════════════════════════════════════════════════
# 2. EpistemicClaimClassifier —— Claim 认知分级 + 语言约束
# ═══════════════════════════════════════════════════════
def test_lion_dream_is_textual_inference():
    c = eg.EpistemicClaimClassifier().classify("老人梦见狮子意味着生命力")
    assert c["epistemic_type"] == "TEXTUAL_INFERENCE"


def test_strong_modal_interpretation_not_source_fact():
    c = eg.EpistemicClaimClassifier().classify("老人一定完成了从外部意义到内部意义的转变")
    assert c["epistemic_type"] != "SOURCE_FACT", "强模态解读不得定级为文本事实"
    assert c["epistemic_type"] in ("TEXTUAL_INFERENCE", "SPECULATION")


def test_all_types_defined_with_language_bounds():
    required = {"SOURCE_FACT", "DIRECT_QUOTE", "TEXTUAL_INFERENCE", "CROSS_TEXT_INTERPRETATION",
                "SCHOLARLY_INTERPRETATION", "AUTHOR_COUNTERFACTUAL", "USER_PREMISE",
                "SPECULATION", "UNKNOWN"}
    assert required <= set(eg.EPISTEMIC_TYPES), f"缺类型: {required - set(eg.EPISTEMIC_TYPES)}"
    for t in eg.EPISTEMIC_TYPES:
        assert t in eg.EPISTEMIC_LANGUAGE, f"{t} 缺表达强度模板"
        assert eg.EPISTEMIC_LANGUAGE[t].strip(), f"{t} 模板为空"
    # 关键模板内容（语言约束）
    assert "文本明确写道" in eg.EPISTEMIC_LANGUAGE["SOURCE_FACT"]
    assert "原文写道" in eg.EPISTEMIC_LANGUAGE["DIRECT_QUOTE"]
    assert "可以理解为" in eg.EPISTEMIC_LANGUAGE["TEXTUAL_INFERENCE"]
    assert "无法知道" in eg.EPISTEMIC_LANGUAGE["AUTHOR_COUNTERFACTUAL"]


def test_classify_variants():
    cl = eg.EpistemicClaimClassifier()
    assert cl.classify("原文写道：知识即美德")["epistemic_type"] == "DIRECT_QUOTE"
    assert cl.classify("文本明确写道：人应当追求卓越")["epistemic_type"] == "SOURCE_FACT"
    assert cl.classify("若采用加缪的框架，可以把它读作一种反抗")["epistemic_type"] == "CROSS_TEXT_INTERPRETATION"
    assert cl.classify("某种研究解释认为他是先验幻觉论者")["epistemic_type"] == "SCHOLARLY_INTERPRETATION"
    assert cl.classify("一种可能的解释是他晚年转向神秘主义")["epistemic_type"] == "SPECULATION"
    assert cl.classify("现有材料不足以判断他是否读过这本书")["epistemic_type"] == "UNKNOWN"
    assert cl.classify("你提出的前提不太成立")["epistemic_type"] == "USER_PREMISE"
    assert cl.classify("尼采会怎么看AI")["epistemic_type"] == "AUTHOR_COUNTERFACTUAL"


def test_classify_canonical_shape():
    c = eg.EpistemicClaimClassifier().classify("老人梦见狮子意味着生命力")
    # 关键 Claim 进入生成前必须能给出: claim / epistemic_type / confidence / evidence_ids
    assert set(c) >= {"claim", "epistemic_type", "confidence", "evidence_ids"}
    assert c["confidence"] is None          # Phase 1 不设 confidence
    assert isinstance(c["evidence_ids"], list)


# ═══════════════════════════════════════════════════════
# 3. CounterfactualAuthorGuard —— 反事实识别与历史/反事实分离
# ═══════════════════════════════════════════════════════
def test_camus_on_oldman_is_counterfactual():
    v = eg.CounterfactualAuthorGuard().check("加缪怎么看《老人与海》？")
    assert v["mode"] == "counterfactual"
    assert v["requires_guard"] is True
    assert v["author"] == "加缪"
    assert "没有证据表明加缪" in v["boundary_text"]


def test_nietzsche_on_ai_is_counterfactual():
    v = eg.CounterfactualAuthorGuard().check("尼采怎么看AI？")
    assert v["mode"] == "counterfactual"
    assert v["requires_guard"] is True
    assert v["epistemic_type"] == "AUTHOR_COUNTERFACTUAL"
    assert "没有证据表明尼采" in v["boundary_text"]


def test_liveness_counterfactual():
    v = eg.CounterfactualAuthorGuard().check("叔本华如果活到今天会怎么看智能手机？")
    assert v["mode"] == "counterfactual"
    assert v["requires_guard"] is True


def test_historical_vs_counterfactual_separated():
    # 作者自己的作品/已载史料的主题 → historical（正常回答）, 不插边界
    v1 = eg.CounterfactualAuthorGuard().check("加缪在《西西弗斯神话》中对自杀的论证")
    assert v1["mode"] == "historical"
    assert v1["requires_guard"] is False
    v2 = eg.CounterfactualAuthorGuard().check("尼采如何看待瓦格纳？")
    assert v2["mode"] == "historical"
    assert v2["requires_guard"] is False
    v3 = eg.CounterfactualAuthorGuard().check("康德在《纯粹理性批判》中如何论证先验")
    assert v3["mode"] == "historical"


def test_boundary_present_check():
    a = "加缪反对自杀，认为反抗才有出路。"
    assert eg.CounterfactualAuthorGuard.boundary_present(a, "加缪") is False
    b = "没有证据表明加缪本人评论过这一对象；以下是依据其已知思想框架进行的反事实推演。"
    assert eg.CounterfactualAuthorGuard.boundary_present(b, "加缪") is True


# ═══════════════════════════════════════════════════════
# 4. 引擎接线（结构级: 前置注入 + 后置补正; mock APP, 不调 LLM）
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


def test_stream_agent_injects_premise_correction(monkeypatch):
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="老人87天没捕到鱼，这说明了什么？",
                                        answer="《老人与海》开篇写的是连续84天没有捕到鱼。"))
    # 前置: 校正注入进入上下文
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "前提校验" in (m.content or ""))
    assert "84" in injected and "87天" in injected
    # 后置: 答案按注入输出校正; 事件序列不变量（token 之后才 done）
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "84天" in text
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done（done 后可跟增量 reasoning_summary/suggestions）"


def test_stream_agent_counterfactual_boundary_state_audited(monkeypatch):
    # O2 改写: LLM 未写边界 → runtime 不再尾补边界句（正文零代写）;
    # 反事实状态如实随 done.epistemic 审计输出, 由 Main Agent 自主落实
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="尼采怎么看AI？",
                                        answer="尼采会拥抱这个新时代。"))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "反事实边界" in (m.content or ""))
    assert "尼采" in injected, "前置注入（prompt 层要求）保留"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "没有证据表明尼采" not in text, "runtime 不得再代写边界句——正文原样发布"
    assert "尼采会拥抱这个新时代。" in text
    done = next(ev for ev in evs if ev["type"] == "done")
    epi = done.get("epistemic") or {}
    cf = epi.get("counterfactual") or {}
    assert cf.get("requires_guard") is True and cf.get("author") == "尼采", \
        "反事实 guard 状态随 done.epistemic 如实输出"
    assert done["final_ownership"]["runtime_factual_appends"] == 0


def test_stream_agent_normal_flow_no_guard(monkeypatch):
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="什么是虚无主义？",
                                        answer="虚无主义是价值真空的状态。"))
    injected = [m.content for m in fake.captured_messages
                if m.type == "system" and ("前提校验" in (m.content or "") or "反事实边界" in (m.content or ""))]
    assert injected == [], "普通问题不得注入护栏"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "虚无主义" in text
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done（done 后可跟增量 reasoning_summary/suggestions）"


# ═══════════════════════════════════════════════════════
# 5. 回归: 工具注册表 / 人格数据 / 流式协议不变
# ═══════════════════════════════════════════════════════
def test_tool_registry_unchanged_by_guard():
    before = dict(AG.TOOLS)
    import engine_langgraph as elg
    # 重载时工具数/名称不得因 guard 变化（guard 不注册任何工具）
    assert set(before) == set(elg.TOOLS_BY_NAME)
    assert len(before) == 30
    assert "search_books" in before and "philosopher_debate" in before
    # 哲学家专属四件套不变
    from agents import PHILO_EXTRA_TOOLS
    assert len(PHILO_EXTRA_TOOLS) == 8


def test_persona_and_prompts_unchanged():
    import engine_langgraph as elg
    import agents as AGENTS
    assert "你是" in elg.SYSTEM_PROMPT_LG and "737 位哲学家" in elg.SYSTEM_PROMPT_LG
    assert set(AGENTS.PHILO_AGENTS) == {"nietzsche"}, "Phase 1 禁新增哲学家"
    assert "查拉图斯特拉的作者" in AGENTS.NIETZSCHE_PROMPT
    assert elg.get_system_prompt("general") == elg.SYSTEM_PROMPT_LG
    assert elg.get_system_prompt("nietzsche") == AGENTS.NIETZSCHE_PROMPT


def test_epistemic_guard_never_raises_on_garbage():
    # 护栏对任意输入不抛出（尽力而为）
    for q in ["", None, "???", "《" * 50, "a" * 10000,
              "海德格尔的《存在与时间》里尼采87天1889年写反基督"]:
        assert eg.run_epistemic_guards(q or "") is not None
