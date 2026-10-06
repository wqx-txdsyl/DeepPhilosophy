# -*- coding: utf-8 -*-
"""Phase T.1 — Source Attribution / Quote Verification Regression Hotfix（T1.1-A~H）

对应真实回归: "言必有中出处" → 模型凭记忆给 blockquote（甚至拼接相邻章句）+
"未经库中核验" 免责 + "如果你需要我可以再读"反模式。

本文件只测确定性规则层（不调 LLM）:
  T1.1-A  事实分层（O4: 义务满足总闸已删; O5: 台账并入 evidence_contract.EvidenceState——
          只剩 LOCATED/READ 执行事实, 逐字命中判定归 quote_bound/validator;
          O4-RP1: 意图检测/术语核验链已随旧 planner 模块删除——理解用户问题归 Main Agent）
  T1.1-B  locate_exact_phrase 逐字定位
  T1.1-D  Quote Bound: 提取/核验状态（O2: 流式渲染转写已删——audit + validator issue）
  T1.1-E  MEMORY_HINT ≠ EVIDENCE（检索命中不置位 primary_text_read）
  T1.1-F  相邻章句拼接防护（跨 span 连续性校验）
O4-RP1: T1.1-G/H（verify-later 矛盾 → validator issue）已随 check_consistency 删除
（task-intent discipline; evidence-consistency 类检查如后续需要再立项）。
O4: T1.1-C（read 配额/准入拒绝措辞）已随检索准入机制删除。
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import quote_bound as QB
import final_validator as FV


# ═══════════════════════════════════════════════════════
# T1.1-A 执行事实分层（O5: 旧义务台账整类并入 evidence_contract.EvidenceState——
# 只记 LOCATED/READ 执行事实; term/exact_quote_verified 失去生产喂入口随之删除,
# 逐字核验真源 = quote_bound.verify_quote + final_validator, 见 TestT11D/F）
# ═══════════════════════════════════════════════════════
class TestT11AExecutionFacts:
    def test_evidence_state_located_vs_read_layering(self):
        from evidence_contract import EvidenceState
        ev = EvidenceState()
        # 检索命中 → 只置位 source_candidate_found（MEMORY_HINT, T1.1-E）
        ev.record_search(True, {"results": [{"book_id": "d927", "chapter_idx": 12}]})
        assert ev.source_candidate_found
        assert not ev.primary_text_read
        # get_chapter 成功读取 → READ（主文本已读）
        ev.record_read("d927", 12)
        assert ev.primary_text_read
        snap = ev.snapshot()
        assert snap["source_candidate_found"] and snap["primary_text_read"]
        assert snap["read_chapters"] == ["d927#12"]
        assert snap["search_execs"] == 1 and snap["read_execs"] == 1

    def test_read_registers_fact_without_verdict(self):
        # R7 型: 读到章节 ≠ 逐字核验通过——EvidenceState 只记"已读"事实,
        # "表述是否逐字命中原文"由 quote_bound/validator 判定（O5: 台账不再裁决）
        from evidence_contract import EvidenceState
        ev = EvidenceState()
        ev.record_read("x", 1)
        snap = ev.snapshot()
        assert snap["primary_text_read"] is True
        assert "exact_quote_verified" not in snap        # 死字段不得回归
        assert "verification_states" not in snap         # 旧嵌套形态不再存在

    def test_failed_read_and_failed_search_facts(self):
        from evidence_contract import EvidenceState
        ev = EvidenceState()
        ev.record_search(False, {"error": "x"})          # 失败检索也计数（事实）
        assert ev.search_execs == 1 and not ev.source_candidate_found
        ev.record_search(True, {"results": [{"book_id": "d"}]})
        assert ev.source_candidate_found


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
        引擎层不再存在 _ensure_primary_read / AUTO_READ_THOUGHT; O5 后事实登记器 =
        evidence_contract.EvidenceState（agent_runtime 旧义务台账整类已删,
        防运行时认知代执行回归; 行为级断言见 test_o1_causal_loop.T1/T8）。"""
        import engine_langgraph as ELG
        assert not hasattr(ELG, "_ensure_primary_read")
        assert not hasattr(ELG, "AUTO_READ_THOUGHT")
        from evidence_contract import EvidenceState
        ev = EvidenceState()
        assert not hasattr(ev, "auto_primary_read")
        assert "auto_primary_read" not in ev.snapshot()
        # 未读取时台账保持"未读"事实——是否补读由 Main Agent 自主决定
        assert ev.primary_text_read is False


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
# T1.1-G/H (O4-RP1 删除确认): check_consistency / VERIFY_LATER_MISSTATEMENT
# 已随 final_validator 瘦身删除（task-intent discipline——runtime 不判断
# "这道题本来就该现在查"; evidence-consistency 类检查如后续需要再立项）
# ═══════════════════════════════════════════════════════
class TestT11GHConsistencyRemoved:
    def test_no_consistency_governance_symbols(self):
        assert not hasattr(FV, "check_consistency")
        assert not hasattr(FV, "VERIFY_LATER_MISSTATEMENT")
        # validate_final_candidate 签名收窄: 无 primary_text_read / 意图分类参数
        import inspect
        sig = inspect.signature(FV.validate_final_candidate)
        for gone in ("primary_text_read", "source_constraint", "subject_authors",
                     "verification_intent"):
            assert gone not in sig.parameters, gone
        # verify-later 措辞不再是发布拦截对象——候选原样通过 validator（quote/citation 除外）
        ans = "若你需要，我可以再去读取《论语·先进》的章节全文。"
        res = FV.validate_final_candidate(ans, raw_tool_log=[], fallback_log=[])
        assert res.ok is True
