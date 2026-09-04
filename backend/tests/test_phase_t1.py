# -*- coding: utf-8 -*-
"""Phase T.1 — Source Attribution / Quote Verification Regression Hotfix（T1.1-A~H）

对应真实回归: "言必有中出处" → 模型凭记忆给 blockquote（甚至拼接相邻章句）+
"未经库中核验" 免责 + "如果你需要我可以再读"反模式。

本文件只测确定性规则层（不调 LLM）:
  T1.1-A  SOURCE_ATTRIBUTION 检测（裸「X出处」词型/term 兜底）+ 事实三态分层
          （O4: 义务满足总闸已删——只剩 LOCATED/READ/QUOTE_VERIFIED 执行事实）
  T1.1-B  locate_exact_phrase 逐字定位 + _ensure_primary_read 兜底读取
  T1.1-D  Quote Bound: 提取/核验状态（O2: 流式渲染转写已删——audit + validator issue）
  T1.1-E  MEMORY_HINT ≠ EVIDENCE（检索命中不置位 primary_text_read）
  T1.1-F  相邻章句拼接防护（跨 span 连续性校验）
  T1.1-G/H 收口一致性（O2: 强确定性降调已删; verify-later 矛盾 → validator issue;
          O4: 仅由 primary_text_read 事实触发）
O4: T1.1-C（read 配额/准入拒绝措辞）已随检索准入机制删除。
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent_runtime as AR
import quote_bound as QB
import final_validator as FV
import reasoning_plan as RP


# ═══════════════════════════════════════════════════════
# T1.1-A 检测
# ═══════════════════════════════════════════════════════
class TestT11ADetection:
    def test_r1_bare_chuchu(self):
        # 真实回归句: 旧正则不命中 → vi=None → 核验路径整体缺席
        vi = RP.detect_verification_intent("言必有中出处")
        assert vi is not None
        assert vi["kind"] in ("SOURCE_ATTRIBUTION", "EXACT_WORDING")
        assert vi["term"] == "言必有中"

    def test_r2_r3_r4_r5_r6(self):
        vi2 = RP.detect_verification_intent("“过犹不及”出自哪里？给原文上下文。")
        assert vi2 and vi2["term"] == "过犹不及"
        vi3 = RP.detect_verification_intent("“己所不欲，勿施于人”在《论语》哪一篇？原文是什么？")
        assert vi3 and vi3["kind"] == "EXACT_WORDING"
        vi4 = RP.detect_verification_intent("“天行健，君子以自强不息”是不是《论语》里的？")
        assert vi4 and vi4["kind"] == "SOURCE_ATTRIBUTION"
        assert vi4["term"] == "天行健，君子以自强不息"
        vi5 = RP.detect_verification_intent("“知我者谓我心忧，不知我者谓我何求”出处")
        assert vi5 and "知我者谓我心忧" in vi5["term"]
        vi6 = RP.detect_verification_intent("“民为贵，社稷次之，君为轻”是不是孟子原话？")
        assert vi6 and vi6["kind"] == "EXACT_WORDING"

    def test_non_verification_untouched(self):
        assert RP.detect_verification_intent("比较康德和黑格尔的美学") is None
        assert RP.detect_verification_intent("什么是休谟的归纳问题？") is None

    def test_plan_routed_to_verification_family(self):
        plan = RP.build_plan("言必有中出处")
        # O4: problem_type/complexity 认知分类已删——plan 只剩核验意图元数据
        assert "problem_type" not in plan and "complexity" not in plan
        assert plan["verification_intent"]["term"] == "言必有中"
        # T1.1-B/E/H: 核验纪律注入必须存在
        assert any("出处核验纪律" in inj for inj in plan["injections"])

    def test_ledger_three_state_layering(self):
        led = AR.ObligationLedger(term="言必有中")
        # 检索命中 → 只置位 SOURCE_CANDIDATE_FOUND（MEMORY_HINT, T1.1-E）
        led.record("search_books", {"query": "言必有中"}, True,
                   {"results": [{"book_id": "d927", "chapter_idx": 12}]})
        assert led.source_candidate_found
        assert not led.primary_text_read
        # get_chapter 全文命中 → READ + EXACT
        led.record("get_chapter", {"book_id": "d927", "chapter_idx": 12}, True,
                   {"book_id": "d927", "chapter_idx": 12,
                    "text": "鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”子曰：“夫人不言，言必有中。”"})
        assert led.primary_text_read
        assert led.exact_quote_verified
        snap = led.snapshot()["verification_states"]
        assert snap["source_candidate_found"] and snap["primary_text_read"]
        assert snap["exact_quote_verified"]

    def test_read_without_term_hit_stays_unverified(self):
        # R7 型: 读到了章节但表述不在其中 → 已读但未逐字命中（诚实 NOT_FOUND 路径）
        led = AR.ObligationLedger(term="青天揽月寸心如磐")
        led.record("get_chapter", {"book_id": "x", "chapter_idx": 1}, True,
                   {"book_id": "x", "chapter_idx": 1, "text": "子曰：学而时习之，不亦说乎。"})
        assert led.primary_text_read
        assert not led.exact_quote_verified


# ═══════════════════════════════════════════════════════
# T1.1-B 逐字定位（真实语料; 冷扫描 ~9s 进程级缓存）
# ═══════════════════════════════════════════════════════
class TestT11BLocate:
    def test_locate_yan_bi_you_zhong(self):
        from routes.agent_tools_retrieval import locate_exact_phrase
        r = locate_exact_phrase("言必有中")
        assert r["found"]
        top = r["hits"][0]
        assert top["book_title"] == "论语"
        assert top["chapter_title"] == "先进篇"
        assert "鲁人为长府" in top["passage"] and "言必有中" in top["passage"]
        # 正确 passage（PASSAGE_B），不得混入"闵子侍侧"（PASSAGE_A）
        assert "闵子侍侧" not in top["passage"]

    def test_locate_prefer_absent(self):
        from routes.agent_tools_retrieval import locate_exact_phrase
        r = locate_exact_phrase("言必有中", prefer_title="道德经")
        assert r["prefer_absent"] and r["found"]

    def test_locate_not_found(self):
        from routes.agent_tools_retrieval import locate_exact_phrase
        r = locate_exact_phrase("青天揽月，寸心如磐")
        assert not r["found"]

    def test_ensure_primary_read_removed_engine_no_longer_executes_reads(self):
        """O1: 引擎兜底 auto-read 已删除——主文本读取只能由 Main Agent 宣告。
        引擎层不再存在 _ensure_primary_read / AUTO_READ_THOUGHT; 台账不再有
        auto_primary_read 标志（防运行时认知代执行回归; 行为级断言见 test_o1_causal_loop.T1/T8）。"""
        import engine_langgraph as ELG
        assert not hasattr(ELG, "_ensure_primary_read")
        assert not hasattr(ELG, "AUTO_READ_THOUGHT")
        plan = RP.build_plan("言必有中出处")
        led = AR.ObligationLedger()
        assert not hasattr(led, "auto_primary_read")
        snap = led.snapshot()["verification_states"]
        assert "auto_primary_read" not in snap
        # 未读取时台账保持"未读"事实——是否补读由 Main Agent 自主决定
        assert led.primary_text_read is False


# ═══════════════════════════════════════════════════════
# T1.1-D Quote Bound
# ═══════════════════════════════════════════════════════
_PASSAGE_B = "鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”子曰：“夫人不言，言必有中。”"
_SPANS = [{"evidence_id": "qb_read_0", "book": "论语", "chapter": "先进篇",
           "book_id": "d927", "chapter_idx": 12, "source_type": "primary_read",
           "units": [_PASSAGE_B]}]


class TestT11DQuoteBound:
    def test_extract_blockquote_and_leadin(self):
        text = "开头\n> 这是一段足够长的引文内容用于测试提取逻辑\n结尾他写道：“这是引导词引文也足够长可被提取”"
        qs = QB.extract_quotes(text)
        kinds = {q["kind"] for q in qs}
        assert "blockquote" in kinds

    def test_verify_exact_near_memory(self):
        v1 = QB.verify_quote("鲁人为长府。闵子骞曰：“仍旧贯，如之何？何必改作？”子曰：“夫人不言，言必有中。”", _SPANS)
        assert v1["state"] == "VERIFIED_EXACT"
        v2 = QB.verify_quote("夫人不言，言必有中", _SPANS)
        assert v2["state"] == "VERIFIED_EXACT"
        v3 = QB.verify_quote("这是一句完全无关的话没有证据支撑它", _SPANS)
        assert v3["state"] == "MEMORY_ONLY"
        v4 = QB.verify_quote("短句", _SPANS)
        assert v4["state"] == "SHORT"

    def test_memory_blockquote_audited_not_converted(self):
        # O2 改写: QuoteBoundSanitizer（MEMORY_ONLY blockquote 转写"据通行理解"）已删除——
        # audit_quotes 如实标记 unverified_blockquote, 正文零转写;
        # 修复由 validator issue（UNSUPPORTED_EXACT_QUOTE）打回 same-agent 完成
        src = "回答开始\n> 这是一段未核验而直接给出的原文引文形态内容完全没有证据支撑\n回答结束"
        audit = QB.audit_quotes(src, [])
        assert audit["summary"]["unverified_blockquote"] == 1
        assert "> 这是一段未核验而直接给出的原文引文形态内容完全没有证据支撑" in src, "blockquote 原样保留（不转写）"
        assert "据通行理解，" not in src and "尚未在当前原典库中逐字核验" not in src
        _, issues = FV.check_quotes(src, [])
        assert any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in issues), "结构化 issue 打回 repair"

    def test_verified_blockquote_kept_verbatim(self):
        # VERIFIED_EXACT blockquote 原样保留在正文, validator 零 issue
        tool_log = [{"name": "get_chapter", "result_full": {"book_id": "d927", "chapter_idx": 12,
                                                     "title": "先进篇", "text": _PASSAGE_B,
                                                     "book_title": "论语"}}]
        src = f"结论如下\n> {_PASSAGE_B}\n以上。"
        audit, issues = FV.check_quotes(src, tool_log)
        assert audit["summary"]["verified_exact"] >= 1 and issues == []
        assert audit["entries"][0]["kind"] == "blockquote"
        assert audit["entries"][0]["verification_state"] == "VERIFIED_EXACT"
        assert f"> {_PASSAGE_B}" in src, "verified 引文原样保留"
        assert "据通行理解" not in src

    def test_audit_flags_unverified_blockquote(self):
        ans = "根据记忆：\n> 这是一段未核验的记忆引文完全没有证据支撑其逐字性\n以上"
        audit = QB.audit_quotes(ans, [])
        assert audit["summary"]["unverified_blockquote"] >= 1


# ═══════════════════════════════════════════════════════
# T1.1-F 相邻章句拼接
# ═══════════════════════════════════════════════════════
class TestT11FStitching:
    PASSAGE_A = "闵子侍侧，訚訚如也；子路，行行如也；冉有、子贡，侃侃如也。子乐。“若由也，不得其死然。”"

    def test_adjacent_units_stitch_fails(self):
        spans = [{"evidence_id": "u1", "book": "论语", "chapter": "先进篇", "book_id": "d927",
                  "chapter_idx": 12, "source_type": "primary_read", "units": [self.PASSAGE_A]},
                 {"evidence_id": "u2", "book": "论语", "chapter": "先进篇", "book_id": "d927",
                  "chapter_idx": 12, "source_type": "primary_read", "units": [_PASSAGE_B]}]
        # 真实事故形态: A 段开头逐字 + B 段结尾逐字的拼接引文
        stitched_quote = "闵子侍侧，訚訚如也。夫人不言，言必有中。"
        v = QB.verify_quote(stitched_quote, spans)
        assert v["state"] == "MEMORY_ONLY"
        assert v["stitched"]

    def test_whole_text_contiguity_blocks_stitch(self):
        # 即便两段在同一章文本内（拼接体不是连续子串）→ 不得 VERIFIED_EXACT
        spans = [{"evidence_id": "u1", "book": "论语", "chapter": "先进篇", "book_id": "d927",
                  "chapter_idx": 12, "source_type": "primary_read",
                  "units": [self.PASSAGE_A, _PASSAGE_B]}]
        stitched_quote = "闵子侍侧，訚訚如也。夫人不言，言必有中。"
        v = QB.verify_quote(stitched_quote, spans)
        assert v["state"] != "VERIFIED_EXACT"
        v2 = QB.verify_quote(_PASSAGE_B, spans)
        assert v2["state"] == "VERIFIED_EXACT"   # 真引文不受影响

    def test_stitched_audited_not_converted(self):
        # O2 改写: QuoteBoundSanitizer（拼接引文转写）已删除——
        # 拼接经 audit/validator 结构化暴露（STITCHED_QUOTE）, 正文零改写
        spans_units = [{"name": "get_chapter", "result_full": {
            "book_id": "d927", "chapter_idx": 12, "title": "先进篇", "book_title": "论语",
            "text": self.PASSAGE_A + "\n" + _PASSAGE_B}}]
        src = "\n> 闵子侍侧，訚訚如也。夫人不言，言必有中。\n"
        audit, issues = FV.check_quotes(src, spans_units)
        assert audit["summary"]["stitched"] >= 1
        assert any(i.code == FV.STITCHED_QUOTE for i in issues), "拼接引文 → 结构化 issue 打回 repair"
        assert "> 闵子侍侧，訚訚如也。夫人不言，言必有中。" in src, "正文原样（不转写）"
        assert "据通行理解，" not in src


# ═══════════════════════════════════════════════════════
# T1.1-G/H 收口一致性（O2 改写: scan_final_consistency 已拆分——
#   G 分支强确定性降调彻底删除（certainty 归 Agent 认知, 机械层不得治理）;
#   H 分支 verify-later 矛盾转为 final_validator.check_consistency 结构化 issue）
# ═══════════════════════════════════════════════════════
class TestT11GHConsistency:
    def test_strong_certainty_no_longer_governed(self):
        ans = "其作为成语来源的判断是可靠的——学界与通行注本一致。"
        assert FV.check_consistency(ans, primary_text_read=False) == [], \
            "强确定性 + 未核验不再被机械降调（validator 无 certainty 职权）"

    def test_no_issue_when_verified(self):
        ans = "原文已逐字核验，可以确认出处。"
        assert FV.check_consistency(ans, primary_text_read=True) == []

    def test_verify_later_contradiction_flagged_after_read(self):
        # O4: 仅由 primary_text_read 事实触发——台账显示本次已读原文,
        # 正文却称"可再读" → 机械可判定的自相矛盾 → issue
        for ans in ("若你需要，我可以再去读取《论语·先进》的章节全文。",
                    "你若需要，我可再作针对性逐字核验。"):
            issues = FV.check_consistency(ans, primary_text_read=True)
            assert [i.code for i in issues] == [FV.VERIFY_LATER_MISSTATEMENT], ans

    def test_verify_later_honest_boundary_when_unread(self):
        # 未读过原文时"可再核实"是诚实边界, 不是矛盾 → 零 issue
        ans = "需要的话我可以进一步核实原文。"
        assert FV.check_consistency(ans, primary_text_read=False) == []
