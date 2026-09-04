# -*- coding: utf-8 -*-
"""Patch 1 纯规则单元测试（Backend Reliability Patch 1: B1/B3/B4/B5/B7）

覆盖: 问题分类/复杂度（B7/B1）、术语核验与措辞约束（B3）、时期检测与路由（B5）、
检索语义状态与充分性（B1）、引用实时核验与内部控制标签剥离（B4）、RationaleParser 防泄漏。
不联网、不调 LLM、不改任何数据。
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

import reasoning_plan as RP  # noqa: E402
import agent_runtime as AR   # noqa: E402
from evidence_contract import LiveCitationSanitizer  # noqa: E402
from engine_langgraph import RationaleParser, _strip_control_tags, _visible_text  # noqa: E402


# ═══════════════════════════════════════════════════════
# B7: 问题类型分类
# ═══════════════════════════════════════════════════════
class TestProblemType:
    def test_t5_term_presence(self):
        assert RP.classify_problem(
            "康德在《判断力批判》里是不是已经明确提出了“无目的的合目的性”这个完整术语？"
        ) == "FACT_VERIFICATION"

    def test_t11_narrow_yesno(self):
        assert RP.classify_problem(
            "只回答一个问题：康德所谓“共通感”是不是民主投票式的多数意见？"
        ) == "FACT_VERIFICATION"

    def test_t12_deep(self):
        assert RP.classify_problem(
            "请做一次深入分析：从“特殊如何归入普遍”这个问题出发，解释为什么《判断力批判》"
            "既是认识论问题，也是美学和目的论问题，并说明黑格尔为什么会认为康德仍没有真正解决这个问题。"
        ) == "DEEP_SYNTHESIS"

    def test_t7_argument(self):
        assert RP.classify_problem(
            "“审美判断人人都可以各有喜好，所以康德所谓审美判断的普遍性是自相矛盾的。”分析这个论证。"
        ) == "ARGUMENT_ANALYSIS"

    def test_t8_socratic(self):
        assert RP.classify_problem(
            "不要直接告诉我答案。用苏格拉底式提问带我自己想明白：为什么康德会认为审美判断既主观又要求普遍同意？"
        ) == "SOCRATIC"

    def test_persona(self):
        assert RP.classify_problem("你怎么看康德？", agent="nietzsche") == "PERSONA_RESPONSE"

    def test_t1_system_question_normal(self):
        # 单解释型体系问题 → 一般解释（深度综合需显式深度线索或长问+多关键词）
        assert RP.classify_problem("《判断力批判》在康德三大批判体系里到底解决了什么问题？") \
            == "CONCEPT_EXPLANATION"

    def test_comparison(self):
        assert RP.classify_problem("比较一下康德和黑格尔对美的看法有什么异同？") == "COMPARISON"

    def test_form_directives_do_not_prescribe_fixed_sections(self):
        # B7: 形态注入不得规定固定编号标题（①②③）或固定五段骨架
        for ptype in ("FACT_VERIFICATION", "CONCEPT_EXPLANATION", "ARGUMENT_ANALYSIS",
                      "COMPARISON", "DEEP_SYNTHESIS", "HISTORICAL_GENEALOGY"):
            d = RP.get_form_directive(ptype, "zh") or ""
            assert "①" not in d and "②" not in d and "③" not in d
            assert "直接判断" not in d.replace("先直接给出", "")


# ═══════════════════════════════════════════════════════
# B1: 复杂度分类 + 检索状态 + 充分性
# ═══════════════════════════════════════════════════════
class TestComplexity:
    def test_narrow(self):
        assert RP.classify_complexity("FACT_VERIFICATION", "是不是这样？") == "NARROW_FACTUAL"

    def test_deep(self):
        assert RP.classify_complexity("DEEP_SYNTHESIS", "深入分析……") == "DEEP_SYNTHESIS"

    def test_comparison(self):
        assert RP.classify_complexity("COMPARISON", "比较A与B") == "COMPARISON"


class TestRetrievalState:
    def _search_result(self, book_ids, chapter=0):
        return {"results": [{"book_title": f"书{i}", "book_id": bid, "chapter_idx": chapter,
                             "snippet": f"片段{i}含关键词"} for i, bid in enumerate(book_ids)]}

    def test_new_and_low_gain(self):
        rs = AR.RetrievalState()
        r1 = rs.register("search_books", {"query": "共通感"}, self._search_result(["a", "b", "c"]))
        assert r1["low_gain"] is False and r1["new"] == 3
        # 完全同源 → low_gain
        r2 = rs.register("search_books", {"query": "共通感 审美"}, self._search_result(["a", "b", "c"]))
        assert r2["low_gain"] is True and r2["new"] == 0
        # 高度重合（4 源中仅 1 新）→ low_gain
        r3 = rs.register("search_books", {"query": "共通感 判断力"}, self._search_result(["a", "b", "c", "d"]))
        assert r3["low_gain"] is True and r3["new"] == 1

    def test_relevant_sources(self):
        rs = AR.RetrievalState()
        rs.register("search_books", {"query": "共通感"}, self._search_result(["a"]), key_terms=["关键词"])
        assert len(rs.relevant_ids) == 1
        # 无关键术语命中 → 检索无信息增益（low_gain）
        rs2 = AR.RetrievalState()
        r = rs2.register("search_books", {"query": "共通感"}, self._search_result(["a", "b"]),
                         key_terms=["不存在的词"])
        assert r["low_gain"] is True

    def test_get_chapter_never_low_gain(self):
        rs = AR.RetrievalState()
        r = rs.register("get_chapter", {"book_id": "x", "chapter_idx": 1},
                        {"book_id": "x", "chapter_idx": 1, "text": "正文"}, key_terms=["关键词"])
        assert r["low_gain"] is False  # 阅读类工具豁免（逐字核验途径）


class TestSufficiency:
    def test_narrow_factual_force_after_hi(self):
        # 窄事实: 期望 1-3——收口点 max(1, 3-2)=1, 首个工具轮后即收口
        assert AR.sufficiency_verdict("NARROW_FACTUAL", 3, True, 1, True) == "force"
        assert AR.sufficiency_verdict("NARROW_FACTUAL", 2, True, 1, True) == "force"
        assert AR.sufficiency_verdict("NARROW_FACTUAL", 1, True, 0, False) == "force"
        assert AR.sufficiency_verdict("NARROW_FACTUAL", 2, False, 1, True,
                                      round_any_low=True) == "force"
        assert AR.sufficiency_verdict("NARROW_FACTUAL", 2, False, 1, True) == "force"
        assert AR.sufficiency_verdict("NARROW_FACTUAL", 0, False, 0, False) == "none"

    def test_deep_allows_more(self):
        # 深度综合: 期望 5-10——收口点 max(5, 8)=8; 低增益不提前收口
        assert AR.sufficiency_verdict("DEEP_SYNTHESIS", 5, True, 2, False, round_any_low=True) == "none"
        assert AR.sufficiency_verdict("DEEP_SYNTHESIS", 7, True, 2, False) == "none"
        assert AR.sufficiency_verdict("DEEP_SYNTHESIS", 8, True, 2, False) == "force"
        assert AR.sufficiency_verdict("DEEP_SYNTHESIS", 11, False, 2, False) == "force"

    def test_hint_text(self):
        h = AR.sufficiency_hint("force", "NARROW_FACTUAL", "zh")
        assert h and "检索已充分" in h and "禁止调用任何工具" in h


# ═══════════════════════════════════════════════════════
# B3: 术语核验
# ═══════════════════════════════════════════════════════
class TestTermVerification:
    def test_detect(self):
        assert RP.detect_term_presence("是否明确提出了“无目的的合目的性”这个完整术语？")["term"] == "无目的的合目的性"
        assert RP.detect_term_presence("“共通感”是不是民主投票？") is None  # 无术语核验线索

    def test_exact(self):
        log = [{"name": "get_chapter", "result_full": {"book_id": "x", "text": "……无目的的合目的性……"}}]
        v = RP.verify_term_presence("无目的的合目的性", log)
        assert v["state"] == "VERIFIED_EXACT"

    def test_semantic(self):
        log = [{"name": "get_chapter",
                "result_full": {"book_id": "x", "text": "……无目的的愉悦与合目的性的形式……"}}]
        v = RP.verify_term_presence("无目的的合目的性", log)
        assert v["state"] == "VERIFIED_SEMANTIC"

    def test_not_found(self):
        log = [{"name": "search_books",
                "result_full": {"results": [{"book_title": "书", "snippet": "合目的性是反思判断力的原则"}]}}]
        v = RP.verify_term_presence("无目的的合目的性", log)
        assert v["state"] == "NOT_FOUND"

    def test_constrain_unconditional(self):
        s = "可以确认——康德已经完整提出了这一命题。"
        out = RP.constrain_unconditional_claim(s, "NOT_FOUND")
        assert "未能核验" in out and "完整提出" not in out
        # EXACT 状态不改写
        assert RP.constrain_unconditional_claim(s, "VERIFIED_EXACT") == s

    def test_gate_holds_only_term_sentence(self):
        gate = RP.TermClaimGate("术语X", lambda s: RP.constrain_unconditional_claim(s, "NOT_FOUND"))
        assert gate.push("不含术语的句子。") == "不含术语的句子。"
        # 含术语但句界未到 → 缓冲（不返回）
        assert gate.push("这里说“已经完整提出了术语X”然后继续") == ""
        # 句界到达 → 受约束改写, 此后全部放行
        out = gate.push("。")
        assert "未能核验" in out and "完整提出" not in out
        assert gate.push("第二句。") == "第二句。"
        # 约束只发生一次（激活即关闭）
        gate2 = RP.TermClaimGate("术语X", lambda s: RP.constrain_unconditional_claim(s, "NOT_FOUND"))
        assert gate2.push("已经完整提出了术语X。") != ""
        assert gate2.push("又已经完整提出了术语X。") == "又已经完整提出了术语X。"

    def test_constrain_absorbs_object(self):
        out = RP.constrain_unconditional_claim(
            "可以确认——康德已经完整提出了“无目的的合目的性”这一完整命题。", "NOT_FOUND")
        assert "完整提出" not in out and "未能核验" in out and "这一完整命题" not in out


# ═══════════════════════════════════════════════════════
# B5: 时期检测与路由
# ═══════════════════════════════════════════════════════
class TestTemporal:
    def test_detect(self):
        t = RP.detect_temporal("1872年的你和1888年的你，会怎样分别评价康德的“无利害审美”？")
        assert t["detected"] and t["years"] == [1872, 1888]

    def test_detect_words(self):
        assert RP.detect_temporal("你早期的想法和晚期有什么不同？")["detected"]

    def test_year_to_period(self):
        assert RP.year_to_period("nietzsche", 1872) == "early"
        assert RP.year_to_period("nietzsche", 1888) == "late"
        assert RP.year_to_period("nietzsche", 1880) == "middle"

    def test_directive_requires_period_tool(self):
        d = RP.temporal_directive("nietzsche", {"years": [1872, 1888]}, "zh")
        assert "philosopher_period" in d and "1872年→early" in d and "1888年→late" in d


# ═══════════════════════════════════════════════════════
# B4: 引用实时核验 + 控制标签剥离
# ═══════════════════════════════════════════════════════
class TestLiveCitationSanitizer:
    def _log(self):
        return [{"name": "search_books", "args": {"query": "x"},
                 "result_full": {"results": [
                     {"book_title": "判断力批判", "author": "康德", "chapter_idx": 3,
                      "chapter_title": "第一卷 审美判断力的分析论",
                      "snippet": "鉴赏判断并不是认识判断"}]}},
                {"name": "get_chapter", "args": {}, "result_full": {
                    "book_id": "f08c1ead3164", "chapter_idx": 4, "title": "第二卷 审美判断力的辩证论",
                    "text": "55.鉴赏的二律背反"}}]

    def test_verified_kept(self):
        s = LiveCitationSanitizer(self._log())
        out = s.push("康德说【《判断力批判》· 第一卷 审美判断力的分析论】如此。")
        assert "【《判断力批判》· 第一卷 审美判断力的分析论】" in out
        assert s.verified == 1 and s.downgraded == 0

    def test_unverified_downgraded(self):
        s = LiveCitationSanitizer(self._log())
        out = s.push("康德说【《判断力批判》·§55】如此。")
        assert "【" not in out and "《判断力批判》" in out and s.downgraded == 1

    def test_partial_marker_held(self):
        s = LiveCitationSanitizer(self._log())
        assert s.push("开头【《判断力批判》") == "开头"      # 未闭合标记缓冲
        out = s.push("· 第二卷 审美判断力的辩证论】正文")
        assert "【《判断力批判》· 第二卷 审美判断力的辩证论】" in out
        assert out.endswith("正文")
        assert s.flush() == ""

    def test_no_disclosure_footnote(self):
        # B4-B: 净化不得产生"引用核验说明"补丁尾注
        s = LiveCitationSanitizer(self._log())
        out = s.push("正文【《不存在的书》·第1章】内容。")
        assert "引用核验说明" not in out and "【" not in out


class TestControlTags:
    def test_complete_pair_removed(self):
        assert _strip_control_tags("<rationale>内部思考</rationale>回答正文") == "回答正文"

    def test_stray_tag_removed(self):
        assert _strip_control_tags("正文</rationale>继续") == "正文继续"

    def test_visible_text(self):
        assert _visible_text("<tool_calls><invoke name='x'></invoke></tool_calls><rationale>r</rationale>正文") == "正文"

    def test_parser_unclosed_release_stripped(self):
        # B4-A 回归: 未闭合 <rationale> 经 finish() 释放后不得携带标签
        p = RationaleParser()
        p.push("前半段回答。")
        p.push("<rationale>未闭合的思考说明")
        tail = _strip_control_tags(p.finish())
        assert "<rationale>" not in tail and "未闭合的思考说明" in tail

    def test_parser_complete_pair(self):
        p = RationaleParser()
        out, rats = p.push("<rationale>说明</rationale>正文")
        assert out == "正文" and rats == ["说明"]
        assert p.finish() == ""
