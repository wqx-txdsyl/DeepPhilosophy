# -*- coding: utf-8 -*-
"""Patch 1 纯规则单元测试（Backend Reliability Patch 1: B1/B3/B4/B5/B7）

覆盖: 术语核验与措辞约束（B3）、时期检测与路由（B5）、
引用核验（B4, O2 后为 final_validator 结构化校验）与内部控制标签剥离、RationaleParser 防泄漏。
O4 Cognitive Layer Collapse: 问题类型分类（B7）/复杂度档位（B1）/RetrievalState 语义增益/
sufficiency 收敛已随 Shadow planner 删除——相关用例移除, 行为契约由 test_o4_cognitive_collapse 覆盖。
不联网、不调 LLM、不改任何数据。
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

import reasoning_plan as RP  # noqa: E402
import agent_runtime as AR   # noqa: E402
import final_validator as FV  # noqa: E402
from engine_langgraph import RationaleParser, _strip_control_tags, _visible_text  # noqa: E402


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

    def test_unverified_wording_constrained_at_prompt_layer(self):
        # O2 改写: 旧 constrain_unconditional_claim（runtime 句界改写）已删除——
        # NOT_FOUND 状态改为 prompt 层措辞约束注入, 由 Main Agent 自己如实表述
        assert not hasattr(RP, "constrain_unconditional_claim"), "runtime 句子改写不得回归"
        inj = RP.verification_injection({"state": "NOT_FOUND", "term": "无目的的合目的性"})
        assert inj and "不得无条件肯定" in inj and "不能确认" in inj
        # EXACT 状态允许明确措辞（不约束）
        inj_ok = RP.verification_injection({"state": "VERIFIED_EXACT", "term": "无目的的合目的性"})
        assert "逐字命中" in inj_ok and "不得" not in inj_ok

    def test_term_claim_gate_removed_not_runtime(self):
        # O2 改写: 旧 TermClaimGate（流式句界改写门）已删除——未核验对象的措辞
        # 约束只能经 prompt 注入, 引擎正文通道零改写
        assert not hasattr(RP, "TermClaimGate"), "流式句子改写门不得回归"
        # 正文通道仅做机械净化（控制标签/内部措辞剥离）, 不改写术语句
        s = "可以确认——康德已经完整提出了无目的的合目的性。"
        assert _visible_text(s) == s


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
# B4 (O2 改写): 引用核验——LiveCitationSanitizer 流式降级已删除,
# 替代为 final_validator.check_citations 结构化校验（检测, 绝不改写）
# ═══════════════════════════════════════════════════════
class TestFinalCitationValidation:
    def _log(self):
        return [{"name": "search_books", "args": {"query": "x"},
                 "result_full": {"results": [
                     {"book_title": "判断力批判", "author": "康德", "chapter_idx": 3,
                      "chapter_title": "第一卷 审美判断力的分析论",
                      "snippet": "鉴赏判断并不是认识判断"}]}},
                {"name": "get_chapter", "args": {}, "result_full": {
                    "book_id": "f08c1ead3164", "chapter_idx": 4, "title": "第二卷 审美判断力的辩证论",
                    "text": "55.鉴赏的二律背反"}}]

    def test_verified_counted_no_issue_text_untouched(self):
        ans = "康德说【《判断力批判》· 第一卷 审美判断力的分析论】如此。"
        verified, issues = FV.check_citations(ans, self._log())
        assert verified == 1 and issues == []
        # validator 只检测——正文原样（verified 引用保留在文本中）
        assert "【《判断力批判》· 第一卷 审美判断力的分析论】" in ans

    def test_unverified_reported_not_downgraded(self):
        # 旧契约（未核验引用流式降级为《书》一般提及）已废除——
        # 现在返回 UNVERIFIED_CITATION issue, 正文文本绝不被修改
        ans = "康德说【《判断力批判》·§55】如此。"
        verified, issues = FV.check_citations(ans, self._log())
        assert verified == 0
        assert [i.code for i in issues] == [FV.UNVERIFIED_CITATION]
        assert issues[0].locator == "【《判断力批判》·§55】"
        assert "【《判断力批判》·§55】" in ans and "【" in ans

    def test_partial_marker_held_no_longer_streaming_concern(self):
        # 旧"未闭合标记流式缓冲"属 sanitizer 渲染职责, 已随类删除——
        # validator 只对完整候选工作, 半截标记不再是特殊对象（机械原样检测）
        ans = "开头【《判断力批判"
        verified, issues = FV.check_citations(ans, self._log())
        assert ans == "开头【《判断力批判"   # 文本零改动

    def test_feedback_is_structured_not_text_patch(self):
        # B4-B 回归（新契约）: 未核验引用处理 = 结构化 issue 反馈给 Main Agent,
        # 绝不产生"引用核验说明"式补丁尾注追加进正文
        ans = "正文【《不存在的书》·第1章】内容。"
        verified, issues = FV.check_citations(ans, self._log())
        assert verified == 0 and issues
        fb = FV.format_feedback(FV.ValidationResult(ok=False, issues=issues))
        assert FV.UNVERIFIED_CITATION in fb and "引用核验说明" not in fb
        assert ans.endswith("内容。")   # 原文原样——无尾注追加

    def test_validate_final_candidate_gate(self):
        # 总入口: 全部引用已核验 → PASS; 含未核验引用 → FAIL（发布前拦截）
        log = self._log()
        ok_ans = "康德说【《判断力批判》· 第一卷 审美判断力的分析论】如此。"
        assert FV.validate_final_candidate(ok_ans, raw_tool_log=log).ok is True
        bad_ans = "康德说【《判断力批判》·§55】如此。"
        res = FV.validate_final_candidate(bad_ans, raw_tool_log=log)
        assert res.ok is False
        assert any(i.code == FV.UNVERIFIED_CITATION for i in res.issues)


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
