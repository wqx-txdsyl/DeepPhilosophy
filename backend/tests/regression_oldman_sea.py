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

覆盖 2026-08-30 Phase 4 验收项（O4 瘦身后仍适用部分）:
  校正:     T3 检出 87→84（"执念"语境）; 校正不破坏主体分析
            （O4-RP1: PremiseVerifier 随生产 guard 模块删除——检出能力只保留在
            evaluation_suite 离线评分副本; runtime 不再注入"先纠正再回答"directive）
  所有权:   T1/T2/T3 回答由 Main Agent 原样发布——runtime 零注入结构/零补正/零改写
            （O4: interpretation_engine/answer_composer Shadow planner 已删除;
            五维评估中的解释/结构启发式只存在于 evaluation_suite 离线评分器）
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AIMessageChunk

import evaluation_suite as ev
from evaluation_suite import PremiseVerifier
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
    # O4/T5: 回答结构由 Main Agent 自主决定——runtime 不注入"回答结构"指令、
    # 不做结构扫描补正; 结构完整的回答原样发布
    good = ("我的判断是：加缪的荒谬主义在《老人与海》中可以得到印证，但这是借来的框架。"
            "首先，圣地亚哥对抗大马林鱼却不求占有，接近西西弗斯的反抗"
            "【《西西弗斯神话》·荒诞的自由】。其次，狮子是生命力的延续而非来世许诺"
            "【《老人与海》·结尾】。但也可以质疑，海明威未必接受'荒诞'这个标签。"
            "结论：这是一种有解释力的读法，但并非唯一。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, T1, good))
    injected = "".join(m.content for m in fake.captured_messages
                       if m.type == "system" and "回答结构" in (m.content or ""))
    assert injected == "", "composer 结构注入不得回归"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["type"] == "done"
    assert "composition" not in done, "O4: done.composition 已删除"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "（补充：" not in text and "需要补充一句" not in text, "零 runtime 补正"


def test_t1_wire_strong_wording_published_as_is(monkeypatch):
    # O2/O4/T5: 强化措辞的确定性归 Main Agent——runtime 不 hedge/不改写/不追加;
    # 候选通过机械 validator（引用/引文）即原样发布
    bad = ("加缪的荒谬主义本质就是海明威的主题。但并非唯一。"
           "让我先检索一下材料，现在我已经有材料了。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, T1, bad))
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "本质就是" in text, "措辞强度归 Main Agent——正文原样发布"
    assert "（补充：" not in text and "强化措辞" not in text, "零 runtime 补正"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert "composition" not in done
    assert done["final_ownership"]["semantic_mutators"] == 0


# ═══════════════════════════════════════════════════════
# T2 —— 逃避式希望 vs 荒诞幸福
# ═══════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════
# T3 —— 87 天执念: 必须纠正 84 天, 且不破坏主体分析
# ═══════════════════════════════════════════════════════
def test_t3_premise_87_days_detected():
    checks = PremiseVerifier().check(T3)
    ids = [c.get("rule_id") for c in checks]
    assert "oldman_84_days" in ids, f"T3 的 87 天前提必须检出, 实际: {ids}"
    c = next(c for c in checks if c.get("rule_id") == "oldman_84_days")
    assert "84" in c["corrected_value"]
    assert c["nonblocking"] is True   # 检出是事实, 不是拒绝


def test_t3_no_runtime_correction_directive(monkeypatch):
    # O4-RP1: 旧 guard 会对 T3 注入"先简短纠正再继续回答"directive——已删除。
    # 事实由 Main Agent 自主检索核验后自行纠正; runtime 零认知注入
    good = "先纠正一个小事实：《老人与海》开篇写的是连续84天没有捕到鱼，不是87天。其余如常。"
    evs, fake = asyncio.run(_run_stream(monkeypatch, T3, good))
    injected = [m.content for m in fake.captured_messages
                if m.type == "system" and "前提" in (m.content or "")]
    assert injected == [], "runtime 不得替 Agent 下'用户前提错了'的结论（PRE_LLM_FACTUAL_CORRECTION_AUTHORITY=0）"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "84天" in text


def test_t3_good_answer_corrects_and_keeps_analysis(monkeypatch):
    # 注意: 本 harness 无工具轮（raw_tool_log 为空）——正式引用【《书》·章】会被
    # O2 validator 判 UNVERIFIED_CITATION 并拒绝发布（零发布契约, 见 test_phase_s.S4）。
    # 此处用一般提及（不带【】标注）承载同一校正内容。
    good = ("先纠正一个小事实：《老人与海》开篇写的是连续84天没有捕到鱼，不是87天。"
            "回到你的问题：是的，这可以读作他不再向世界索取意义。"
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
    assert "composition" not in done, "O4: 零结构扫描/补正"
    # 五维评估: 前提校正落实且不破坏分析
    r = ev.evaluate_premise_accuracy(T3, good)
    assert r["metrics"]["corrected"] == 1 and r["metrics"]["disruptive"] == 0
    assert r["passed"] is True


def test_t3_correction_only_answer_flagged_disruptive():
    # 只纠正 84 天、丢掉主体分析 → 破坏主体（违反 T3 特别要求）; O4: 纯离线评估
    bad = "《老人与海》写的是84天。至于梦狮，我不确定。"
    r = ev.evaluate_premise_accuracy(T3, bad)
    assert r["metrics"]["corrected"] == 1
    assert r["metrics"]["disruptive"] == 1
    assert any(f.startswith("correction_disrupted_analysis") for f in r["findings"])


# ═══════════════════════════════════════════════════════
# Phase S (S1): 84/87 Premise Benchmark 语义化回归（永久保留）
#   84 与 87 都可能正确——判断用户所指事件, 不做简单数字替换。
# ═══════════════════════════════════════════════════════
def test_phase_s_a_opening_87_corrected():
    # A. 开篇当前这次 → 必须纠正为 84 天
    checks = PremiseVerifier().check("小说开头老人已经87天没捕到鱼")
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None and c["referent_mode"] == "current"
    assert "84" in c["corrected_value"]


def test_phase_s_b_historical_87_not_corrected():
    # B. 过去那次经历 → 87 天属实: 只确认, 不得纠正（防 LLM 反向误纠）
    checks = PremiseVerifier().check("老人以前有过87天没捕到鱼的经历")
    assert checks and checks[0]["status"] == "confirmed"
    assert not any(c["status"] == "contradicted" for c in checks)


def test_phase_s_c_ambiguous_distinguished_not_mechanical():
    # C. 歧义 → 区分当前 84 与历史 87, 不得机械纠错
    checks = PremiseVerifier().check("老人从87天的困境到最后安然睡觉，梦见狮子")
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None and c["referent_mode"] == "ambiguous"
    assert "84天" in c["corrected_value"] and "87天" in c["corrected_value"]
    # O4-RP1: 歧义辨析是评分层的知识, runtime 不再注入辨析 directive——
    # 由 Main Agent 自主判断并区分（行为契约见 test_o4_cognitive_collapse.TestRP1.R4）
    import engine_langgraph as elg
    import inspect
    code_only = "\n".join(ln for ln in inspect.getsource(elg).splitlines()
                          if not ln.strip().startswith("#"))
    assert "存在歧义" not in code_only and "不要武断断言" not in code_only


def test_phase_s_t3_still_current_correction():
    # 既有 T3（"从一开始87天的执念"）语义仍为当前这次 → 纠正不回归
    checks = PremiseVerifier().check(T3)
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None and c["referent_mode"] == "current"
    assert "84" in c["corrected_value"]
