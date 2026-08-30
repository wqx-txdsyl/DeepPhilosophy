# -*- coding: utf-8 -*-
"""《老人与海》固定回归集（Phase 4, 永久保留, 不得删除）

三题必须永久存在——它们分别覆盖 Phase 4 的三条主线:

  T1  从《老人与海》看加缪的荒谬主义。
      框架读法（从《》看）→ 多候选解读 + 回答结构（直接判断→理由→证据→反方→结论）
  T2  加缪会不会认为老人梦见狮子是一种逃避式希望，还是恰恰证明荒诞幸福？
      二选一读法（是A还是B）+ 反事实边界 + 类比≠等同 + 强化措辞禁令
  T3  老人从一开始87天的执念到了最后安然睡觉，梦见狮子，
      是不是恰是他不再向世界索取意义？
      特别要求: 必须纠正 84 天（87→84）, 且不能因此破坏主体分析
      （先校正一两句, 然后继续完整回答; 校正不得吞掉分析、不得拒绝问题）

覆盖 2026-08-30 Phase 4 验收项:
  结构:     T1/T2/T3 的好回答 → scan_composition 零补正、五维评估全过
  校正:     T3 检出 87→84（"执念"语境）; 注入先纠正再回答; 校正不破坏主体分析
  双补防护: T2 越级断言只补正一次（interpretation 补了 composer 不再补）
  摘要兜底: T3 无 LLM 摘要 → 确定性推理摘要（核验文本事实…）
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AIMessageChunk

import epistemic_guard as eg
import interpretation_engine as ie
import answer_composer as ac
import evaluation_suite as ev
from routes import agent as AG

T1 = "从《老人与海》看加缪的荒谬主义。"
T2 = "加缪会不会认为老人梦见狮子是一种逃避式希望，还是恰恰证明荒诞幸福？"
T3 = ("老人从一开始87天的执念到了最后安然睡觉，梦见狮子，"
      "是不是恰是他不再向世界索取意义？")
REGRESSION = [T1, T2, T3]


def test_regression_set_permanent():
    # 三题永久保留; T3 自带 87 天错误前提（84 天才是正解）
    assert REGRESSION == [T1, T2, T3]
    assert "87" in T3 and "84" not in T3


# ═══════════════════════════════════════════════════════
# 引擎接线（mock APP, 不调 LLM）
# ═══════════════════════════════════════════════════════
class _FakeApp:
    """替换 LangGraph APP.astream: 单 agent 轮回一个 AIMessageChunk（最终回答）"""

    def __init__(self, answer):
        self.answer = answer
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


async def _run_stream(monkeypatch, question, answer, agent="general"):
    import engine_langgraph as elg
    fake = _FakeApp(answer)
    monkeypatch.setattr(elg, "APP", fake)
    monkeypatch.setattr(AG, "llm_chat",
                        lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = [ev async for ev in elg.stream_agent(question, [], agent, None, "zh")]
    return evs, fake


# ═══════════════════════════════════════════════════════
# T1 —— 从《老人与海》看加缪的荒谬主义
# ═══════════════════════════════════════════════════════
def test_t1_framed_reading_triggers_interpretation():
    v = ie.run_interpretation_engine(T1)
    assert v["activated"] is True, "「从《》看」框架读法必须触发解释机制"
    assert "literary_interpretation" in v["categories"]
    assert "philosophical_interpretation" in v["categories"]
    assert v["hypothesis_min"] >= 2


def test_t1_good_answer_passes_evaluation():
    ans = ("我的判断是：加缪的荒谬主义在《老人与海》中可以得到印证，但这是借来的框架，"
           "不是海明威明写的主题。首先，圣地亚哥对抗大马林鱼却不求占有，接近西西弗斯的反抗"
           "【《西西弗斯神话》·荒诞的自由】。其次，梦中的狮子是生命力的延续而非来世许诺"
           "【《老人与海》·结尾】。但也可以质疑：海明威未必接受'荒诞'这个标签。"
           "结论：这是一种有解释力的读法，但并非唯一。")
    hits = [{"book_id": "b1", "book_title": "西西弗斯神话", "author": "加缪",
             "chapter_idx": 0, "chapter_title": "荒诞的自由",
             "snippet": "加缪写道: 荒诞在于把意义强加给世界。", "score": 0.9},
            {"book_id": "b2", "book_title": "老人与海", "author": "海明威",
             "chapter_idx": 3, "chapter_title": "结尾",
             "snippet": "老人正梦见狮子。", "score": 0.9}]
    tl = [{"name": "search_books", "args": {"query": "荒诞 狮子"}, "result_summary": "",
           "result_full": {"results": hits, "query": "荒诞 狮子"}}]
    r = ev.evaluate_answer(T1, ans, tool_log=tl)
    for dim in ("premise", "epistemic", "interpretation", "evidence", "ux"):
        assert r[dim]["passed"] is True, f"T1 {dim}: {r[dim]['findings']}"
    assert r["passed_all"] is True


def test_t1_wire_well_composed_no_append(monkeypatch):
    good = ("我的判断是：加缪的荒谬主义在《老人与海》中可以得到印证，但这是借来的框架。"
            "首先，圣地亚哥对抗大马林鱼却不求占有，接近西西弗斯的反抗"
            "【《西西弗斯神话》·荒诞的自由】。其次，狮子是生命力的延续而非来世许诺"
            "【《老人与海》·结尾】。但也可以质疑，海明威未必接受'荒诞'这个标签。"
            "结论：这是一种有解释力的读法，但并非唯一。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, T1, good))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "回答结构" in (m.content or ""))
    assert "直接判断" in injected
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["type"] == "done"
    assert done["composition"]["direct_judgment"] is True
    assert done["composition"]["appends"] == [], "结构完整的好回答不得补正"
    assert done["composition"]["strong_wording"] == []


def test_t1_wire_unhedged_assertion_hedged(monkeypatch):
    bad = ("加缪的荒谬主义本质就是海明威的主题。但并非唯一。"
           "让我先检索一下材料，现在我已经有材料了。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, T1, bad))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "强化措辞" in text, "未经证据支持的'本质就是'必须被 composer 补正"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["composition"]["strong_wording"] == ["本质就是"]
    assert done["composition"]["appends"]


# ═══════════════════════════════════════════════════════
# T2 —— 逃避式希望 vs 荒诞幸福
# ═══════════════════════════════════════════════════════
def test_t2_either_or_triggers_interpretation():
    v = ie.run_interpretation_engine(T2)
    assert v["activated"] is True, "「是A还是B」二选一读法必须触发解释机制"
    assert "literary_interpretation" in v["categories"]
    assert "philosophical_interpretation" in v["categories"]
    assert v["evidence_requirement"] == {"supporting": True, "challenging": True}


def test_t2_camus_guard_verdict_sane():
    # 荒诞属已载史料主题 → historical（边界非强制）; 但作者必须是加缪
    v = eg.CounterfactualAuthorGuard().check(T2)
    assert v["author"] == "加缪"
    assert v["mode"] in ("historical", "counterfactual")
    assert "question" in v["cues"]


def test_t2_good_answer_passes_interpretation_evaluation():
    ans = ("没有证据表明加缪本人评论过《老人与海》，以下是借其思想框架的推演。"
           "直接判断：两种读法都能成立，但第二种更贴合加缪的文本。"
           "理由一：若把梦狮读作对现实的逃避，它接近加缪批评的'哲学性自杀'——"
           "在希望中自我欺骗【《西西弗斯神话》·荒诞的推理】。"
           "理由二：但加缪的荒诞幸福恰恰是在清醒中热爱有限之物，老人的狮子是记忆而非来世，"
           "更接近后者【《西西弗斯神话》·西西弗斯是幸福的】。"
           "反方：小说本身没有加缪的词汇，也可以质疑海明威未必接受'荒诞'这个标签。"
           "结论：更稳妥的读法是第二种，但它仍是一种读法，并非唯一。")
    r = ev.evaluate_interpretation_quality(T2, ans)
    assert r["findings"] == [], r["findings"]
    assert r["passed"] is True
    r2 = ev.evaluate_epistemic_accuracy(ans)
    assert r2["passed"] is True, r2["findings"]


def test_t2_wire_overclaim_hedged_exactly_once(monkeypatch):
    # 越级断言只补正一次: interpretation 补了, composer 不重复补
    evs, fake = asyncio.run(_run_stream(monkeypatch, T2,
                                        answer="加缪一定会认为这是荒诞幸福，这毫无疑问。"))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "解释型问题" in (m.content or ""))
    assert "至少提出两种" in injected, "T2 必须注入多候选解读要求"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "并非唯一" in text, "越级断言必须被补正"
    assert "强化措辞" not in text, "interpretation 已补正, composer 不得重复补（防双补）"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["composition"]["strong_wording"], "强化措辞仍须检出（审计用）"
    assert done["composition"]["appends"] == [], "解释型问题已补正 → composer 零补正"


# ═══════════════════════════════════════════════════════
# T3 —— 87 天执念: 必须纠正 84 天, 且不破坏主体分析
# ═══════════════════════════════════════════════════════
def test_t3_premise_87_days_detected():
    checks = eg.PremiseVerifier().check(T3)
    ids = [c.get("rule_id") for c in checks]
    assert "oldman_84_days" in ids, f"T3 的 87 天前提必须检出, 实际: {ids}"
    c = next(c for c in checks if c.get("rule_id") == "oldman_84_days")
    assert "84" in c["corrected_value"]
    assert c["nonblocking"] is True   # 先校正, 不拒绝问题


def test_t3_injection_orders_correction_before_answer():
    v = eg.run_epistemic_guards(T3)
    inj = "\n".join(v["injections"])
    assert "87天" in inj and "84" in inj
    assert "先简短纠正" in inj, "注入必须要求先纠正再继续回答"
    assert "不要因此拒绝回答" in inj, "校正不得破坏主体分析（不拒绝、不纠缠）"


def test_t3_interpretation_also_activated():
    v = ie.run_interpretation_engine(T3)
    assert v["activated"] is True
    assert "philosophical_interpretation" in v["categories"]


def test_t3_good_answer_corrects_and_keeps_analysis(monkeypatch):
    good = ("先纠正一个小事实：《老人与海》开篇写的是连续84天没有捕到鱼，不是87天"
            "【《老人与海》·开篇】。回到你的问题：是的，这可以读作他不再向世界索取意义。"
            "首先，老人安然入睡、梦见狮子，是把狮子当作青春的延续而非战利品。"
            "其次，这与加缪的荒诞幸福相通，但也可以质疑，海明威未必接受这一标签。"
            "结论：这是一种有解释力的读法，但并非唯一。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, T3, good))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "84天" in text, "回答必须纠正为 84 天"
    assert "不是87天" in text, "校正须显式否定错误数字（87 只能以否定式出现, 不得作为事实重复）"
    # 主体分析完整: 直接判断 + 理由 + 反方 + 结论都在
    assert "并非唯一" in text and "质疑" in text
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["composition"]["direct_judgment"] is True
    assert done["composition"]["appends"] == [], "纠正并完整分析的回答不得补正"
    # 五维评估: 前提校正落实且不破坏分析
    r = ev.evaluate_premise_accuracy(T3, good)
    assert r["metrics"]["corrected"] == 1 and r["metrics"]["disruptive"] == 0
    assert r["passed"] is True


def test_t3_correction_only_answer_flagged_disruptive(monkeypatch):
    # 只纠正 84 天、丢掉主体分析 → 破坏主体（违反 T3 特别要求）
    bad = "《老人与海》写的是84天。至于梦狮，我不确定。"
    evs, fake = asyncio.run(_run_stream(monkeypatch, T3, bad))
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["composition"]["direct_judgment"] is True
    r = ev.evaluate_premise_accuracy(T3, bad)
    assert r["metrics"]["corrected"] == 1
    assert r["metrics"]["disruptive"] == 1
    assert any(f.startswith("correction_disrupted_analysis") for f in r["findings"])


def test_t3_reasoning_summary_mentions_premise_check(monkeypatch):
    # 无 LLM 摘要 → 确定性推理摘要兜底, 且包含"核验文本事实"（前提校正步骤）
    evs, fake = asyncio.run(_run_stream(monkeypatch, T3,
                                        answer="先纠正：《老人与海》写的是84天。回到问题："
                                               "这可以读作不再向世界索取意义，但并非唯一读法。"))
    summaries = [ev["content"] for ev in evs if ev["type"] == "reasoning_summary"]
    assert summaries and "核验文本事实" in summaries[0]


# ═══════════════════════════════════════════════════════
# Phase S (S1): 84/87 Premise Benchmark 语义化回归（永久保留）
#   84 与 87 都可能正确——判断用户所指事件, 不做简单数字替换。
# ═══════════════════════════════════════════════════════
def test_phase_s_a_opening_87_corrected():
    # A. 开篇当前这次 → 必须纠正为 84 天
    checks = eg.PremiseVerifier().check("小说开头老人已经87天没捕到鱼")
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None and c["referent_mode"] == "current"
    assert "84" in c["corrected_value"]


def test_phase_s_b_historical_87_not_corrected():
    # B. 过去那次经历 → 87 天属实: 只确认, 不得纠正（防 LLM 反向误纠）
    checks = eg.PremiseVerifier().check("老人以前有过87天没捕到鱼的经历")
    assert checks and checks[0]["status"] == "confirmed"
    assert not any(c["status"] == "contradicted" for c in checks)


def test_phase_s_c_ambiguous_distinguished_not_mechanical():
    # C. 歧义 → 区分当前 84 与历史 87, 不得机械纠错
    checks = eg.PremiseVerifier().check("老人从87天的困境到最后安然睡觉，梦见狮子")
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None and c["referent_mode"] == "ambiguous"
    assert "84天" in c["corrected_value"] and "87天" in c["corrected_value"]
    inj = "\n".join(eg.run_epistemic_guards(
        "老人从87天的困境到最后安然睡觉")["injections"])
    assert "存在歧义" in inj or "需要区分" in inj
    assert "不要武断断言" in inj


def test_phase_s_t3_still_current_correction():
    # 既有 T3（"从一开始87天的执念"）语义仍为当前这次 → 纠正不回归
    checks = eg.PremiseVerifier().check(T3)
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None and c["referent_mode"] == "current"
    assert "84" in c["corrected_value"]
