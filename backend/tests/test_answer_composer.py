# -*- coding: utf-8 -*-
"""Answer Composer（Phase 4）用例——回答结构 / 隐藏推理 / DeepSeek 优点吸收边界 / 引擎接线

覆盖 2026-08-30 Phase 4 验收项:
  结构:     默认五段（直接判断→2~4核心理由→关键文本证据→反方/限定→结论）; 禁止默认骨架
            （材料说明/工具说明/检索过程/五层报告/原典路径/再总结）; 生成类请求不注入
  隐藏推理: 过程叙述（"让我检索…""我已经有材料了"）检出; 用户只看推理摘要（✦）
  风格吸收: 允许快给中心论点/概念压缩/比喻/自然段落/有力结尾;
            禁止未经 epistemic state 支持的强化措辞（完全正确/毫无疑问/绝不会/本质就是）
  后置:     强化措辞/推理噪音/骨架残留 → 措辞级补正; 解释型问题不重复补正（防双补）
  摘要兜底: LLM 摘要缺席 → 确定性推理摘要（核验文本事实/检索原典/比较解释/结论置信度）
  回归:     工具注册表 / 流式事件序列（mock APP, 不调 LLM）
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from langchain_core.messages import AIMessageChunk

import answer_composer as ac
from routes import agent as AG


# ═══════════════════════════════════════════════════════
# 1. 前置注入——自适应回答形态（B7）+ 禁止默认骨架 + 隐藏推理 + 风格吸收
# ═══════════════════════════════════════════════════════
def test_composer_always_activated_for_plain_question():
    v = ac.run_answer_composer("从《老人与海》看加缪的荒谬主义。")
    assert v["activated"] is True
    # Patch 1 (B7): 自适应形态注入 + 通用质量约束 + Phase S 篇幅预算注入
    assert len(v["injections"]) >= 2
    assert "回答形态" in v["injections"][0]
    assert "篇幅预算" in v["injections"][-1]


def test_injection_contains_full_structure():
    inj = "\n".join(ac.run_answer_composer("什么是荒诞？")["injections"])
    # Patch 1 (B7): 形态由 problem type 决定（CONCEPT_EXPLANATION → 概念层次推进）
    assert "回答形态" in inj and "先直接界定概念" in inj
    # 不再规定固定编号标题/固定五段骨架
    assert "① 直接判断" not in inj and "② 2~4 个核心理由" not in inj
    # 五段定义仅保留为内部元数据（不进入注入）
    assert [s[0] for s in ac.ANSWER_STRUCTURE] == [
        "direct_judgment", "core_reasons", "text_evidence",
        "counter_qualification", "conclusion"]


def test_injection_bans_default_skeleton():
    inj = "\n".join(ac.run_answer_composer("什么是荒诞？")["injections"])
    for block in ("材料说明", "工具说明", "检索过程", "五层报告", "原典路径", "再总结"):
        assert block in inj, f"默认骨架禁止项缺 {block}"


def test_injection_hides_raw_reasoning():
    inj = "\n".join(ac.run_answer_composer("什么是荒诞？")["injections"])
    assert "让我检索" in inj or "过程叙述" in inj
    assert "推理摘要" in inj, "用户只看到推理摘要"
    assert "工具调用卡片由界面展示" in inj


def test_injection_absorbs_deepseek_strengths_but_bans_overclaim():
    inj = "\n".join(ac.run_answer_composer("什么是荒诞？")["injections"])
    # 优点吸收
    for good in ("更快给出中心论点", "概念压缩", "比喻", "有力量的结尾"):
        assert good in inj, f"风格吸收缺 {good}"
    # 强化措辞禁令
    for bad in ("完全正确", "毫无疑问", "绝不会", "本质就是"):
        assert bad in inj, f"强化措辞禁令缺 {bad}"


def test_generative_requests_skip_composer():
    # 生成类请求不注入通用回答结构（成品形态由专门工具决定）
    for q in ("帮我写一篇关于自由的作文", "写一首诗", "生成一张尼采的画像", "让尼采和庄子辩论"):
        v = ac.run_answer_composer(q)
        assert v["activated"] is False, f"生成类请求不应注入: {q}"
        assert v["injections"] == []


def test_english_injection():
    inj = "\n".join(ac.run_answer_composer("What is absurdity?", language="en")["injections"])
    # Patch 1 (B7): 英文形态注入（自适应 form + 质量约束）
    assert "[Answer form]" in inj and "essentially" in inj


# ═══════════════════════════════════════════════════════
# 2. 检测: 强化措辞 / 推理噪音 / 默认骨架 / 直接判断 / 冗余
# ═══════════════════════════════════════════════════════
def test_strong_wording_detected():
    scan = ac.scan_composition(ac.run_answer_composer("什么是荒诞？"),
                               "荒诞就是理性与世界之间的裂隙，这完全正确。")
    assert "完全正确" in scan["strong_wording"]
    scan2 = ac.scan_composition(ac.run_answer_composer("什么是荒诞？"),
                                "这毫无疑问是加缪的命题，本质就是理性与世界的裂隙。")
    assert "毫无疑问" in scan2["strong_wording"] and "本质就是" in scan2["strong_wording"]


def test_negated_strong_wording_not_flagged():
    # "并非完全正确"是合法限定, 不得误伤
    scan = ac.scan_composition(ac.run_answer_composer("什么是荒诞？"),
                               "这一读法并非完全正确，只是一种可能。")
    assert scan["strong_wording"] == []


def test_reasoning_noise_detected():
    bad = "让我先检索一下材料。现在我已经有材料了，让我读取第一章。"
    scan = ac.scan_composition(ac.run_answer_composer("什么是荒诞？"), bad)
    assert "让我检索" in scan["reasoning_noise"] or "让我先" in scan["reasoning_noise"]
    assert "我已经有材料" in scan["reasoning_noise"]
    assert scan["direct_judgment"] is False


def test_banned_default_blocks_detected():
    bad = ("材料说明：我找到了三本书。检索过程：先查了《西西弗斯神话》。"
           "再总结：以上就是全部。")
    scan = ac.scan_composition(ac.run_answer_composer("什么是荒诞？"), bad)
    assert "材料说明" in scan["banned_blocks"]
    assert "检索过程" in scan["banned_blocks"]
    assert "再总结" in scan["banned_blocks"]


def test_directness_detection():
    good = "荒诞是理性与世界的裂隙，加缪对此有过系统的论证【《西西弗斯神话》·开篇】。"
    bad = "让我先检索一下《老人与海》的材料，然后再说明。"
    assert ac.scan_composition(ac.run_answer_composer("什么是荒诞？"), good)["direct_judgment"] is True
    assert ac.scan_composition(ac.run_answer_composer("什么是荒诞？"), bad)["direct_judgment"] is False


def test_redundancy_detected():
    ans = ("荒诞是理性与世界的裂隙。荒诞是理性与世界的裂隙。"
           "综上，总之，总而言之，结论是荒诞。")
    scan = ac.scan_composition(ac.run_answer_composer("什么是荒诞？"), ans)
    assert scan["redundancy"], "重复句/总结堆叠必须检出"


def test_structure_signals():
    good = ("我的判断是：可以用加缪的框架读《老人与海》。首先，老人与大鱼对峙却不求占有，"
            "接近西西弗斯的反抗【《西西弗斯神话》·荒诞的自由】。但也要指出，海明威未必接受"
            "'荒诞'这一标签。结论：这是一种有解释力的读法，但并非唯一。")
    scan = ac.scan_composition(ac.run_answer_composer("从《老人与海》看加缪的荒谬主义。"), good)
    assert scan["direct_judgment"] is True
    s = scan["structure_signals"]
    assert s["evidence_marker"] is True
    assert s["reasons_enumerated"] is True
    assert s["counter_qualification"] is True
    assert s["conclusion_marker"] is True
    assert scan["appends"] == []


# ═══════════════════════════════════════════════════════
# 3. 后置补正——强化措辞 / 过程开头; 防双补
# ═══════════════════════════════════════════════════════
def test_strong_wording_gets_hedge_appended():
    v = ac.run_answer_composer("什么是荒诞？")
    scan = ac.scan_composition(v, "荒诞是理性与世界的裂隙，这完全正确。")
    assert scan["strong_wording"]
    appends = "\n".join(scan["appends"])
    assert "强化措辞" in appends or "完全正确" in appends
    assert not any(ch.isdigit() for ch in appends), "补正只做措辞级, 不展示置信度数字"


def test_no_double_hedge_when_interpretation_scan_appended():
    # 解释型问题的强化措辞已由 interpretation_engine 补正 → composer 不重复
    v = ac.run_answer_composer("老人梦狮是不是不再向世界索取意义？")
    isc = {"appends": ["（补充：这是一种可成立但并非唯一的解释……）"]}
    scan = ac.scan_composition(v, "老人梦狮就是彻底摆脱外部意义的证明，这毫无疑问。",
                               interpretation_scan=isc)
    assert scan["strong_wording"], "强化措辞仍须检出（审计用）"
    assert scan["appends"] == [], "解释型问题已补正过 → composer 不得重复补"


def test_short_answer_no_directness_nudge():
    v = ac.run_answer_composer("什么是荒诞？")
    scan = ac.scan_composition(v, "让我检索一下。")
    assert scan["appends"] == [], "短回答不得补'结论先行'提示（防误伤）"


def test_generative_verdict_scan_empty():
    v = ac.run_answer_composer("帮我写一篇作文")
    scan = ac.scan_composition(v, "随便什么内容，这完全正确。")
    assert scan["activated"] is False
    assert scan["appends"] == []


def test_scan_never_raises_on_garbage():
    v = ac.run_answer_composer("什么是荒诞？")
    for ans in [None, "", "《" * 50, "a" * 10000]:
        r = ac.scan_composition(v, ans)
        assert r["appends"] == []
    assert ac.run_answer_composer(None)["injections"] == []
    assert ac.run_answer_composer("")["injections"] == []


# ═══════════════════════════════════════════════════════
# 4. 确定性推理摘要（✦ 推理摘要兜底）
# ═══════════════════════════════════════════════════════
def test_reasoning_summary_from_verdicts():
    epi = {"premise_checks": [{"status": "contradicted"}],
           "counterfactual": {"requires_guard": False}}
    interp = {"activated": True, "categories": ["literary_interpretation", "philosophical_interpretation"]}
    isc = {"tier": "tentative"}
    ev = {"retrieved_count": 20, "used_count": 3}
    tl = [{"name": "search_books"}, {"name": "get_chapter"}]
    s = ac.build_reasoning_summary(epi, interp, isc, ev, tl)
    assert s is not None
    assert "核验文本事实" in s and "检索原典" in s
    assert "候选解读" in s
    assert "3/20" in s and "结论置信度" in s
    assert s.startswith("1.") and "4." in s


def test_reasoning_summary_counterfactual_step():
    epi = {"premise_checks": [], "counterfactual": {"requires_guard": True, "author": "加缪"}}
    s = ac.build_reasoning_summary(epi, {"activated": False}, None, None, None)
    assert "反事实边界" in s


def test_reasoning_summary_none_when_no_info():
    assert ac.build_reasoning_summary(None, None, None, None, None) is None
    assert ac.build_reasoning_summary({"premise_checks": []}, {"activated": False},
                                      None, None, []) is None


# ═══════════════════════════════════════════════════════
# 5. 引擎接线（mock APP, 不调 LLM）
# ═══════════════════════════════════════════════════════
class _FakeApp:
    """替换 LangGraph APP.astream: 单 agent 轮回一个 AIMessageChunk（最终回答）"""

    def __init__(self, answer):
        self.answer = answer
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


async def _run_stream(monkeypatch, question, answer, language="zh"):
    import engine_langgraph as elg
    fake = _FakeApp(answer)
    monkeypatch.setattr(elg, "APP", fake)
    monkeypatch.setattr(AG, "llm_chat",
                        lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = [ev async for ev in elg.stream_agent(question, [], "general", None, language)]
    return evs, fake


def test_stream_agent_injects_composer_structure(monkeypatch):
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="什么是荒诞？",
                                        answer="荒诞是理性与世界的裂隙。"))
    # Patch 1 (B7): 注入按问题类型自适应的回答形态（"什么是X" → CONCEPT_EXPLANATION）
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and ("回答形态" in (m.content or "") or "回答结构" in (m.content or "")))
    assert "先直接界定概念" in injected
    assert "材料说明" in injected  # 禁止默认骨架的通用约束仍在
    assert "让我检索" in injected or "过程叙述" in injected
    assert next(ev for ev in evs if ev["type"] == "done")["type"] == "done"


def test_stream_agent_strong_wording_gets_hedge(monkeypatch):
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="什么是荒诞？",
                                        answer="荒诞是理性与世界的裂隙，这完全正确。"))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "强化措辞" in text, "非解释型问题的强化措辞必须由 composer 补正"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["type"] == "done"
    assert done.get("composition") is not None, "done 事件携带 composition 扫描结果"
    assert done["composition"]["strong_wording"] == ["完全正确"]


def test_stream_agent_reasoning_noise_gets_nudge(monkeypatch):
    bad = ("让我先检索一下《老人与海》和《西西弗斯神话》的材料。现在我已经有材料了，"
           "让我读取第一章的内容，把两个文本都读一遍。材料说明：我找到了三本书，"
           "其中两本直接相关。检索过程：先查了《西西弗斯神话》的开篇，"
           "又查了《老人与海》的结尾。再总结：以上就是全部检索结果，下面进入正题。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, question="什么是荒诞？", answer=bad))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "直接判断" in text, "过程叙述开头必须补'结论先行'提示"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["composition"]["direct_judgment"] is False
    assert done["composition"]["banned_blocks"]
    assert next(ev for ev in evs if ev["type"] == "done")["type"] == "done"


def test_stream_agent_well_composed_no_append(monkeypatch):
    good = ("我的判断是：加缪的荒谬主义可以在《老人与海》中得到印证，但这是借来的框架。"
            "首先，圣地亚哥对抗大马林鱼却不求占有，接近西西弗斯的反抗"
            "【《西西弗斯神话》·荒诞的自由】。其次，狮子是生命力的延续而非来世许诺"
            "【《老人与海》·结尾】。但也要指出，海明威未必接受'荒诞'这个标签。"
            "结论：这是一种有解释力的读法，但并非唯一。")
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="从《老人与海》看加缪的荒谬主义。", answer=good))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "强化措辞" not in text and "并非唯一" in text
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["composition"]["direct_judgment"] is True
    assert done["composition"]["appends"] == []
    assert done["composition"]["strong_wording"] == []


def test_stream_agent_no_runtime_reasoning_summary_event(monkeypatch):
    # RP1 (O1-RP1): 事后推理摘要通道已整体删除——runtime 不得摘要 raw CoT 冒充 Agent
    # （mini-LLM），也不得用 Python 编造确定性摘要（旧兜底）。
    # reasoning_summary 事件不得再出现在生产流; public Thinking 唯一来源 =
    # thinking_summary(_delta)（模型自己写的 rationale / 公开工作笔记）。
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="老人从一开始87天的执念到了最后安然睡觉，梦见狮子，"
                                                 "是不是恰是他不再向世界索取意义？",
                                        answer="先纠正：《老人与海》开篇写的是连续84天没有捕到鱼。"
                                               "回到问题：这可以读作不再向世界索取意义，但并非唯一读法。"))
    assert [ev for ev in evs if ev["type"] == "reasoning_summary"] == [], \
        "runtime 生成的 reasoning_summary 事件已废除, 不得回流"
    # 回答正文不受影响, 照常流出
    answer = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "84" in answer


def test_stream_agent_generative_no_composer(monkeypatch):
    evs, fake = asyncio.run(_run_stream(monkeypatch,
                                        question="帮我写一篇关于自由的作文",
                                        answer="作文正文……"))
    injected = [m.content for m in fake.captured_messages
                if m.type == "system" and "回答结构" in (m.content or "")]
    assert injected == [], "生成类请求不得注入回答结构"
    assert next(ev for ev in evs if ev["type"] == "done")["type"] == "done"
