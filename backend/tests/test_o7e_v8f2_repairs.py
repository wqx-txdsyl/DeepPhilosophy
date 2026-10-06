# -*- coding: utf-8 -*-
"""V8-F2: 三类已证明 production failure class 修复的确定性回归。

任务书要求的五个 synthetic 场景（全新 DEV-only, 零 V8 case 复用）:
  plan-only 拦截 / real research-plan 不误杀 / provider failover +
  irrelevant-only reformulation / no-op repair 检测与升级。
plan-only 与 no-op 用 production path 集成（真实 LangGraph 图 + 脚本化假 LLM,
与 test_o7e_final_diagnostic 同一 harness）; scholarly 门用 stub provider 单测。
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_langgraph as EG
import scholarly_sources as SS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o7e_final_diagnostic import (_run_lp, _done, _GOOD,
                                       _AnchorMissingAdapter, _FIN_PATCH)
from test_o2_final_ownership import _TOOLS_SCRIPT, _msg, _SENTINEL_FAKE

_PLAN = ("我先梳理一下：这个问题涉及相关学术争论。下一步我并行检索几个方向，"
         "定位真实文献记录。")


# ═══════════════════════════════════════════════════════
# 1. plan-only 检测器（纯确定性单元）
# ═══════════════════════════════════════════════════════
def test_a1_plan_preamble_detected():
    preamble = ("我先梳理一下已知与待核验的点：我记得以色列的论题。但这些都还只是"
                "我的记忆，属于工作假设。下一步我并行检索几个方向，定位真实文献记录。")
    assert EG._is_plan_only_terminal(preamble, "以色列的激进启蒙论题受到哪些批评？")


def test_a2_real_plan_request_never_blocked():
    plan_answer = ("研究维特根斯坦，我建议按以下顺序读：先读《逻辑哲学论》，"
                   "再读《哲学研究》，配合安斯康姆的导读。下一步我建议精读第 §§ 节。")
    assert not EG._is_plan_only_terminal(
        plan_answer, "想严肃研究维特根斯坦，应该按什么顺序读哪些文献？给我研究计划")


def test_a3_substantive_answer_not_blocked():
    substantive = ("黑格尔的「承认」既是伦理的也是逻辑的……如需深入，"
                   "您可以检索《精神现象学》第四章「自我意识的独立与依赖」。")
    assert not EG._is_plan_only_terminal(substantive, "黑格尔的承认概念是伦理的还是逻辑的？")


def test_a4_empty_candidate_not_blocked():
    assert not EG._is_plan_only_terminal("   ", "任意问题")


# ═══════════════════════════════════════════════════════
# 2. plan-only production 集成: 前言不发布, recovery 后实质回答发布
# ═══════════════════════════════════════════════════════
def test_b1_plan_only_preamble_not_published():
    preamble = ("我先梳理一下：这个问题涉及尼采的谱系学。下一步我将检索相关文献"
                "记录来核验，先并行检索几个方向。")
    evs, _chat = _run_lp("尼采谱系学", [_msg(preamble), _msg(_GOOD)])
    done = _done(evs)
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    tel = done.get("v8f2_telemetry") or {}
    assert tel.get("PLAN_ONLY_TERMINAL_BLOCKED") is True
    # 最终发布的候选是 recovery 后的实质回答, 不是前言
    hist = (done.get("validation") or {}).get("history") or []
    assert hist and hist[-1]["candidate_chars"] == len(_GOOD)
    assert answer.strip().endswith("评价。") or _GOOD in answer
    assert preamble not in answer


def test_b2_real_plan_request_published_normally():
    question = "想严肃研究维特根斯坦，应该按什么顺序读哪些文献？给我研究计划"
    plan_answer = ("建议顺序: 1.《逻辑哲学论》 2.《哲学研究》 3. 安斯康姆《维特根斯坦"
                   "〈哲学研究〉导读》。先读早期再读后期, 关注语言游戏概念的转变。")
    evs, _chat = _run_lp(question, [_msg(plan_answer)])
    done = _done(evs)
    tel = done.get("v8f2_telemetry") or {}
    assert tel.get("PLAN_ONLY_TERMINAL_BLOCKED") is False
    hist = (done.get("validation") or {}).get("history") or []
    assert hist and hist[0]["ok"] is True   # 计划型回答正常通过并发布


# ═══════════════════════════════════════════════════════
# 3. no-op repair: 相同候选 → NO_OP_REPAIR → 升级后实质修复
# ═══════════════════════════════════════════════════════
def test_c1_no_op_repair_detected_and_escalated():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(bad), _msg(bad), _msg(_GOOD)],
        adapter=_AnchorMissingAdapter())
    done = _done(evs)
    trace = (done.get("validation") or {}).get("repair_trace") or []
    tel = done.get("v8f2_telemetry") or {}
    assert len(trace) >= 2
    assert trace[0]["no_op_repair"] is True
    assert trace[0]["pre_repair_candidate_sha256"] == \
        trace[0]["post_repair_candidate_sha256"]
    assert trace[1].get("no_op_escalated") is True
    assert tel.get("REPAIR_NO_OP_COUNT") == 1
    assert tel.get("REPAIR_NO_OP_ESCALATED") == 1
    # escalation 后候选改变且 issue 消失, 无新 semantic issue
    hist = (done.get("validation") or {}).get("history") or []
    st = hist[-1].get("semantic_transition")
    assert hist[-1]["ok"] is True
    if st:
        assert st["summary"]["GENUINELY_NEW_ISSUE"] == 0
        assert st["summary"]["AMBIGUOUS"] == 0


# ═══════════════════════════════════════════════════════
# 4. scholarly relevance 门 + 一次有界 reformulation + failover
# ═══════════════════════════════════════════════════════
def _mk_rec(title, venue="", provider="crossref", rid=None):
    return {"doi": None, "provider_record_id": title[:20], "provider": provider,
            "cited_by": 1,
            "title": title, "container_title": venue,
            "authors": [], "publication_year": 2020,
            "publication_type": "journal-article",
            "identifiers": {}, "provenance": {"providers": [provider],
                                              "field_sources": {}},
            "access": {"level": "METADATA_ONLY"},
            "source_record_id": rid or f"fp-{abs(hash(title)) % 10 ** 12}"}


@pytest.fixture
def stub_cache(monkeypatch):
    cache = {"searches": {}, "records": {}}
    monkeypatch.setattr(SS, "_load_cache", lambda: cache)
    monkeypatch.setattr(SS, "_save_cache", lambda: None)
    monkeypatch.setattr(SS, "_local_results",
                        lambda q, limit, strict_only=False: [])
    return cache


def test_d1_irrelevant_only_triggers_reformulation(monkeypatch, stub_cache):
    calls = {"n": 0}

    def fake_crossref(query, limit=8, year_from=None, year_to=None):
        calls["n"] += 1
        if "Kant" in query or "康德" in query:
            return [_mk_rec("Critique of Pure Reason", "Kant-Studien")]
        return [_mk_rec("Critique of Pure Reason", "Kant-Studien")]  # 首轮全离题

    monkeypatch.setattr(SS, "search_crossref", fake_crossref)

    def fake_openalex(query, limit=8, year_from=None, year_to=None):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "blocked")

    monkeypatch.setattr(SS, "search_openalex", fake_openalex)

    out = SS.search_scholarship("Arendt banality of evil 平庸之恶")
    # 首轮离题 → 一次有界 reformulation（latin variant）→ 相关记录恢复
    assert out["query_reformulation"]["triggered"] is True
    assert "Arendt" in out["query_reformulation"]["variant_query"]
    assert out["relevance_gate"]["dropped_irrelevant"] >= 1
    assert all("Kant" not in (r.get("title") or "") for r in out["results"])


def test_d2_irrelevant_without_variant_not_fake_success(monkeypatch, stub_cache):
    def fake_crossref(query, limit=8, year_from=None, year_to=None):
        return [_mk_rec("Critique of Pure Reason", "Kant-Studien")]

    monkeypatch.setattr(SS, "search_crossref", fake_crossref)
    monkeypatch.setattr(SS, "search_openalex", fake_crossref)

    out = SS.search_scholarship("平庸之恶 档案批评")   # 无 latin 词 → 无 variant
    assert out["query_reformulation"]["triggered"] is False
    assert out["results"] == []            # 离题记录不冒充检索成功
    assert out["relevance_gate"]["dropped_irrelevant"] >= 1


def test_d3_provider_failover_keeps_path_alive(monkeypatch, stub_cache):
    def broken_crossref(query, limit=8, year_from=None, year_to=None):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "blocked")

    def good_openalex(query, limit=8, year_from=None, year_to=None):
        return [_mk_rec("Hannah Arendt and the banality of evil", "Journal of Genocide Research",
                        provider="openalex")]

    monkeypatch.setattr(SS, "search_crossref", broken_crossref)
    monkeypatch.setattr(SS, "search_openalex", good_openalex)

    out = SS.search_scholarship("Arendt banality evil")
    assert out["errors"] and out["errors"][0]["provider"] == "crossref"
    assert out["provider_failover"] is True
    assert any("banality" in (r.get("title") or "") for r in out["results"])


def test_d4_relevant_records_kept(monkeypatch, stub_cache):
    def fake_crossref(query, limit=8, year_from=None, year_to=None):
        return [_mk_rec("平庸之恶的当代争论", "伦理学研究")]

    monkeypatch.setattr(SS, "search_crossref", fake_crossref)
    monkeypatch.setattr(SS, "search_openalex", fake_crossref)

    out = SS.search_scholarship("平庸之恶 批评")
    assert out["relevance_gate"]["kept_relevant"] >= 1
    assert out["relevance_gate"]["dropped_irrelevant"] == 0


# ═══════════════════════════════════════════════════════
# V8-F2-R1 §1: round-local tool accounting + fail-closed
# ═══════════════════════════════════════════════════════
def test_r1_prior_tools_then_terminal_plan_still_blocked():
    # 前一轮真实执行了工具 → 累计 tool_log 非空; 末轮输出「下一步我会继续检索」
    # 且 0 tool → round-local 记账下必须仍被拦截
    evs, _chat = _run_lp(
        "言必有中出处",
        [_msg("需要定位原典核验。",
              [{"name": "search_books", "args": {"query": "言必有中 出处"}, "id": "c1"}]),
         _msg("结果已取得。下一步我会继续检索更多二手文献来核验这个说法。"),
         _msg(_GOOD)])
    done = _done(evs)
    tel = done.get("v8f2_telemetry") or {}
    assert tel.get("PLAN_ONLY_TERMINAL_BLOCKED") is True
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    assert "下一步我会继续检索" not in answer


def test_r1_stubborn_plan_exhaustion_fail_closed():
    # initial + recovery + 全部 repair 都返回 plan-only → 永不发布, 计划文本
    # 不得出现在任何 token 中, 以 validation_failed/error 非语义失败路径收口
    script = [_msg(_PLAN), _msg(_PLAN), _msg(_PLAN), _msg(_PLAN)]
    evs, _chat = _run_lp("尼采谱系学", script)
    tokens = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    assert _PLAN not in tokens
    assert not [e for e in evs if e.get("type") == "token"]
    assert any(e.get("type") == "validation_failed" for e in evs)
    assert any(e.get("type") == "error" for e in evs)
    done = _done(evs)
    tel = done.get("v8f2_telemetry") or {}
    assert tel.get("PLAN_ONLY_EXHAUSTION_FAIL_CLOSED") is True


def test_r1_literature_review_not_exempted():
    # 「给我写一份文献综述」要求成品——模型只输出「下一步我检索」必须拦截
    # （V8-F2-R1 §1: 文献综述/回顾/清单不再构成 plan-request 豁免）
    assert EG._is_plan_only_terminal(_PLAN, "给我写一份文献综述：阿伦特平庸之恶研究")


def test_r1_genuine_research_plan_still_exempt():
    assert not EG._is_plan_only_terminal(
        "建议顺序: 先读原著再读二手。", "给我一份研究计划：海德格尔存在与时间")


# ═══════════════════════════════════════════════════════
# V8-F2-R1 §2: no-op 在 effective candidate 上判定
# ═══════════════════════════════════════════════════════
_NOOP_PATCH = json.dumps({"patches": []}, ensure_ascii=False)   # 零 patch → 零文本变化


def test_r1_local_patch_effective_no_op_detected():
    # production LocalPatchAdapter（supported）: patch apply「成功」但
    # replacement 与原文相同 → effective candidate == pre → NO_OP_REPAIR
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg("结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"),
                         _msg(_NOOP_PATCH), _msg(_FIN_PATCH)],
        adapter=__import__("local_patch_runtime", fromlist=["LocalPatchAdapter"]).LocalPatchAdapter())
    done = _done(evs)
    trace = (done.get("validation") or {}).get("repair_trace") or []
    tel = done.get("v8f2_telemetry") or {}
    assert trace[0]["repair_output_mode"] == "LOCAL_PATCH"
    assert trace[0]["no_op_repair"] is True
    assert trace[0]["no_op_scope"] == "LOCAL_PATCH_EFFECTIVE"
    assert trace[0]["pre_repair_candidate_sha256"] == \
        trace[0]["post_repair_candidate_sha256"]
    assert trace[1].get("no_op_escalated") is True
    assert tel.get("REPAIR_NO_OP_COUNT") == 1
    assert tel.get("REPAIR_NO_OP_ESCALATED") == 1


def test_r1_local_patch_apply_failure_fallback_is_no_op():
    # patch 解析/应用失败 → 回退 pre candidate → effective post hash == pre
    # → no-op 事实正确记录并触发升级
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg("结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"),
                         _msg("这不是一个合法的 patch JSON。"),
                         _msg(_FIN_PATCH)],
        adapter=__import__("local_patch_runtime", fromlist=["LocalPatchAdapter"]).LocalPatchAdapter())
    done = _done(evs)
    trace = (done.get("validation") or {}).get("repair_trace") or []
    assert trace[0]["repair_output_mode"] == "LOCAL_PATCH"
    assert trace[0]["no_op_repair"] is True
    assert trace[0]["pre_repair_candidate_sha256"] == \
        trace[0]["post_repair_candidate_sha256"]
    assert trace[1].get("no_op_escalated") is True


# ═══════════════════════════════════════════════════════
# V8-F2-R1 §3: 零结果 reformulation + 中文 canonical bilingual 路径
# ═══════════════════════════════════════════════════════
def test_r1_zero_result_still_triggers_reformulation(monkeypatch, stub_cache):
    calls = {"n": 0}

    def empty_then_relevant(query, limit=8, year_from=None, year_to=None):
        calls["n"] += 1
        # 首轮（含 CJK 的原 query）零结果; variant 轮（纯 latin）返回相关记录
        if "平庸" not in query:
            return [_mk_rec("Hannah Arendt and the banality of evil",
                            "Journal of Genocide Research")]
        return []

    monkeypatch.setattr(SS, "search_crossref", empty_then_relevant)
    monkeypatch.setattr(SS, "search_openalex", empty_then_relevant)

    out = SS.search_scholarship("Arendt banality of evil 平庸之恶")
    assert out["query_reformulation"]["triggered"] is True   # 零结果也重试
    assert calls["n"] == 4                                   # 2 provider × 恰一次 retry
    assert any("banality" in (r.get("title") or "") for r in out["results"])


def test_r1_chinese_query_bilingual_canonical_variant(monkeypatch, stub_cache):
    # 中文-only query 无 latin token → 经本地 canonical/alias 元数据
    # （匹配 CJK bigram 的 curated 记录的英文身份）形成英文 variant;
    # 零硬编码、零模型猜译。
    def fake_local(q, limit=24, strict_only=False):
        rec = _mk_rec("阿伦特与艾希曼审判的当代争论 平庸之恶", "伦理学研究",
                      provider="local_curated")
        rec["authors"] = [{"name": "Hannah Arendt"}]
        return [rec]

    def fake_crossref(query, limit=8, year_from=None, year_to=None):
        if "arendt" in query.lower():
            return [_mk_rec("Hannah Arendt revisited: Eichmann and the banality of evil",
                            "Political Theory")]
        return []

    monkeypatch.setattr(SS, "_local_results", fake_local)
    monkeypatch.setattr(SS, "search_crossref", fake_crossref)

    out = SS.search_scholarship("平庸之恶 批评")
    assert out["query_reformulation"]["triggered"] is True
    assert "arendt" in (out["query_reformulation"]["variant_query"] or "").lower()
    assert any("Arendt" in (r.get("title") or "") for r in out["results"])


# ═══════════════════════════════════════════════════════
# V8-F2-R2 §1: repair 生成的 plan-only 同样拦截（每候选独立判定）
# ═══════════════════════════════════════════════════════
def test_r2_repair_generated_plan_only_blocked():
    # initial 是含伪引文的实质回答（validator FAIL）→ repair 1 返回计划前言
    # （validator 本身 ok）→ plan gate 必须独立拦截, 不得发布;
    # repair 2（升级反馈后）给出实质回答 → 发布
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(bad), _msg(_PLAN), _msg(_GOOD)],
        adapter=_AnchorMissingAdapter())
    done = _done(evs)
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    tel = done.get("v8f2_telemetry") or {}
    assert tel.get("PLAN_ONLY_TERMINAL_BLOCKED") is True
    assert _PLAN not in answer
    assert _GOOD in answer


def test_r2_repair_generated_plan_exhaustion_fail_closed():
    # repair 全部只产出计划前言 → 耗尽后 FAIL-CLOSED, 计划零外流
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(bad), _msg(_PLAN), _msg(_PLAN), _msg(_PLAN)],
        adapter=_AnchorMissingAdapter())
    tokens = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    assert _PLAN not in tokens and _SENTINEL_FAKE not in tokens
    assert any(e.get("type") == "error" for e in evs)
    tel = (_done(evs).get("v8f2_telemetry") or {})
    assert tel.get("PLAN_ONLY_EXHAUSTION_FAIL_CLOSED") is True


# ═══════════════════════════════════════════════════════
# V8-F2-R2 §2: completion 语言不再一刀切豁免
# ═══════════════════════════════════════════════════════
def test_r2_past_completion_plus_future_intent_still_blocked():
    assert EG._is_plan_only_terminal(
        "我已经找到了一些初步线索，但还不能下结论。下一步我会检索正式文献进行核实。",
        "研究问题")


def test_r2_genuinely_completed_answer_still_published():
    # 无未来宣告的完成型回答照常发布
    assert not EG._is_plan_only_terminal(
        "我已经查到相关材料。核心分歧有三点：第一……第二……第三……", "研究问题")


def test_r2_completion_after_intent_counts_as_delivery():
    # O4-T5 实况: 意图句在前、完成+实质回答在后 → 非 plan-only
    assert not EG._is_plan_only_terminal(
        "让我先检索一下材料。现在已经查到了：荒诞是裂隙。", "什么是荒诞？")


# ═══════════════════════════════════════════════════════
# V8-F2-R3: completion keyword ≠ substantive delivery
# ═══════════════════════════════════════════════════════
def test_r3_completion_with_empty_result_still_plan_only():
    assert EG._is_plan_only_terminal("下一步我会检索。现在已经查到了。", "研究问题")


def test_r3_completion_colon_no_body_still_plan_only():
    assert EG._is_plan_only_terminal("下一步我会检索。结果如下：", "研究问题")


def test_r3_search_complete_no_body_still_plan_only():
    assert EG._is_plan_only_terminal("下一步我会检索。检索完成。", "研究问题")


def test_r3_punctuation_only_after_completion_still_plan_only():
    assert EG._is_plan_only_terminal("下一步我会检索。现在已经查到了。！！？！", "研究问题")


def test_r3_another_plan_after_completion_still_plan_only():
    assert EG._is_plan_only_terminal(
        "下一步我会检索。现在已经查到了。下一步我会继续查证。", "研究问题")


def test_r3_substantive_result_body_after_completion_not_blocked():
    assert not EG._is_plan_only_terminal(
        "让我先检索一下材料。现在已经查到了：荒诞是主体期待意义而世界沉默之间的裂隙。",
        "什么是荒诞？")
