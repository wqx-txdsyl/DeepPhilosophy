# -*- coding: utf-8 -*-
"""Patch 1.1 纯规则单元测试（Final Gate Closure: P1-P7）

P1 execution fact ledger（O4: 纯事实登记器——检索准入/配额/义务总闸已删）/
P2 核验意图分类 / P3 evidence contract candidate-used 语义与二手排除 /
P5 短答与空候选零第二 writer（O2: 兜底回答指令与 AG.llm_chat 兜底生成已删）/
P6 claim role（evidence_contract 内部分级）。
O4: P4 反事实 guard / P7 原典路径条件已随 Shadow cognition 删除。
不联网、不调 LLM、不改任何数据。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from langchain_core.messages import AIMessageChunk  # noqa: E402

import reasoning_plan as RP    # noqa: E402
import agent_runtime as AR     # noqa: E402
import evidence_contract as EC  # noqa: E402


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

    def test_f12_plan_carries_verification_intent(self):
        # O4: plan 不再有 problem_type/complexity（认知分类已删）——
        # 核验意图与来源约束注入是仅存的机械上下文
        p = RP.build_plan("只用亚里士多德自己的原典回答：“人是政治的动物”是不是他的原话？"
                          "如果库里不能精确确认，就直接说不能确认，不要拿二手书替代。")
        assert "problem_type" not in p and "complexity" not in p
        assert p["verification_intent"]["constraint"] == "PRIMARY_ONLY"
        # 来源约束注入存在
        assert any("原典" in inj for inj in p["injections"])

    def test_f02_f03_enter_verification_path(self):
        for q in ("维特根斯坦在《逻辑哲学论》里是不是逐字写过“语言的界限就是世界的界限”？我要确认的是这句中文表述本身。",
                  "尼采是不是在《查拉图斯特拉如是说》里写过“当你凝视深渊时，深渊也凝视你”？请告诉我具体章节。"):
            p = RP.build_plan(q)
            assert p["verification_intent"]


# ═══════════════════════════════════════════════════════
# P1: evidence obligation 台账（检索准入）
# ═══════════════════════════════════════════════════════
def _f12_vi():
    return {"kind": "EXACT_WORDING", "term": "人是政治的动物", "quoted": True,
            "constraint": "PRIMARY_ONLY", "subject_author": "亚里士多德"}


class TestObligationLedger:
    """O4: 纯事实登记器——record 后 snapshot 含执行事实; 无 admit/配额/义务总闸"""

    def _led(self, term=""):
        return AR.ObligationLedger(term=term)

    def test_search_hit_registers_candidate_found_and_counter(self):
        led = self._led(term="言必有中")
        led.record("search_books", {"query": "言必有中"}, True,
                   {"results": [{"book_id": "d927", "chapter_idx": 12}]})
        snap = led.snapshot()
        assert snap["verification_states"]["source_candidate_found"] is True
        # MEMORY_HINT 永远不置位 READ（T1.1-E 不变量保留）
        assert snap["verification_states"]["primary_text_read"] is False
        assert snap["search_execs"] == 1 and snap["read_execs"] == 0

    def test_read_registers_primary_text_and_exact_hit(self):
        led = self._led(term="言必有中")
        led.record("get_chapter", {"book_id": "d927", "chapter_idx": 12}, True,
                   {"book_id": "d927", "chapter_idx": 12,
                    "text": "鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”子曰：“夫人不言，言必有中。”"})
        snap = led.snapshot()
        assert snap["read_chapters"] == ["d927#12"]
        assert snap["verification_states"]["primary_text_read"] is True
        assert snap["verification_states"]["exact_quote_verified"] is True
        assert snap["read_execs"] == 1

    def test_read_without_term_hit_stays_unverified(self):
        # R7 型: 读到了章节但表述不在其中 → 已读但未逐字命中（诚实 NOT_FOUND 路径）
        led = self._led(term="青天揽月寸心如磐")
        led.record("get_chapter", {"book_id": "x", "chapter_idx": 1}, True,
                   {"book_id": "x", "chapter_idx": 1, "text": "子曰：学而时习之，不亦说乎。"})
        vs = led.snapshot()["verification_states"]
        assert vs["primary_text_read"] is True and vs["exact_quote_verified"] is False

    def test_failed_read_not_registered_as_read(self):
        led = self._led()
        led.record("get_chapter", {"book_id": "b", "chapter_idx": 3}, False, {"error": "x"})
        snap = led.snapshot()
        assert snap["read_chapters"] == [] and snap["read_execs"] == 0
        assert snap["verification_states"]["primary_text_read"] is False

    def test_no_admission_quota_api_remains(self):
        # O4 删除的准入/配额/义务面: 不得回归
        led = self._led()
        for gone in ("admit", "mark_result", "_reject", "family_key", "obligations_satisfied",
                     "rejected", "forced_reads", "_wording_evidence_in"):
            assert not hasattr(led, gone), gone


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
# P5 (O2 改写): 短答/空候选零第二 writer——兜底回答指令
# （_final_answer_directive）与 AG.llm_chat 兜底生成已删除:
# 空候选 → validator EMPTY_FINAL → same-agent repair; 短答 → 原样发布。
# ═══════════════════════════════════════════════════════
class _FakeApp:
    """替换 LangGraph APP.astream: 单 agent 轮回一个 AIMessageChunk（最终回答候选）"""

    def __init__(self, answer):
        self.answer = answer
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


class TestNoSecondWriterForShortOrEmptyAnswers:
    async def _run(self, monkeypatch, answer):
        import engine_langgraph as elg
        from routes import agent as AG
        llm_calls = []

        def _forbidden_llm_chat(*a, **k):
            llm_calls.append(a)
            return {"choices": [{"message": {"content": ""}}]}
        fake = _FakeApp(answer)
        monkeypatch.setattr(elg, "APP", fake)
        monkeypatch.setattr(AG, "llm_chat", _forbidden_llm_chat, raising=False)
        evs = [ev async for ev in elg.stream_agent("什么是荒诞？", [], "general", None, "zh")]
        return evs, llm_calls

    def test_short_answer_published_without_second_llm(self, monkeypatch):
        # 短答（<60 字符）不再触发第二 LLM 兜底生成——validator PASS → 原样发布
        short = "荒诞是理性与世界的裂隙。"
        evs, llm_calls = asyncio.run(self._run(monkeypatch, short))
        text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
        assert text == short, "短答原样发布, 无兜底改写/追加"
        assert llm_calls == [], "短答不得触发第二 LLM（AG.llm_chat 兜底生成已删）"
        done = next(ev for ev in evs if ev["type"] == "done")
        assert done["validation"]["result"]["ok"] is True
        assert done["validation"]["repairs_used"] == 0

    def test_empty_candidate_repairs_same_agent_never_llm_chat(self, monkeypatch):
        # 空候选 → validator EMPTY_FINAL → 中性反馈打回同一个 Main Agent
        # （图重跑, 绝不调 AG.llm_chat 独立生成）; 达上限后如实收口
        evs, llm_calls = asyncio.run(self._run(monkeypatch, ""))
        assert llm_calls == [], "空候选兜底不得调用第二 LLM"
        done = next(ev for ev in evs if ev["type"] == "done")
        v = done["validation"]
        assert v["result"]["ok"] is False
        assert any(i["code"] == "EMPTY_FINAL" for i in v["result"]["issues"])
        assert v["repairs_used"] == v["max_validation_repairs"] == 2
        assert v["repair_protocol"] == "same_main_agent"
        fo = done["final_ownership"]
        assert fo["final_text_owner"] == "main_agent"
        assert fo["invalid_final_publicly_streamed"] is False
        assert fo["validator_repair_invocations"] == 2


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
