# -*- coding: utf-8 -*-
"""Phase T.1 — Source Attribution / Quote Verification Regression Hotfix（T1.1-A~H）

对应真实回归: "言必有中出处" → 模型凭记忆给 blockquote（甚至拼接相邻章句）+
"未经库中核验" 免责 + "如果你需要我可以再读"反模式。

本文件只测确定性规则层（不调 LLM）:
  T1.1-A  SOURCE_ATTRIBUTION 检测（裸「X出处」词型/term 兜底）+ 义务三态分层
  T1.1-B  locate_exact_phrase 逐字定位 + _ensure_primary_read 兜底读取
  T1.1-C  read 配额独立 + ADMISSION_REJECTED ≠ SOURCE_NOT_FOUND（拒绝理由措辞）
  T1.1-D  Quote Bound: 提取/核验状态/流式渲染规则
  T1.1-E  MEMORY_HINT ≠ EVIDENCE（检索命中不置位 primary_text_read）
  T1.1-F  相邻章句拼接防护（跨 span 连续性校验）
  T1.1-G/H 收口一致性扫描（置信升级 / verify-later 反模式）
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent_runtime as AR
import quote_bound as QB
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
        assert plan["problem_type"] == "FACT_VERIFICATION"
        assert plan["complexity"] == "NARROW_FACTUAL"
        assert plan["verification_intent"]["term"] == "言必有中"
        # T1.1-B/E/H: 核验纪律注入必须存在
        assert any("出处核验纪律" in inj for inj in plan["injections"])

    def test_ledger_three_state_layering(self):
        led = AR.ObligationLedger({}, {"kind": "SOURCE_ATTRIBUTION", "term": "言必有中",
                                       "constraint": "NONE", "subject_author": ""})
        # 检索命中 → 只置位 SOURCE_CANDIDATE_FOUND（MEMORY_HINT, T1.1-E）
        led.record("search_books", {"query": "言必有中"}, True,
                   {"results": [{"book_id": "d927", "chapter_idx": 12}]})
        assert led.source_candidate_found
        assert not led.primary_text_read
        assert not led.obligations_satisfied
        # get_chapter 全文命中 → READ + EXACT + 满足
        led.record("get_chapter", {"book_id": "d927", "chapter_idx": 12}, True,
                   {"book_id": "d927", "chapter_idx": 12,
                    "text": "鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”子曰：“夫人不言，言必有中。”"})
        assert led.primary_text_read
        assert led.exact_quote_verified
        assert led.obligations_satisfied
        snap = led.snapshot()["verification_states"]
        assert snap["source_candidate_found"] and snap["primary_text_read"]
        assert snap["exact_quote_verified"]

    def test_read_without_term_hit_stays_unsatisfied(self):
        # R7 型: 读到了章节但表述不在其中 → 已读但不满足（诚实 NOT_FOUND 路径）
        led = AR.ObligationLedger({}, {"kind": "SOURCE_ATTRIBUTION", "term": "青天揽月寸心如磐",
                                       "constraint": "NONE", "subject_author": ""})
        led.record("get_chapter", {"book_id": "x", "chapter_idx": 1}, True,
                   {"book_id": "x", "chapter_idx": 1, "text": "子曰：学而时习之，不亦说乎。"})
        assert led.primary_text_read
        assert not led.exact_quote_verified
        assert not led.obligations_satisfied


# ═══════════════════════════════════════════════════════
# T1.1-C 分项预算与拒绝理由措辞
# ═══════════════════════════════════════════════════════
class TestT11CBudget:
    def test_search_exhaustion_does_not_block_read(self):
        led = AR.ObligationLedger({}, {"kind": "SOURCE_ATTRIBUTION", "term": "言必有中",
                                       "constraint": "NONE", "subject_author": ""})
        cx = "NARROW_FACTUAL"
        assert led.admit("search_books", {"query": "言必有中"}, cx, False)[0]
        assert led.admit("search_books", {"query": "夫人不言 言必有中"}, cx, False)[0]
        ok, why = led.admit("search_books", {"query": "闵子骞 长府"}, cx, False)
        assert not ok and "search_cap" in why
        # search 用尽不影响 read（独立配额, T1.1-C 核心）
        assert led.admit("get_chapter", {"book_id": "d927", "chapter_idx": 12}, cx, False)[0]

    def test_admission_rejected_is_not_source_not_found(self):
        led = AR.ObligationLedger({}, None)
        cx = "NORMAL_EXPLANATION"
        led.admit("search_books", {"query": "a"}, cx, True)   # forced 轮
        ok, why = led.admit("search_books", {"query": "b"}, cx, True)
        assert not ok
        # 拒绝理由必须防止模型把"未执行"误读为"库中无此书"
        assert "非库中无此书" in why or "不得向用户声称库中未收录" in why


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

    def test_ensure_primary_read_triggers_and_satisfies(self):
        import engine_langgraph as ELG
        plan = RP.build_plan("言必有中出处")
        led = AR.ObligationLedger(plan)
        led.search_execs = 2   # 模拟已发生定位
        raw_log = []
        state = {"plan": plan, "obligation_ledger": led, "verif_box": {"state": None, "term": "言必有中", "computed": False},
                 "raw_tool_log": raw_log, "budget": None, "trace": None,
                 "user_message": "言必有中出处", "language": "zh"}

        async def run():
            return await ELG._ensure_primary_read(state)

        out = asyncio.run(run())
        assert out and out["located"]
        assert "论语" in out["injection"]
        assert raw_log and raw_log[-1]["name"] == "get_chapter"
        assert led.primary_text_read and led.obligations_satisfied
        assert led.auto_primary_read
        # 幂等: 第二次不再触发
        out2 = asyncio.run(run())
        assert out2 is None


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

    def test_sanitizer_converts_memory_blockquote(self):
        s = QB.QuoteBoundSanitizer([], "zh")
        src = "回答开始\n> 这是一段凭记忆给出的所谓原文引文并没有任何证据支撑\n回答结束"
        out = s.push(src) + s.flush()
        assert "> " not in out.split("回答开始")[1].split("回答结束")[0]
        assert "据通行理解，" in out
        assert "尚未在当前原典库中逐字核验" in out
        assert s.snapshot()["converted"] == 1

    def test_sanitizer_keeps_verified_blockquote(self):
        s = QB.QuoteBoundSanitizer(
            [{"name": "get_chapter", "result_full": {"book_id": "d927", "chapter_idx": 12,
                                                     "title": "先进篇", "text": _PASSAGE_B,
                                                     "book_title": "论语"}}], "zh")
        src = f"结论如下\n> {_PASSAGE_B}\n以上。"
        out = s.push(src) + s.flush()
        assert "> 鲁人为长府" in out
        assert "据通行理解" not in out
        assert s.snapshot()["verified_exact"] == 1

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

    def test_sanitizer_converts_stitched(self):
        spans_units = [{"name": "get_chapter", "result_full": {
            "book_id": "d927", "chapter_idx": 12, "title": "先进篇", "book_title": "论语",
            "text": self.PASSAGE_A + "\n" + _PASSAGE_B}}]
        s = QB.QuoteBoundSanitizer(spans_units, "zh")
        src = "\n> 闵子侍侧，訚訚如也。夫人不言，言必有中。\n"
        out = s.push(src) + s.flush()
        assert "据通行理解，" in out
        assert s.snapshot()["stitched"] >= 1


# ═══════════════════════════════════════════════════════
# T1.1-G/H 收口一致性
# ═══════════════════════════════════════════════════════
class TestT11GHConsistency:
    def test_strong_certainty_downgraded_when_unverified(self):
        ans = "其作为成语来源的判断是可靠的——学界与通行注本一致。"
        audit = QB.audit_quotes(ans, [])
        appends = QB.scan_final_consistency(ans, audit, obligations_satisfied=False)
        assert any("确定性边界" in a for a in appends)

    def test_no_downgrade_when_verified(self):
        ans = "原文已逐字核验，可以确认出处。"
        audit = QB.audit_quotes(ans, [])
        appends = QB.scan_final_consistency(ans, audit, obligations_satisfied=True,
                                            primary_text_read=True)
        assert not appends

    def test_verify_later_neutralized_after_read(self):
        for ans in ("若你需要，我可以再去读取《论语·先进》的章节全文。",
                    "你若需要，我可再作针对性逐字核验。"):
            audit = QB.audit_quotes(ans, [])
            appends = QB.scan_final_consistency(ans, audit, obligations_satisfied=True,
                                                primary_text_read=True)
            assert any("更正" in a for a in appends), ans

    def test_verify_later_boundary_when_unverified(self):
        ans = "需要的话我可以进一步核实原文。"
        audit = QB.audit_quotes(ans, [])
        appends = QB.scan_final_consistency(ans, audit, obligations_satisfied=False)
        assert any("核验边界" in a for a in appends)
