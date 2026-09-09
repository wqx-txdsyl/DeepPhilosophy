# -*- coding: utf-8 -*-
"""O7-E RCA-2 Quote Action Semantics Split: Q1-Q12 回归。

锁死（Reviewer 2026-09-09 RCA-2 任务书 §必测回归）:
  Q1  quote COPY_SLICE 仍只替换 content span, wrapper 保留
  Q2  quote PARAPHRASE_CLAIM 替换 claim span
  Q3  blockquote paraphrase 后 > 不再存在于目标 claim
  Q4  quoted/leadin paraphrase 后原 quote delimiters 不再包住 replacement
  Q5  PARAPHRASE_CLAIM replacement 被 QuoteBound 识别成新 quote → reject
  Q6  quote REPLACE_TEXT → reject（INVALID_ACTION_FOR_QUOTE, 零兼容）
  Q7  citation REPLACE_TEXT 行为不变
  Q8  citation COPY_SLICE 行为不变
  Q9  target claim 外字节完全不变
  Q10 目标外已验证 quote byte-preserved
  Q11 intentional demotion 不计 UNINTENTIONAL_QUOTE_WRAPPER_LOSS
  Q12 LP anchor/starvation metric 只统计真实 LOCAL_PATCH attempt
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import repair_context as RC
import quote_bound as QB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o7e_h2c_contract import CAND, _raw_log, _sha, _bundles_and_catalog
from test_o7e_final_diagnostic import case_result
from o7e_rca1_hook_eval import LocalPatchAdapter

QUOTE_B = next(b for b in _bundles_and_catalog()[1]
               if b["code"] != "UNVERIFIED_CITATION")
CITE_B = next(b for b in _bundles_and_catalog()[1]
              if b["code"] == "UNVERIFIED_CITATION")


def _apply(cand, patch_obj, bundles, catalog, sha=None):
    return RC.apply_main_agent_patches_v2(
        cand, json.dumps(patch_obj, ensure_ascii=False), bundles, catalog,
        context_candidate_sha=sha)


# ── Q1: quote COPY_SLICE content span, wrapper 保留 ──
def test_q1_quote_copy_slice_content_only_wrapper_kept():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] != "UNVERIFIED_CITATION")
    s = catalog[qt["issue_id"]][0]
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": qt["issue_id"], "action": "COPY_SLICE",
         "slice_id": s["slice_id"]}]}, [qt], catalog)
    assert new is not None, errs
    a = qt["anchor"]
    cs = a["content_start"]
    # content span = slice 精确字节
    assert new[cs:cs + len(s["text"])] == s["text"]
    # wrapper（> 与 「」）原样保留
    assert new[:a["claim_start"]] == CAND[:a["claim_start"]]
    assert CAND[a["claim_start"]:a["content_start"]] in new   # 开 wrapper
    assert CAND[a["content_end"]:a["claim_end"]] in new       # 闭 wrapper


# ── Q2/Q3: quote PARAPHRASE_CLAIM 替换整个 claim span ──
_PARA = "孔子批评鲁人改建长府，并以闵子骞为例说明行事当遵循成规旧制、言谈务求切中要害。"


def test_q2_quote_paraphrase_claim_replaces_claim_span():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] != "UNVERIFIED_CITATION")
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": qt["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": _PARA}]}, [qt], catalog)
    assert new is not None, errs
    assert _PARA in new
    a = qt["anchor"]
    assert CAND[a["claim_start"]:a["claim_end"]] not in new


def test_q3_blockquote_paraphrase_removes_blockquote_marker():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] != "UNVERIFIED_CITATION")
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": qt["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": _PARA}]}, [qt], catalog)
    assert new is not None
    assert "> 「" not in new            # 目标 blockquote 前缀随 claim 一并移除


# ── Q4: leadin（弯引号）paraphrase 后 delimiters 不再包住 replacement ──
_FAKE_LONG = "伪造的引文内容足够长以触发核验机制"
CAND_LEADIN = "原文如下：“" + _FAKE_LONG + "”他说完便停了下来。"


def _leadin_fixtures():
    v = _mk_validation_local(CAND_LEADIN)
    bundles = RC.build_repair_issue_bundles(CAND_LEADIN, v, _raw_log())
    issues = v.as_dict().get("issues", [])
    per_loc = {f"vi_{k+1}": (i or {}).get("locator") or ""
               for k, i in enumerate(issues)}
    catalog = RC.build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    return bundles, catalog


def _mk_validation_local(candidate):
    from final_validator import validate_final_candidate
    return validate_final_candidate(candidate, raw_tool_log=_raw_log(),
                                    fallback_log=[], language="zh")


def test_q4_leadin_paraphrase_removes_delimiters():
    bundles, catalog = _leadin_fixtures()
    assert bundles, "fixture 必须产生 quote issue"
    qt = bundles[0]
    new, errs = _apply(CAND_LEADIN, {"patches": [
        {"issue_id": qt["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": "他转述完那句原话便停了下来。"}]}, [qt], catalog)
    assert new is not None, errs
    assert "“" not in new and "”" not in new
    assert _FAKE_LONG not in new


# ── Q5: PARAPHRASE 不得重新制造 quote ──
def test_q5_paraphrase_containing_verbatim_quote_rejected():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] != "UNVERIFIED_CITATION")
    bad = "这是转述：“鲁人为长府，闵子骞曾如此批评改建。”"
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": qt["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": bad}]}, [qt], catalog)
    assert new is None
    assert any("PARAPHRASE_CONTAINS_VERBATIM_QUOTE" in e for e in errs)


# ── Q6: quote REPLACE_TEXT 非法（零兼容）──
def test_q6_quote_replace_text_invalid():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] != "UNVERIFIED_CITATION")
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": qt["issue_id"], "action": "REPLACE_TEXT",
         "replacement_text": "任何文字"}]}, [qt], catalog)
    assert new is None
    assert any("INVALID_ACTION_FOR_QUOTE" in e for e in errs)


# ── Q7/Q8: citation 动作行为不变 ──
def test_q7_citation_replace_text_unchanged():
    _, bundles, catalog = _bundles_and_catalog()
    ct = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": ct["issue_id"], "action": "REPLACE_TEXT",
         "replacement_text": "【《论语·先进》】"}]}, [ct], catalog)
    assert new is not None, errs
    a = ct["anchor"]
    cs = a.get("content_start", a.get("start"))
    assert new[cs:cs + len("【《论语·先进》】")] == "【《论语·先进》】"


CAND_CITE = ("引言测试正文，讨论《论语》的成书与流传。\n\n"
             "书中另有说法，见【《论语·八佾》】。"
             "结尾一段正文保持结构完整。")

# 仅 search 证据——citation ref（ev_N）→ citation payload snippet → source/slices
_LOG_SEARCH = [{"name": "search_books", "args": {"query": "论语 先进篇"},
                "result_full": {"results": [
                    {"book_title": "论语", "chapter_title": "先进篇",
                     "book_id": "lunyu", "chapter_idx": 13,
                     "snippet": "鲁人为长府，闵子骞曰：仍旧贯如之何？何必改作？",
                     "score": 0.9}],
                    "query": "论语 先进篇"}}]


def test_q8_citation_copy_slice_unchanged():
    from final_validator import validate_final_candidate
    CAND_CITE8 = ("引言测试正文，讨论《论语》的成书与流传。\n\n"
                  "书中另有说法，见【《论语》·八佾】。"
                  "结尾一段正文保持结构完整。")
    v = validate_final_candidate(CAND_CITE8, raw_tool_log=_LOG_SEARCH,
                                 fallback_log=[], language="zh")
    issues = v.as_dict().get("issues", [])
    assert any(i.get("code") == "UNVERIFIED_CITATION" for i in issues)
    bundles = RC.build_repair_issue_bundles(CAND_CITE8, v, _LOG_SEARCH)
    per_loc = {f"vi_{k+1}": (i or {}).get("locator") or ""
               for k, i in enumerate(issues)}
    catalog = RC.build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    ct = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    assert ct.get("source"), "book 命中的 citation 必须解析出 source（ev ref → snippet）"
    assert ct["evidence_resolution"] == "RESOLVED"
    slices = catalog.get(ct["issue_id"]) or []
    assert slices
    new, errs = _apply(CAND_CITE8, {"patches": [
        {"issue_id": ct["issue_id"], "action": "COPY_SLICE",
         "slice_id": slices[0]["slice_id"]}]}, [ct], catalog)
    assert new is not None, errs


# ── Q9: target claim 外字节完全不变 ──
def test_q9_bytes_outside_target_claim_unchanged():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] != "UNVERIFIED_CITATION")
    new, errs = _apply(CAND, {"patches": [
        {"issue_id": qt["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": _PARA}]}, [qt], catalog)
    assert new is not None
    a = qt["anchor"]
    expected = CAND[:a["claim_start"]] + _PARA + CAND[a["claim_end"]:]
    assert new == expected


# ── Q10/Q11: 目标外已验证 quote 保护 + intentional demotion 遥测 ──
_REAL = "夫人不言，言必有中"
CAND_2Q = ("孔子曾言，“" + _REAL + "。”此为库中可核验的真引。\n\n"
           "结论：原文如下——\n\n> 「" + _FAKE_LONG + "」\n")


def _two_quote_ctx():
    v = _mk_validation_local(CAND_2Q)
    bundles = RC.build_repair_issue_bundles(CAND_2Q, v, _raw_log())
    issues = v.as_dict().get("issues", [])
    assert len(bundles) == 1 and bundles[0]["code"] == "UNSUPPORTED_EXACT_QUOTE"
    per_loc = {f"vi_{k+1}": (i or {}).get("locator") or ""
               for k, i in enumerate(issues)}
    catalog = RC.build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    fps = [RC.issue_fingerprint((i or {}).get("code"),
                                (i or {}).get("locator") or "",
                                (i or {}).get("evidence_ref")) for i in issues]
    ctx = {"bundles": bundles, "catalog": catalog,
           "candidate_sha": _sha(CAND_2Q), "issue_fps": fps,
           "raw_tool_log": _raw_log()}
    return bundles, catalog, ctx


def test_q10_preexisting_verified_quote_outside_target_preserved():
    bundles, catalog, ctx = _two_quote_ctx()
    ad = LocalPatchAdapter()
    patch = json.dumps({"patches": [
        {"issue_id": bundles[0]["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": "此处原为伪引，现改为普通转述不再作为原文呈现。"}]},
        ensure_ascii=False)
    new, errs, tel = ad.parse_and_apply(CAND_2Q, patch, ctx)
    assert new is not None, errs
    assert _REAL in new                    # 目标外已验证 quote 原样保留
    assert tel["preexisting_verified_quotes_lost"] == 0


def test_q11_intentional_demotion_not_counted_as_wrapper_loss():
    bundles, catalog, ctx = _two_quote_ctx()
    ad = LocalPatchAdapter()
    patch = json.dumps({"patches": [
        {"issue_id": bundles[0]["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": "此处原为伪引，现改为普通转述不再作为原文呈现。"}]},
        ensure_ascii=False)
    new, errs, tel = ad.parse_and_apply(CAND_2Q, patch, ctx)
    assert new is not None, errs
    assert tel["intentional_quote_to_paraphrase"] == 1
    assert tel["unintentional_quote_wrapper_loss"] == 0


# ── Q12: LP anchor/starvation 口径只统计真 LOCAL_PATCH attempt ──
def _synthetic_evs(trace, hist):
    return [{"type": "done", "validation": {
        "history": hist, "result": {"ok": True, "issues": []},
        "repair_trace": trace, "repairs_used": len(trace)}}]


def test_q12_metric_denominators_split_prep_vs_lp():
    trace = [
        # attempt1: preflight 拦截（unresolved anchor）→ FULL_REWRITE——
        # 其 bundle 不得进入 LP 硬门口径（H07 实况）
        {"repair_output_mode": "FULL_REWRITE",
         "bundles": [{"anchor": False, "has_evidence_ref": True,
                      "evidence_resolution": "UNRESOLVED", "linked_source": False}],
         "local_patch": {}, "finalization": {}},
        {"repair_output_mode": "LOCAL_PATCH",
         "bundles": [{"anchor": True, "has_evidence_ref": True,
                      "evidence_resolution": "RESOLVED", "linked_source": True},
                     {"anchor": True, "has_evidence_ref": False,
                      "evidence_resolution": "NOT_REQUIRED", "linked_source": False}],
         "local_patch": {}, "finalization": {}}]
    hist = [{"ok": False, "issue_codes": ["UNSUPPORTED_EXACT_QUOTE"],
             "issue_fingerprints": ["f1"], "candidate_chars": 40},
            {"ok": True, "issue_codes": [], "issue_fingerprints": [],
             "candidate_chars": 40}]
    r = case_result("q12", _synthetic_evs(trace, hist))
    assert r["PREP_ANCHOR_TOTAL"] == 3 and r["PREP_ANCHOR_RESOLVED"] == 2
    assert r["LP_ANCHOR_TOTAL"] == 2 and r["LP_ANCHOR_RESOLVED"] == 2
    assert r["LOCAL_PATCH_ANCHOR_RESOLUTION_RATE"] == 1.0   # 硬门口径不被 preflight 拉低
    assert r["LINKED_EVIDENCE_REQUIRED"] == 1
    assert r["LINKED_EVIDENCE_PRESENT"] == 1
    assert r["LINKED_EVIDENCE_STARVATION"] == 0   # ref+UNRESOLVED 在 FULL_REWRITE attempt
    assert r["BEST_EFFORT_SOURCE_MISSING"] == 1   # 无 ref 且无 source（best-effort 未命中）


def test_q12b_lp_attempt_starvation_still_counted():
    trace = [
        {"repair_output_mode": "LOCAL_PATCH",
         "bundles": [{"anchor": True, "has_evidence_ref": True,
                      "evidence_resolution": "UNRESOLVED", "linked_source": False}],
         "local_patch": {}, "finalization": {}}]
    hist = [{"ok": False, "issue_codes": ["UNVERIFIED_CITATION"],
             "issue_fingerprints": ["f1"], "candidate_chars": 40},
            {"ok": True, "issue_codes": [], "issue_fingerprints": [],
             "candidate_chars": 40}]
    r = case_result("q12b", _synthetic_evs(trace, hist))
    # 真正的 starvation: ref 存在 + 解析失败 + 发生在 LOCAL_PATCH attempt
    assert r["LINKED_EVIDENCE_REQUIRED"] == 1
    assert r["LINKED_EVIDENCE_PRESENT"] == 0
    assert r["LINKED_EVIDENCE_STARVATION"] == 1
    assert r["LOCAL_PATCH_ANCHOR_RESOLUTION_RATE"] == 1.0
