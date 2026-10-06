# -*- coding: utf-8 -*-
"""Patch 1.1 纯规则单元测试（Final Gate Closure: P1-P7）

P1 execution fact ledger（O4: 纯事实登记器——检索准入/配额/义务总闸已删）/
P5 短答与空候选零第二 writer（O2: 兜底回答指令与 AG.llm_chat 兜底生成已删）/
P6 claim role（evidence_contract 内部分级）。
O4: P4 反事实 guard / P7 原典路径条件已随 Shadow cognition 删除。
O4-RP1: P2 核验意图分类（含来源约束注入）已随旧 planner 模块整体删除;
P3 的来源约束二手排除（source_constraint/subject_authors）一并移除——
evidence contract 只描述 检索候选 ↔ 回答使用 的确定性关系。
不联网、不调 LLM、不改任何数据。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from langchain_core.messages import AIMessageChunk  # noqa: E402

import agent_runtime as AR     # noqa: E402
import evidence_contract as EC  # noqa: E402


# ═══════════════════════════════════════════════════════
# P2 (O4-RP1 删除确认): 核验意图分类不得回归
# ═══════════════════════════════════════════════════════
class TestVerificationIntentRemoved:
    def test_no_intent_classifier_symbols(self):
        import sys as _sys
        assert not any(m.endswith("plan") and m.startswith("reasoning") for m in _sys.modules), "旧 planner 模块不得回归"
        import engine_langgraph as elg
        assert not hasattr(elg, "detect_verification_intent")
        assert not hasattr(elg, "verification_constraint_directive")
        # 引擎源码（剥注释）无意图分类/约束注入引用（行为级审计见 test_o4.TestRP1）
        import inspect
        code_only = "\n".join(ln for ln in inspect.getsource(elg).splitlines()
                              if not ln.strip().startswith("#"))
        for gone in ("build_plan", "injections"):
            assert gone not in code_only, gone


# ═══════════════════════════════════════════════════════
# P1: 执行事实登记（O5 MERGE: agent_runtime 旧义务台账整类删除, 并入
#     evidence_contract.EvidenceState——纯事实登记器, 检索准入/配额/义务总闸随 O4 删除）
# ═══════════════════════════════════════════════════════
class TestEvidenceState:
    """record 后 snapshot 含执行事实; 无 admit/配额/义务总闸/term 死字段"""

    def _ev(self):
        return EC.EvidenceState()

    def test_search_hit_registers_candidate_found_and_counter(self):
        ev = self._ev()
        ev.record_search(True, {"results": [{"book_id": "d927", "chapter_idx": 12}]})
        snap = ev.snapshot()
        assert snap["source_candidate_found"] is True
        # MEMORY_HINT 永远不置位 READ（T1.1-E 不变量保留）
        assert snap["primary_text_read"] is False
        assert snap["search_execs"] == 1 and snap["read_execs"] == 0

    def test_read_registers_primary_text_fact(self):
        ev = self._ev()
        ev.record_read("d927", 12)
        snap = ev.snapshot()
        assert snap["read_chapters"] == ["d927#12"]
        assert snap["primary_text_read"] is True
        assert snap["read_execs"] == 1

    def test_read_fact_carries_no_verification_verdict(self):
        # R7 型: "已读"是事实, "表述是否逐字命中"不是台账的判断（quote_bound/validator 职责）
        ev = self._ev()
        ev.record_read("x", 1)
        vs = ev.snapshot()
        assert vs["primary_text_read"] is True
        assert "exact_quote_verified" not in vs and "term" not in vs

    def test_failed_read_not_registered_as_read(self):
        # 失败读取不是 READ 事实——工具失败时引擎不调用 record_read（O3 判据沿用）
        ev = self._ev()
        assert ev.snapshot()["read_chapters"] == [] and ev.snapshot()["read_execs"] == 0
        assert ev.snapshot()["primary_text_read"] is False

    def test_no_admission_quota_api_remains(self):
        # O4 删除的准入/配额/义务面 + O5 删除的 term/exact_quote_verified: 不得回归
        ev = self._ev()
        for gone in ("admit", "mark_result", "_reject", "family_key", "obligations_satisfied",
                     "rejected", "forced_reads", "_wording_evidence_in",
                     "term", "exact_quote_verified", "record"):
            assert not hasattr(ev, gone), gone


# ═══════════════════════════════════════════════════════
# P3: evidence contract — retrieved/candidate/used 语义
# （O4-RP1: source_constraint/subject_authors 二手排除已删除——契约层无意图过滤;
#   二手是否被引用由 Main Agent 自主判断, O2 validator 只校验引用可核验性）
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
    def test_no_constraint_keeps_current_semantics(self):
        ans = "原句见【《政治学》· 第二章】。普莱希特的概括见《认识世界：古代与中世纪哲学》。"
        c = EC.build_evidence_contract(_f12_tool_log(), ans, "general", "zh")
        assert c["used_count"] >= 1

    def test_contract_signature_has_no_intent_params(self):
        # validator/契约不依赖用户意图分类（O4-RP1 §3）:
        # build_evidence_contract 签名中不得再有 source_constraint/subject_authors
        import inspect
        sig = inspect.signature(EC.build_evidence_contract)
        for gone in ("source_constraint", "subject_authors"):
            assert gone not in sig.parameters, gone

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
