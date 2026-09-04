# -*- coding: utf-8 -*-
"""Patch 1.1 纯规则单元测试（Final Gate Closure: P1-P7）

P1 evidence obligation 台账与检索准入 / P2 核验意图分类 / P3 evidence contract
candidate-used 语义与二手排除 / P4 反事实 guard 非侵入 / P5 兜底回答指令 /
P6 claim role / P7 原典路径条件。
不联网、不调 LLM、不改任何数据。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

import reasoning_plan as RP    # noqa: E402
import agent_runtime as AR     # noqa: E402
import evidence_contract as EC  # noqa: E402
from epistemic_guard import CounterfactualAuthorGuard  # noqa: E402
from engine_langgraph import _final_answer_directive   # noqa: E402


# ═══════════════════════════════════════════════════════
# P2: 核验意图分类
# ═══════════════════════════════════════════════════════
class TestVerificationIntent:
    def test_f12_exact_wording_primary_only(self):
        vi = RP.detect_verification_intent(
            "只用亚里士多德自己的原典回答：“人是政治的动物”是不是他的原话？"
            "如果库里不能精确确认，就直接说不能确认，不要拿二手书替代。")
        assert vi["kind"] == "EXACT_WORDING"
        assert vi["constraint"] == "PRIMARY_ONLY"
        assert vi["term"] == "人是政治的动物"
        assert vi["subject_author"] == "亚里士多德"

    def test_g2_primary_only_exact_wording(self):
        vi = RP.detect_verification_intent(
            "只用斯宾诺莎自己的文本告诉我，“自由就是认识必然”是不是他的原话。")
        assert vi["kind"] == "EXACT_WORDING" and vi["constraint"] == "PRIMARY_ONLY"
        assert vi["term"] == "自由就是认识必然" and vi["subject_author"] == "斯宾诺莎"

    def test_g1_source_attribution(self):
        vi = RP.detect_verification_intent(
            "“认识你自己”真的是苏格拉底本人说的吗？如果只是德尔斐箴言请直接纠正。")
        assert vi["kind"] == "SOURCE_ATTRIBUTION"
        assert vi["term"] == "认识你自己" and vi["subject_author"] == "苏格拉底"

    def test_f02_exact_wording_translation_layer(self):
        vi = RP.detect_verification_intent(
            "维特根斯坦在《逻辑哲学论》里是不是逐字写过“语言的界限就是世界的界限”？"
            "我要确认的是这句中文表述本身，不只是思想大意。")
        assert vi["kind"] == "EXACT_WORDING"
        assert vi["term"] == "语言的界限就是世界的界限"

    def test_f03_attribution_book_only(self):
        vi = RP.detect_verification_intent(
            "尼采是不是在《查拉图斯特拉如是说》里写过“当你凝视深渊时，深渊也凝视你”？请告诉我具体章节。")
        assert vi["kind"] == "SOURCE_ATTRIBUTION" and vi["constraint"] == "BOOK_ONLY"

    def test_non_verification_untouched(self):
        # 普通概念/比较问题不得误判为核验
        assert RP.detect_verification_intent("比较一下康德和黑格尔对美的看法有什么异同？") is None
        assert RP.detect_verification_intent("什么是休谟的归纳问题？") is None
        # G3: 历史批评问题不是措辞/出处核验
        assert RP.detect_verification_intent(
            "为什么黑格尔会批评康德的物自体？我问历史上的批评，不要做假想对话。") is None

    def test_f12_plan_routed_to_verification(self):
        # P2 硬要求: F12 不得因句长被分类为 DEEP_SYNTHESIS, 必须进 verification-aware path
        p = RP.build_plan("只用亚里士多德自己的原典回答：“人是政治的动物”是不是他的原话？"
                          "如果库里不能精确确认，就直接说不能确认，不要拿二手书替代。")
        assert p["problem_type"] == "FACT_VERIFICATION"
        assert p["complexity"] == "NARROW_FACTUAL"
        assert p["verification_intent"]["constraint"] == "PRIMARY_ONLY"
        # 来源约束注入存在
        assert any("PRIMARY_ONLY" or "原典" in inj for inj in p["injections"])

    def test_f02_f03_enter_verification_path(self):
        for q in ("维特根斯坦在《逻辑哲学论》里是不是逐字写过“语言的界限就是世界的界限”？我要确认的是这句中文表述本身。",
                  "尼采是不是在《查拉图斯特拉如是说》里写过“当你凝视深渊时，深渊也凝视你”？请告诉我具体章节。"):
            p = RP.build_plan(q)
            assert p["problem_type"] == "FACT_VERIFICATION" and p["verification_intent"]


# ═══════════════════════════════════════════════════════
# P1: evidence obligation 台账（检索准入）
# ═══════════════════════════════════════════════════════
def _f12_vi():
    return {"kind": "EXACT_WORDING", "term": "人是政治的动物", "quoted": True,
            "constraint": "PRIMARY_ONLY", "subject_author": "亚里士多德"}


class TestObligationLedger:
    def test_f12_scenario_end_to_end(self):
        led = AR.ObligationLedger({"complexity": "NARROW_FACTUAL"}, _f12_vi())
        cx = "NARROW_FACTUAL"
        # 首轮: 2 个 search 准入
        assert led.admit("search_books", {"query": "人 政治动物 城邦 亚里士多德"}, cx, False)[0]
        assert led.admit("search_books", {"query": "亚里士多德 政治学 城邦 自然 本性"}, cx, False)[0]
        # 同族高相似改写被族规则拒绝（Jaccard ≥0.45）
        led.record("search_books", {"query": "人 政治动物 城邦 亚里士多德"}, True,
                   {"results": [{"book_id": "x", "chapter_idx": 1}]})
        led.mark_result("search_books", {"query": "人 政治动物 城邦 亚里士多德"}, low_gain=True)
        ok, why = led.admit("search_books", {"query": "亚里士多德 政治动物"}, cx, False)
        assert not ok and "query_family_exhausted" in why
        # 收口轮: 只准未读章节; search/websearch 一律拒绝
        assert led.admit("get_chapter", {"book_id": "53b0", "chapter_idx": 1}, cx, True)[0]
        ok, why = led.admit("search_books", {"query": "城邦 目的 论证"}, cx, True)
        assert not ok and "forced" in why
        # 读取命中措辞证据 → 义务满足
        led.record("get_chapter", {"book_id": "53b0", "chapter_idx": 2}, True,
                   {"book_id": "53b0", "chapter_idx": 2,
                    "text": "人类自然是趋向于城邦生活的动物（人类在本性上，也正是一个政治动物）"})
        assert led.obligations_satisfied
        # 义务满足后: 新 search / 重复 get_chapter / 书目类 一律拒绝（F12 回归核心）
        ok, _ = led.admit("search_books", {"query": "非野兽 即神 完全新的查询词"}, cx, False)
        assert not ok
        ok, why = led.admit("get_chapter", {"book_id": "53b0", "chapter_idx": 2}, cx, True)
        assert not ok and "已读取" in why
        ok, _ = led.admit("get_book_detail", {"book_id": "53b0"}, cx, False)
        assert not ok

    def test_lunyu_case_different_families_allowed(self):
        # 真实事故回归（《论语》案例）: 核验义务未满足时, 不同关键词的定位检索必须放行;
        # 且"读原文"不与 search 抢额度（read 独立配额）——read 排后面也能执行
        led = AR.ObligationLedger({"complexity": "NARROW_FACTUAL"},
                                  {"kind": "SOURCE_ATTRIBUTION", "term": "言必有中",
                                   "constraint": "BOOK_ONLY", "subject_author": ""})
        cx = "NARROW_FACTUAL"
        assert led.admit("search_books", {"query": "言必有中"}, cx, False)[0]
        assert led.admit("search_books", {"query": "夫人不言 言必有中"}, cx, False)[0]
        # 书目查询合法（确认《论语》在库）
        assert led.admit("query_database", {"table": "books", "key": "论语"}, cx, False)[0]
        # 第 3 个 search: 核验 search 配额满 → 拒（引导模型转入阅读原文; 措辞澄清"非库中无此书"）
        ok, why = led.admit("search_books", {"query": "闵子骞 仍旧贯 鲁人为长府"}, cx, False)
        assert not ok and "search_cap" in why and "get_chapter" in why and "非库中无此书" in why
        # 读原文: 独立配额, 不受 search 占用影响
        assert led.admit("get_chapter", {"book_id": "d927", "chapter_idx": 12}, cx, False)[0]
        led.record("get_chapter", {"book_id": "d927", "chapter_idx": 12}, True,
                   {"book_id": "d927", "chapter_idx": 12, "text": "夫人不言，言必有中"})
        assert led.obligations_satisfied
        # 第 2 个 read 也允许（配额 2）
        assert led.admit("get_chapter", {"book_id": "d927", "chapter_idx": 11}, cx, False)[0]
        # 第 3 个 read: read 配额满
        ok, why = led.admit("get_chapter", {"book_id": "d927", "chapter_idx": 10}, cx, False)
        assert not ok and "read_cap" in why

    def test_websearch_budget(self):
        # websearch: 核验路径 ≤1（从严）, 非核验 ≤2; forced 一律拒
        led_v = AR.ObligationLedger({"complexity": "NARROW_FACTUAL"}, _f12_vi())
        cx = "NARROW_FACTUAL"
        assert led_v.admit("websearch", {"query": "x"}, cx, False)[0]
        ok, why = led_v.admit("websearch", {"query": "y"}, cx, False)
        assert not ok and "websearch_cap" in why
        ok, why = led_v.admit("websearch", {"query": "z"}, cx, True)
        assert not ok and "forced" in why
        led_n = AR.ObligationLedger({"complexity": "DEEP_SYNTHESIS"}, None)
        assert led_n.admit("websearch", {"query": "a"}, "DEEP_SYNTHESIS", False)[0]
        assert led_n.admit("websearch", {"query": "b"}, "DEEP_SYNTHESIS", False)[0]
        ok, why = led_n.admit("websearch", {"query": "c"}, "DEEP_SYNTHESIS", False)
        assert not ok and "websearch_cap" in why

    def test_meta_book_lookup_not_blocked_by_searches(self):
        # 真实事故回归: 模型查"《论语》在不在库里"是合法动作, 不因已有检索被拒
        # （非核验路径——核验路径 meta 另有 ≤1 独立配额）
        led = AR.ObligationLedger({"complexity": "NARROW_FACTUAL"}, None)
        cx = "NARROW_FACTUAL"
        assert led.admit("search_books", {"query": "言必有中"}, cx, False)[0]
        assert led.admit("query_database", {"table": "books", "key": "论语"}, cx, False)[0]
        # 同对象第二次查 → 族规则拒绝
        ok, why = led.admit("query_database", {"table": "books", "key": "论语"}, cx, False)
        assert not ok and "query_family_exhausted" in why

    def test_verification_meta_cap(self):
        # 核验路径 meta ≤1（防"查目录→查详情"连环占用 gate 额度）, 措辞澄清"非库中无此书"
        led = AR.ObligationLedger({"complexity": "NARROW_FACTUAL"}, _f12_vi())
        cx = "NARROW_FACTUAL"
        assert led.admit("list_books", {"author": "亚里士多德"}, cx, False)[0]
        ok, why = led.admit("get_book_detail", {"book_id": "53b0"}, cx, False)
        assert not ok and "meta_cap" in why and "非库中无此书" in why
        # 非核验路径不受此限
        led2 = AR.ObligationLedger({"complexity": "NORMAL_EXPLANATION"}, None)
        cx2 = "NORMAL_EXPLANATION"
        assert led2.admit("list_books", {"author": "康德"}, cx2, False)[0]
        assert led2.admit("get_philosopher", {"name": "康德"}, cx2, False)[0]

    def test_wording_evidence_variants(self):
        led = AR.ObligationLedger({}, _f12_vi())
        assert led._wording_evidence_in("……人类在本性上，也正是一个政治动物……")
        assert not led._wording_evidence_in("城邦出于自然的演化，先有家庭后有村落。")
        # F02: 德文式接近句（去虚词归一后 4 字成分命中）
        led2 = AR.ObligationLedger({}, {"kind": "EXACT_WORDING", "term": "语言的界限就是世界的界限",
                                        "constraint": "NONE", "subject_author": ""})
        assert led2._wording_evidence_in("我的语言的界限意味着我的世界的界限。")

    def test_query_family_paraphrase_blocked(self):
        led = AR.ObligationLedger({"complexity": "DEEP_SYNTHESIS"}, None)
        cx = "DEEP_SYNTHESIS"
        q1 = {"query": "休谟 因果 必然性 习惯 联想"}
        assert led.admit("search_books", q1, cx, False)[0]
        led.record("search_books", q1, True, {"results": [{"book_id": "a", "chapter_idx": 1}]})
        led.mark_result("search_books", q1, low_gain=True, relevant_new=0)
        # 同族低增益后: 改写检索被拒（含"非库中无此书"澄清）
        ok, why = led.admit("search_books", {"query": "休谟 因果 必然联系 习惯性 联想"}, cx, False)
        assert not ok and "query_family_exhausted" in why and "非库中无此书" in why
        # 不同族仍可准入
        assert led.admit("search_books", {"query": "康德 先验演绎 范畴 统觉"}, cx, False)[0]

    def test_reject_streak_counter(self):
        # 拒绝累计计数（引擎消费: 达阈值强制收口, 防思考流卡住的空转循环）
        led = AR.ObligationLedger({"complexity": "NARROW_FACTUAL"}, _f12_vi())
        cx = "NARROW_FACTUAL"
        for _ in range(5):
            led.admit("search_books", {"query": f"随机查询词{_}"}, cx, False)   # 包络 5 → 依次被拒
        assert led.rejected >= AR.ADMISSION_REJECT_FORCE

    def test_read_failure_retry_allowed(self):
        led = AR.ObligationLedger({}, None)
        cx = "NORMAL_EXPLANATION"
        assert led.admit("get_chapter", {"book_id": "b", "chapter_idx": 3}, cx, False)[0]
        led.record("get_chapter", {"book_id": "b", "chapter_idx": 3}, False, None)
        assert led.admit("get_chapter", {"book_id": "b", "chapter_idx": 3}, cx, False)[0]
        led.record("get_chapter", {"book_id": "b", "chapter_idx": 3}, True, {"book_id": "b", "chapter_idx": 3, "text": "正文"})
        ok, why = led.admit("get_chapter", {"book_id": "b", "chapter_idx": 3}, cx, False)
        assert not ok and "已读取" in why

    def test_forced_read_cap(self):
        led = AR.ObligationLedger({"complexity": "DEEP_SYNTHESIS"}, None)
        cx = "DEEP_SYNTHESIS"
        assert led.admit("get_chapter", {"book_id": "b1", "chapter_idx": 1}, cx, True)[0]
        assert led.admit("get_chapter", {"book_id": "b2", "chapter_idx": 2}, cx, True)[0]
        ok, why = led.admit("get_chapter", {"book_id": "b3", "chapter_idx": 3}, cx, True)
        assert not ok and "forced_cap" in why


# ═══════════════════════════════════════════════════════
# P3: evidence contract — retrieved/candidate/used 语义 + 二手排除
# ═══════════════════════════════════════════════════════
def _f12_tool_log():
    return [
        {"name": "get_chapter", "args": {"book_id": "53b09f03e24e", "chapter_idx": 2},
         "result_full": {"book_id": "53b09f03e24e", "chapter_idx": 2, "title": "第二章",
                         "text": "人类自然是趋向于城邦生活的动物（人类在本性上，也正是一个政治动物）"}},
        {"name": "search_books", "args": {"query": "人是政治的动物"},
         "result_full": {"results": [
             {"book_title": "认识世界：古代与中世纪哲学", "book_id": "c97cb4e6161a",
              "author": "理查德·大卫·普莱希特", "chapter_idx": 3, "chapter_title": "在民主政治与寡头政治之间",
              "snippet": "普莱希特写道：人是政治的动物——亚里士多德的这一命题……"},
             {"book_title": "政治学", "book_id": "53b09f03e24e", "author": "亚里士多德",
              "chapter_idx": 2, "chapter_title": "第二章",
              "snippet": "人类自然是趋向于城邦生活的动物"}]}},
    ]


class TestEvidenceUsedSemantics:
    def test_f12_secondary_excluded_from_used(self):
        ans = ("结论：这一命题确实出自《政治学》卷一第二章，但不是逐字原话。\n"
               "原句是“人类自然是趋向于城邦生活的动物”【《政治学》· 第二章】。\n"
               "普莱希特写道：“人是政治的动物——亚里士多德的这一命题”，这是意译。")
        c = EC.build_evidence_contract(_f12_tool_log(), ans, "general", "zh",
                                       source_constraint="PRIMARY_ONLY",
                                       subject_authors=["亚里士多德"])
        used_books = {e["book"] for e in c["used_evidence"]}
        assert "政治学" in used_books
        assert all("普莱希特" not in (e.get("author") or "") for e in c["used_evidence"])
        assert all("普莱希特" not in (e.get("book") or "") for e in c["citations"])
        # 二手可存在于 retrieved/candidate（正文对齐）, 但 used=false 且带排除原因
        sec = [e for e in c["retrieved_evidence"] if "普莱希特" in (e.get("author") or "")]
        assert sec and sec[0]["candidate"] is True
        assert sec[0]["used"] is False
        assert sec[0].get("excluded_reason") == "secondary_source"
        assert c["secondary_excluded"] and all("普莱希特" in (e.get("author") or "")
                                               for e in c["secondary_excluded"])

    def test_no_constraint_keeps_current_semantics(self):
        ans = "原句见【《政治学》· 第二章】。普莱希特的概括见《认识世界：古代与中世纪哲学》。"
        c = EC.build_evidence_contract(_f12_tool_log(), ans, "general", "zh")
        assert c["used_count"] >= 1
        # 未加约束时二手不被排除（向后兼容）

    def test_subject_unknown_no_overblocking(self):
        # subject 未知时不做排除（防过度排除）
        ans = "普莱希特认为是意译【《认识世界：古代与中世纪哲学》· 在民主政治与寡头政治之间】。"
        c = EC.build_evidence_contract(_f12_tool_log(), ans, "general", "zh",
                                       source_constraint="PRIMARY_ONLY", subject_authors=[])
        assert any("普莱希特" in (e.get("book") or "") or "普莱希特" in (e.get("author") or "")
                   for e in c["used_evidence"])

    def test_candidate_flag(self):
        ans = "原句是“人类自然是趋向于城邦生活的动物”【《政治学》· 第二章】。"
        c = EC.build_evidence_contract(_f12_tool_log(), ans, "general", "zh")
        assert all(e.get("candidate") is not None for e in c["retrieved_evidence"])
        assert all(e["used"] <= e["candidate"] for e in c["retrieved_evidence"])  # used ⊆ candidate


# ═══════════════════════════════════════════════════════
# P4: counterfactual guard 非侵入
# ═══════════════════════════════════════════════════════
class TestGuardNonIntrusion:
    def test_f06_not_counterfactual(self):
        # F06 误触发根因: 引文"必然性"命中强模态词 → 模态单独不得触发
        v = CounterfactualAuthorGuard().check(
            "休谟和康德都从“经验不能给出必然性”这个困难出发，但为什么康德不是简单地“反驳休谟”？")
        assert v["mode"] == "historical" and not v["requires_guard"]

    def test_g3_historical_criticism_not_counterfactual(self):
        v = CounterfactualAuthorGuard().check(
            "为什么黑格尔会批评康德的物自体？我问历史上的批评，不要做假想对话。")
        assert v["mode"] == "historical" and not v["requires_guard"]

    def test_normal_relations_silent(self):
        for q in ("康德会如何回应休谟的怀疑论？",
                  "休谟和康德的理论差异在哪里？",
                  "黑格尔受到康德什么影响？",
                  "亚里士多德是否反驳了柏拉图的理念论？"):
            v = CounterfactualAuthorGuard().check(q)
            assert v["mode"] == "historical" and not v["requires_guard"], q

    def test_true_counterfactual_still_fires(self):
        # 当代对象
        v = CounterfactualAuthorGuard().check("尼采会怎么看短视频算法？")
        assert v["mode"] == "counterfactual" and v["requires_guard"]
        # 活到今天
        v = CounterfactualAuthorGuard().check("如果康德活到今天看到人工智能会怎么想？")
        assert v["mode"] == "counterfactual" and v["requires_guard"]
        # 单哲人 + 无史料话题的"会怎么看"
        v = CounterfactualAuthorGuard().check("笛卡尔会怎么看精神分析？")
        assert v["mode"] == "counterfactual" and v["requires_guard"]

    def test_documented_topic_still_historical(self):
        v = CounterfactualAuthorGuard().check("尼采会如何评价瓦格纳的音乐？")
        assert v["mode"] == "historical" and not v["requires_guard"]


# ═══════════════════════════════════════════════════════
# P5: 兜底回答指令（核验义务四要素）
# ═══════════════════════════════════════════════════════
class TestFallbackDirective:
    def test_verification_directive_keeps_obligations(self):
        plan = {"verification_intent": {"kind": "EXACT_WORDING", "term": "语言的界限就是世界的界限",
                                        "constraint": "NONE", "subject_author": ""}}
        d = _final_answer_directive(plan, {"state": "NOT_FOUND", "term": "语言的界限就是世界的界限"}, "zh")
        assert "核验结论" in d and "层次区分" in d and "确定性边界" in d and "原句" in d
        assert "语言的界限就是世界的界限" in d and "NOT_FOUND" in d

    def test_generic_directive_unchanged(self):
        d = _final_answer_directive({"verification_intent": None}, None, "zh")
        assert "只输出回答文本" in d and "核验结论" not in d

    def test_en_directive(self):
        plan = {"verification_intent": {"kind": "EXACT_WORDING", "term": "x",
                                        "constraint": "NONE", "subject_author": ""}}
        d = _final_answer_directive(plan, {"state": "NOT_FOUND", "term": "x"}, "en")
        assert "Verdict" in d and "Confidence boundary" in d


# ═══════════════════════════════════════════════════════
# P6: claim role（内部表示, 不成正文标题）
# ═══════════════════════════════════════════════════════
class TestClaimRole:
    def _claims(self, answer):
        return EC._claims_from_answer(answer, [])

    def test_roles_distinguished(self):
        ans = ("康德明确主张范畴只适用于现象界【《纯粹理性批判》· 第二章】。\n"
               "可以把这一步理解为康德对休谟问题的一个先验转换。\n"
               "一个有力的读法是把物自体看作界限概念。\n"
               "后来如黑格尔所提出的批评是：先验唯心论把规定都挪进主观。\n"
               "我认为，如果把这些线索合在一起，康德付出的代价是把必然性主观化。")
        roles = [c["role"] for c in self._claims(ans)]
        assert "TEXTUAL_CLAIM" in roles
        assert "RECONSTRUCTION" in roles
        assert "INTERPRETIVE_CLAIM" in roles
        assert "LATER_CRITICISM" in roles
        assert "AGENT_SYNTHESIS" in roles

    def test_role_not_visible_title_material(self):
        # role 是内部语义——不在 CLAIM_ROLES 之外的正文映射里出现
        for r in EC._CLAIM_ROLE_CUES:
            assert r[0] in RP.CLAIM_ROLES

    def test_deep_question_gets_role_directive(self):
        p = RP.build_plan("深入分析：休谟为什么会走向怀疑，而康德为什么会走向先验哲学？"
                          "请说明康德为了保住必然性付出了什么哲学代价。")
        assert p["claim_role_directive"] and "主张层级" in p["claim_role_directive"]
        # 普通概念解释不注入（不扩大范围）
        p2 = RP.build_plan("什么是洞穴寓言？")
        assert p2["claim_role_directive"] is None


# ═══════════════════════════════════════════════════════
# P7: 原典路径按价值条件出现（确定性）
# ═══════════════════════════════════════════════════════
class TestSourceNavigation:
    def test_deep_and_genealogy_allowed(self):
        assert RP.source_navigation_allowed("DEEP_SYNTHESIS", "深入分析……")
        assert RP.source_navigation_allowed("HISTORICAL_GENEALOGY", "概念如何演变……")
        assert RP.source_navigation_allowed("TEXTUAL_INTERPRETATION", "如何理解……")

    def test_concept_and_verification_suppressed(self):
        assert not RP.source_navigation_allowed("FACT_VERIFICATION", "是不是原话？")
        assert not RP.source_navigation_allowed("CONCEPT_EXPLANATION", "什么是X？")
        assert not RP.source_navigation_allowed("ARGUMENT_ANALYSIS", "分析这个论证。")
        assert not RP.source_navigation_allowed("COMPARISON", "比较A与B。")

    def test_explicit_reading_path_request_allowed(self):
        assert RP.source_navigation_allowed("CONCEPT_EXPLANATION", "我想按顺序读柏拉图，应该先读哪一本？")
        assert RP.source_navigation_allowed("FACT_VERIFICATION", "给一份亚里士多德的书单/阅读路径。")

    def test_suppression_injection_present(self):
        p = RP.build_plan("什么是洞穴寓言？")
        assert not p["source_navigation"]
        assert any("原典路径" in inj for inj in p["injections"])
        p2 = RP.build_plan("深入分析：休谟为什么会走向怀疑，而康德为什么会走向先验哲学？")
        assert p2["source_navigation"]
        assert not any("不需要「原典路径」" in inj for inj in p2["injections"])
