# -*- coding: utf-8 -*-
"""Claim 认知分级（evidence_contract）+ 引擎接线回归

覆盖（O4-RP1 适配后）:
  Claim Type: 狮子意味着生命力→TEXTUAL_INFERENCE / "一定完成转变"→ 不得 SOURCE_FACT
              （evidence_contract 生产依赖——O4-RP1 起分类器迁入 evidence_contract, 接口不变）
  O4/O4-RP1: CounterfactualAuthorGuard / scan_answer / 反事实与认知层级 hedge 注入 /
      PremiseVerifier 事实校正注入已全部删除——runtime 不再对用户前提或哲学陈述
      做任何"先替 Agent 判断再注入结论"的语义治理
      （EPISTEMIC_GUARD_SEMANTIC_JUDGMENT=0; PRE_LLM_FACTUAL_CORRECTION_AUTHORITY=0）。
      行为契约见 test_o4_cognitive_collapse.T4 / TestRP1.R4。
  回归: 工具注册表 / 人格提示词 / 流式事件序列（mock APP, 不调 LLM）
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from langchain_core.messages import AIMessageChunk

from evidence_contract import EpistemicClaimClassifier, EPISTEMIC_TYPES
from routes import agent as AG


# ═══════════════════════════════════════════════════════
# 1. EpistemicClaimClassifier —— Claim 认知分级
#    （O4-RP1: 自已删除的 guard 模块迁入 evidence_contract; 接口/classify 行为不变）
# ═══════════════════════════════════════════════════════
def test_lion_dream_is_textual_inference():
    c = EpistemicClaimClassifier().classify("老人梦见狮子意味着生命力")
    assert c["epistemic_type"] == "TEXTUAL_INFERENCE"


def test_strong_modal_interpretation_not_source_fact():
    c = EpistemicClaimClassifier().classify("老人一定完成了从外部意义到内部意义的转变")
    assert c["epistemic_type"] != "SOURCE_FACT", "强模态解读不得定级为文本事实"
    assert c["epistemic_type"] in ("TEXTUAL_INFERENCE", "SPECULATION")


def test_types_schema_intact_language_layer_moved_out():
    # O5 §7: 存储/展示层仍有价值的 claim taxonomy schema 保留在 evidence_contract;
    # 表达强度模板（EPISTEMIC_LANGUAGE/language_bound）已迁离生产模块
    # （离线评估套件 evaluation_suite 自带副本）——运行时不再持有语言约束层。
    required = {"SOURCE_FACT", "DIRECT_QUOTE", "TEXTUAL_INFERENCE", "CROSS_TEXT_INTERPRETATION",
                "SCHOLARLY_INTERPRETATION", "AUTHOR_COUNTERFACTUAL", "USER_PREMISE",
                "SPECULATION", "UNKNOWN"}
    assert required <= set(EPISTEMIC_TYPES), f"缺类型: {required - set(EPISTEMIC_TYPES)}"
    import evidence_contract as EC
    assert not hasattr(EC, "EPISTEMIC_LANGUAGE"), "语言模板层不得回归生产 evidence_contract"
    assert not hasattr(EC.EpistemicClaimClassifier, "language_bound")
    assert not hasattr(EC.EpistemicClaimClassifier, "split_sentences"), "D6: 方法级重复已删"
    import evaluation_suite as EV   # 副本迁入离线评估套件（不丢能力）
    assert set(EV.EPISTEMIC_LANGUAGE) >= required
    assert EV.language_bound("SOURCE_FACT").strip()


def test_classify_variants():
    cl = EpistemicClaimClassifier()
    assert cl.classify("原文写道：知识即美德")["epistemic_type"] == "DIRECT_QUOTE"
    assert cl.classify("文本明确写道：人应当追求卓越")["epistemic_type"] == "SOURCE_FACT"
    assert cl.classify("若采用加缪的框架，可以把它读作一种反抗")["epistemic_type"] == "CROSS_TEXT_INTERPRETATION"
    assert cl.classify("某种研究解释认为他是先验幻觉论者")["epistemic_type"] == "SCHOLARLY_INTERPRETATION"
    assert cl.classify("一种可能的解释是他晚年转向神秘主义")["epistemic_type"] == "SPECULATION"
    assert cl.classify("现有材料不足以判断他是否读过这本书")["epistemic_type"] == "UNKNOWN"
    assert cl.classify("你提出的前提不太成立")["epistemic_type"] == "USER_PREMISE"
    assert cl.classify("尼采会怎么看AI")["epistemic_type"] == "AUTHOR_COUNTERFACTUAL"


def test_classify_canonical_shape():
    c = EpistemicClaimClassifier().classify("老人梦见狮子意味着生命力")
    # 关键 Claim 进入生成前必须能给出: claim / epistemic_type / confidence / evidence_ids
    assert set(c) >= {"claim", "epistemic_type", "confidence", "evidence_ids"}
    assert c["confidence"] is None          # 不设 confidence
    assert isinstance(c["evidence_ids"], list)


# ═══════════════════════════════════════════════════════
# 2. 引擎接线（结构级: 无任何前提校正/反事实注入; mock APP, 不调 LLM）
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


def test_stream_agent_premise_correction_injection_removed(monkeypatch):
    # O4-RP1: 旧 guard 会在构造上述输入时注入"前提校验（系统）"式认知 directive——
    # 现在 runtime 零注入: 事实由 Main Agent 自主检索核验后自行纠正
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="老人87天没捕到鱼，这说明了什么？",
                                        answer="《老人与海》开篇写的是连续84天没有捕到鱼。"))
    injected = [m.content for m in fake.captured_messages
                if m.type == "system" and "前提" in (m.content or "")]
    assert injected == [], "前提校正注入不得回归（PRE_LLM_FACTUAL_CORRECTION_AUTHORITY=0）"
    # 答案原样发布; 事件序列不变量（token 之后才 done）
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "84天" in text
    done = next(ev for ev in evs if ev["type"] == "done")
    assert "epistemic" not in done
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done"


def test_stream_agent_counterfactual_no_runtime_hedge(monkeypatch):
    # O4: 反事实语义判断已删除——无边界注入、无 done.epistemic 审计块;
    # 解释性/反事实文本由 Main Agent 自己负责, runtime 零改写零追加（T4 契约）
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="尼采怎么看AI？",
                                        answer="尼采会拥抱这个新时代。"))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "反事实边界" in (m.content or ""))
    assert injected == "", "反事实边界注入不得回归"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "没有证据表明尼采" not in text, "runtime 不得代写边界句——正文原样发布"
    assert "尼采会拥抱这个新时代。" in text
    done = next(ev for ev in evs if ev["type"] == "done")
    assert "epistemic" not in done, "O4: done.epistemic 审计块已删除"
    assert done["final_ownership"]["runtime_factual_appends"] == 0


def test_stream_agent_normal_flow_no_guard(monkeypatch):
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="什么是虚无主义？",
                                        answer="虚无主义是价值真空的状态。"))
    injected = [m.content for m in fake.captured_messages
                if m.type == "system" and ("前提" in (m.content or "") or "反事实边界" in (m.content or ""))]
    assert injected == [], "普通问题不得注入护栏"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "虚无主义" in text
    done_i = next(i for i, e in enumerate(evs) if e["type"] == "done")
    tok_i = [i for i, e in enumerate(evs) if e["type"] == "token"]
    assert not tok_i or done_i > max(tok_i), "流式协议不变: token 之后才 done"


# ═══════════════════════════════════════════════════════
# 3. 回归: 工具注册表 / 人格数据 / 流式协议不变
# ═══════════════════════════════════════════════════════
def test_tool_registry_unchanged():
    before = dict(AG.TOOLS)
    import engine_langgraph as elg
    # 工具数/名称不得变化（分级器不注册任何工具）; O5: 经 TOOLS_LG 断言（TOOLS_BY_NAME 已删）
    assert set(before) == {t.name for t in elg.TOOLS_LG}
    assert len(before) == 32  # O7-C +2 scholarly
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
