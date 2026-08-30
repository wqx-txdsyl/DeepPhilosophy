# -*- coding: utf-8 -*-
"""Evaluation Suite（Phase 4）用例——回答质量五维评分（纯规则, 不调 LLM）

覆盖 2026-08-30 Phase 4 验收项:
  Premise Accuracy:    错误数字（87→84）/ 错误作者（《存在与时间》尼采）/ 错误书名（《西西弗斯》）/
                       错误年代（《反抗者》1942）/ 错误概念归属（权力意志→叔本华）
  Epistemic Accuracy:  fact/quote/inference/interpretation/counterfactual/speculation 区分;
                       overclaim / counterfactual_unbounded / quote_unlocatable 检出
  Interpretation:      confirmation bias（单候选）/ alternative explanation / cross-framework overreach
  Evidence:            citation validity / used rate / unsupported claim rate
  Answer UX:           directness / redundancy / reasoning noise
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import evaluation_suite as ev
from epistemic_guard import PremiseVerifier


# ═══════════════════════════════════════════════════════
# 1. Premise Accuracy —— 五类错误前提
# ═══════════════════════════════════════════════════════
def test_premise_wrong_number_87_to_84():
    q = "老人从一开始87天的执念到了最后安然睡觉，梦见狮子，是不是恰是他不再向世界索取意义？"
    ans = ("先纠正：《老人与海》开篇写的是连续84天没有捕到鱼，不是87天。回到你的问题："
           "是的，这可以读作不再向世界索取意义——梦狮是对生命力的依恋而非索取，"
           "但并非唯一读法。")
    r = ev.evaluate_premise_accuracy(q, ans)
    assert r["metrics"]["detected"] == 1
    assert r["metrics"]["categories"].get("wrong_number") == ["oldman_84_days"]
    assert r["metrics"]["corrected"] == 1 and r["metrics"]["disruptive"] == 0
    assert r["passed"] is True


def test_premise_correction_must_not_break_analysis():
    q = "老人从一开始87天的执念到了最后安然睡觉，梦见狮子，是不是恰是他不再向世界索取意义？"
    # 只纠正 84 天却丢掉主体分析 → disruptive
    r = ev.evaluate_premise_accuracy(q, "《老人与海》写的是84天。")
    assert r["metrics"]["corrected"] == 1
    assert r["metrics"]["disruptive"] == 1
    assert r["passed"] is False
    assert any(f.startswith("correction_disrupted_analysis") for f in r["findings"])


def test_premise_wrong_author():
    q = "《存在与时间》里尼采认为人是向死而生的"
    ans = ("《存在与时间》的作者是海德格尔，不是尼采。向死而生是海德格尔的概念（《存在与时间》），"
           "尼采关心的是永恒轮回等不同的问题。海德格尔在书中以此在为中心展开生存论分析，"
           "这与尼采的权力意志是两条不同的哲学路线。")
    r = ev.evaluate_premise_accuracy(q, ans)
    cats = r["metrics"]["categories"]
    assert "wrong_author" in cats, f"应检出错误作者, 实际: {cats}"
    assert r["metrics"]["corrected"] >= 1
    assert r["passed"] is True


def test_premise_wrong_book_title():
    q = "加缪在《西西弗斯》里提出了荒诞的三个特征"
    ans = ("加缪这部随笔的全名是《西西弗斯神话》。在《西西弗斯神话》中，荒诞产生于"
           "人向世界索要意义而世界沉默的裂隙，加缪随后给出反抗的回答。"
           "这部书写于1942年，与《局外人》同年问世。")
    r = ev.evaluate_premise_accuracy(q, ans)
    cats = r["metrics"]["categories"]
    assert cats.get("wrong_book_title") == ["title:book_sisyphus_full_title"]
    assert r["metrics"]["corrected"] == 1
    assert r["passed"] is True


def test_premise_wrong_era():
    q = "加缪1942年写《反抗者》"
    ans = ("《反抗者》写于1951年，1942年是《西西弗斯神话》和《局外人》的年代。"
           "加缪在1951年完成这部随笔，随后与萨特在《现代》杂志上展开那场著名的论战，"
           "两人最终因立场分歧而决裂。")
    r = ev.evaluate_premise_accuracy(q, ans)
    assert r["metrics"]["categories"].get("wrong_era") == ["rebel_1951"]
    assert r["metrics"]["corrected"] == 1
    assert r["passed"] is True


def test_premise_wrong_concept_attribution():
    q = "叔本华提出了权力意志"
    ans = ("权力意志是尼采的核心概念，不是叔本华。叔本华的核心概念是生存意志"
           "（Wille zum Leben）。尼采在《查拉图斯特拉如是说》等书中把权力意志发展为"
           "对生命自我超越的肯定。")
    r = ev.evaluate_premise_accuracy(q, ans)
    cats = r["metrics"]["categories"]
    assert cats.get("wrong_concept_attribution") == ["concept:concept_will_to_power"]
    assert r["metrics"]["corrected"] == 1
    assert r["passed"] is True


def test_premise_no_error_passes():
    r = ev.evaluate_premise_accuracy("什么是荒诞？", "荒诞是理性与世界之间的裂隙。")
    assert r["metrics"]["detected"] == 0
    assert r["passed"] is True and r["score"] == 1.0


# ═══════════════════════════════════════════════════════
# 2. Epistemic Accuracy —— 六类区分与措辞一致性
# ═══════════════════════════════════════════════════════
def test_epistemic_overclaim_detected():
    r = ev.evaluate_epistemic_accuracy("老人一定完成了从外部意义到内部意义的转变")
    assert any(f.startswith("overclaim_unhedged") for f in r["findings"])
    assert r["passed"] is False


def test_epistemic_counterfactual_unbounded():
    r = ev.evaluate_epistemic_accuracy("加缪一定会认为老人梦狮是荒诞幸福")
    assert any(f.startswith("counterfactual_unbounded") for f in r["findings"])
    assert r["passed"] is False
    # 有边界 → 不报
    r2 = ev.evaluate_epistemic_accuracy(
        "没有证据表明加缪本人评论过《老人与海》；推演来看，他或许会把梦狮读作荒诞幸福")
    assert not any(f.startswith("counterfactual_unbounded") for f in r2["findings"])


def test_epistemic_quote_unlocatable():
    r = ev.evaluate_epistemic_accuracy("原文写道：人是应当被超越的")
    assert any(f.startswith("quote_unlocatable") for f in r["findings"])


def test_epistemic_six_types_distinguished():
    ans = ("文本明确写道：荒诞在于人与世界的裂隙【《西西弗斯神话》·开篇】。"
           "原文写道：“人是应当被超越的”【《查拉图斯特拉如是说》·前言·4】。"
           "这可以理解为一种召唤。或许，它也是对现代人的批评。")
    r = ev.evaluate_epistemic_accuracy(ans)
    types = r["metrics"]["claim_types"]
    # fact / quote / inference / speculation 至少四种被区分
    assert types.get("SOURCE_FACT", 0) >= 1
    assert types.get("DIRECT_QUOTE", 0) >= 1
    assert types.get("TEXTUAL_INFERENCE", 0) >= 1 or types.get("SPECULATION", 0) >= 1
    assert r["passed"] is True, r["findings"]


def test_epistemic_hedge_contradiction():
    r = ev.evaluate_epistemic_accuracy("或许他一定是对的")
    assert any(f.startswith("hedge_contradiction") for f in r["findings"])


# ═══════════════════════════════════════════════════════
# 3. Interpretation Quality —— bias / alternative / overreach
# ═══════════════════════════════════════════════════════
T2 = "加缪会不会认为老人梦见狮子是一种逃避式希望，还是恰恰证明荒诞幸福？"


def test_interpretation_confirmation_bias_detected():
    r = ev.evaluate_interpretation_quality(T2, "老人梦狮象征着荒诞幸福的证明。")
    assert "confirmation_bias" in r["findings"]
    assert r["passed"] is False


def test_interpretation_alternative_explanation_passes():
    ans = ("一种读法是逃避式希望，另一种读法是荒诞幸福，后者更贴合加缪的文本；"
           "但也可以质疑，海明威未必接受这个标签。结论：这是可成立但并非唯一的读法。")
    r = ev.evaluate_interpretation_quality(T2, ans)
    assert r["metrics"]["alternatives_offered"] is True
    assert r["findings"] == [], r["findings"]
    assert r["passed"] is True


def test_interpretation_cross_framework_overreach():
    r = ev.evaluate_interpretation_quality(
        "尼采的超人和庄子的逍遥是不是一回事？",
        "超人和逍遥本质上完全一样，都是对无限自由的向往。")
    assert "cross_framework_overreach" in r["findings"]
    assert r["passed"] is False


def test_interpretation_not_activated_passes():
    r = ev.evaluate_interpretation_quality("什么是虚无主义？", "虚无主义是价值真空的状态。")
    assert r["metrics"]["activated"] is False
    assert r["passed"] is True


# ═══════════════════════════════════════════════════════
# 4. Evidence —— citation validity / used rate / unsupported rate
# ═══════════════════════════════════════════════════════
def _hit(book, chapter, book_id, idx=0, snippet="加缪在第1段写道: 荒诞在于把意义强加给世界。"):
    return {"book_id": book_id, "book_title": book, "author": "加缪",
            "chapter_idx": idx, "chapter_title": chapter, "snippet": snippet, "score": 0.9}


def _search_tool(results):
    return {"name": "search_books", "args": {"query": "t"}, "result_summary": "",
            "result_full": {"results": results, "query": "t"}}


def test_evidence_unverified_citation_flagged():
    hits = [_hit("西西弗斯神话", "开篇", "b1")]
    ans = ("荒诞是加缪的命题【《西西弗斯神话》·开篇】；而另一个世界是柏拉图的地图【《理想国》·卷十】。")
    r = ev.evaluate_evidence(ans, tool_log=[_search_tool(hits)])
    assert any(f == "unverified_citation:理想国" for f in r["findings"])
    assert r["metrics"]["unverified_count"] == 1
    assert r["passed"] is False


def test_evidence_used_rate_low_flagged():
    hits = [_hit("西西弗斯神话", f"第{i}节", f"b{i}", idx=i) for i in range(20)]
    ans = "荒诞是加缪的核心命题【《西西弗斯神话》·第1节】。"
    r = ev.evaluate_evidence(ans, tool_log=[_search_tool(hits)])
    assert r["metrics"]["used_rate"] == 0.05
    assert "low_used_rate" in r["findings"]


def test_evidence_unsupported_claims_flagged():
    hits = [_hit("西西弗斯神话", "开篇", "b1", snippet="另一个完全无关的段落内容")]
    ans = "文本明确写道：荒诞在于人与世界的裂隙。这意味着反抗是唯一的出路。"
    r = ev.evaluate_evidence(ans, tool_log=[_search_tool(hits)])
    assert r["metrics"]["unsupported_rate"] > 0.5
    assert "unsupported_claims" in r["findings"]
    assert r["passed"] is False


def test_evidence_good_answer_passes():
    hits = [_hit("西西弗斯神话", "开篇", "b1", snippet="荒诞在于把意义强加给世界。"),
            _hit("老人与海", "结尾", "b2", idx=3, snippet="老人正梦见狮子。")]
    ans = ("荒诞是加缪的核心命题【《西西弗斯神话》·开篇】；老人的梦狮呼应这一主题"
           "【《老人与海》·结尾】。")
    r = ev.evaluate_evidence(ans, tool_log=[_search_tool(hits)])
    assert r["metrics"]["unverified_count"] == 0
    assert r["metrics"]["used_rate"] == 1.0
    assert r["passed"] is True


# ═══════════════════════════════════════════════════════
# 5. Answer UX —— directness / redundancy / reasoning noise
# ═══════════════════════════════════════════════════════
def test_ux_process_leadin_flagged():
    r = ev.evaluate_answer_ux("让我先检索一下材料，然后再说明。")
    assert "process_leadin" in r["findings"]
    assert r["passed"] is False


def test_ux_reasoning_noise_flagged():
    r = ev.evaluate_answer_ux("我已经有材料了，现在开始。")
    assert any(f.startswith("reasoning_noise") for f in r["findings"])


def test_ux_default_block_flagged():
    r = ev.evaluate_answer_ux("材料说明：我找到了三本书。检索过程：先查了开篇。再总结：完毕。")
    assert any(f.startswith("default_block") for f in r["findings"])


def test_ux_redundancy_flagged():
    r = ev.evaluate_answer_ux("荒诞是理性与世界的裂隙。荒诞是理性与世界的裂隙。综上总之结论是荒诞。")
    assert any(f.startswith("redundancy") for f in r["findings"])


def test_ux_good_answer_passes():
    ans = ("我的判断是：可以用加缪的框架读《老人与海》。首先，老人与大鱼对峙却不求占有，"
           "接近西西弗斯的反抗【《西西弗斯神话》·荒诞的自由】。但也要指出，海明威未必接受"
           "'荒诞'这一标签。结论：这是一种有解释力的读法，但并非唯一。")
    r = ev.evaluate_answer_ux(ans)
    assert r["metrics"]["direct_judgment"] is True
    assert r["passed"] is True, r["findings"]


# ═══════════════════════════════════════════════════════
# 6. 汇总: evaluate_answer
# ═══════════════════════════════════════════════════════
def test_evaluate_answer_good_composed_answer():
    q = "从《老人与海》看加缪的荒谬主义。"
    ans = ("我的判断是：加缪的荒谬主义在《老人与海》中可以得到印证，但这是借来的框架，"
           "不是海明威明写的主题。首先，圣地亚哥对抗大马林鱼却不求占有，接近西西弗斯的反抗"
           "【《西西弗斯神话》·荒诞的自由】。其次，梦中的狮子是生命力的延续而非来世许诺"
           "【《老人与海》·结尾】。但也可以质疑：海明威未必接受'荒诞'这个标签。"
           "结论：这是一种有解释力的读法，但并非唯一。")
    hits = [_hit("西西弗斯神话", "荒诞的自由", "b1"),
            _hit("老人与海", "结尾", "b2", idx=3, snippet="老人正梦见狮子。")]
    r = ev.evaluate_answer(q, ans, tool_log=[_search_tool(hits)])
    for dim in ("premise", "epistemic", "interpretation", "evidence", "ux"):
        assert r[dim]["passed"] is True, f"{dim}: {r[dim]['findings']}"
    assert r["passed_all"] is True
    assert r["overall"] == 1.0


def test_evaluate_answer_bad_answer_fails_dimensions():
    q = "从《老人与海》看加缪的荒谬主义。"
    ans = ("让我先检索一下材料。现在我已经有材料了。材料说明：我找到了三本书。"
           "再总结：加缪的荒谬主义本质上就是海明威的主题，这毫无疑问。")
    r = ev.evaluate_answer(q, ans)
    assert r["passed_all"] is False
    assert not r["ux"]["passed"]
    assert not r["epistemic"]["passed"]


def test_evaluate_answer_never_raises_on_garbage():
    for q, a in [("", ""), (None, None), ("《" * 50, "a" * 5000)]:
        r = ev.evaluate_answer(q or "", a or "")
        assert isinstance(r["overall"], float)
