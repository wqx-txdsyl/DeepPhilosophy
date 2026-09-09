# -*- coding: utf-8 -*-
"""O7-E RCA-2 H1 §9: full-engine LOCAL_PATCH evaluation RUN。

通过 stream_agent(_evaluation_repair_adapter=LocalPatchAdapter) 注入——
真实工具循环/真实预算/repair_mode 语义（§6）; 生产默认 None 行为不变。

FINAL-DIAG CLOSURE 变更:
  §1 adapter 收敛为 candidate-aware prepare 单入口（supported 才进 LOCAL_PATCH）
  §2 finalization patch 由 engine 从 pending 收口（本文件只消费 trace 事实）
  §4 R1/R2 fingerprint 集合差以 validation.history 为真源
  §4b TERMINAL_CANDIDATE_EMPTY / PUBLIC_RESPONSE_EMITTED 取代 TERMINAL_EMPTY_ANSWER
  §5 patch action 遥测（identity+动作, 零正文）
  §6 Hard Gate telemetry 全字段 per-case + summary
"""
import asyncio
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import engine_langgraph as EG
import repair_context as RC
import quote_bound as QB
import o7e_candidate_config as CC
import routes.agent as AG


class LocalPatchAdapter:
    """FINAL-DIAG §1: prepare 单入口——三条件 preflight（codes/anchors/prompt）
    由 RC.prepare_local_patch 判定; supported=False 时 engine 必须走 FULL_REWRITE。"""

    def prepare(self, candidate, validation, raw_tool_log, prev_errors=None):
        prep = RC.prepare_local_patch(candidate, validation, raw_tool_log, prev_errors)
        issues = validation.as_dict().get("issues", [])
        fps = [RC.issue_fingerprint((i or {}).get("code"),
                                    (i or {}).get("locator") or "",
                                    (i or {}).get("evidence_ref"))
               for i in issues]
        out = dict(prep)
        out["pre_patch_candidate"] = candidate
        out["issue_fps"] = fps
        return out

    def parse_and_apply(self, pre_candidate, model_output, ctx):
        if not ctx.get("rebind_ok", True):
            return None, ["LOCAL_PATCH_UNSUPPORTED: rebind"], {}
        telemetry = []
        new, errs = RC.apply_main_agent_patches_v2(
            pre_candidate, model_output, ctx.get("bundles") or [],
            ctx.get("catalog") or {},
            context_candidate_sha=ctx.get("candidate_sha"), telemetry=telemetry)
        # §5: 指纹补全（bundle 序 == issue 序, vi_N ↔ fps[N-1]）; 零正文记录
        fps = ctx.get("issue_fps") or []
        for rec in telemetry:
            try:
                n = int(str(rec.get("issue_id", "")).split("_")[-1])
                rec["issue_fingerprint"] = fps[n - 1] if 1 <= n <= len(fps) else None
            except Exception:
                rec["issue_fingerprint"] = None
        # RCA-2 §wrapper 遥测: 有意降级 ≠ 非预期 wrapper 丢失
        intentional = 0
        unintentional_loss = 0
        nt_violations = 0
        target_spans = []
        if new is not None:
            target_claims = []
            for rec in telemetry:
                b = next((x for x in (ctx.get("bundles") or [])
                          if x["issue_id"] == rec.get("issue_id")), None)
                a = (b or {}).get("anchor") or {}
                qs, qe = a.get("claim_start"), a.get("claim_end")
                cs, ce = a.get("content_start"), a.get("content_end")
                if None not in (qs, qe):
                    target_claims.append((qs, qe))
                if rec.get("action") == "PARAPHRASE_CLAIM":
                    intentional += 1
                    if None not in (qs, qe):
                        target_spans.append((qs, qe))
                    # 降级机械事实: wrapper 子串应从新候选消失
                    if (qs is not None and cs is not None and qs < cs
                            and pre_candidate[qs:cs]
                            and pre_candidate[qs:cs] in new):
                        rec["wrapper_retained"] = True
                    continue
                if cs is None or ce is None:
                    continue
                target_spans.append((cs, ce))
                if rec.get("anchor_kind") != "quote":
                    continue
                # COPY_SLICE(quote): wrapper 必须保留——消失 = 非预期丢失
                if qs is not None and qs < cs and pre_candidate[qs:cs] \
                        and pre_candidate[qs:cs] not in new:
                    unintentional_loss += 1
                if qe is not None and ce is not None and ce < qe \
                        and pre_candidate[ce:qe] and pre_candidate[ce:qe] not in new:
                    unintentional_loss += 1
            if RC.non_target_changed_chars(pre_candidate, new,
                                           target_spans) != 0:
                nt_violations = 1
            # 目标外已验证 quote byte-preserved（anti-gaming: 不许顺手删别人引文）
            lost = 0
            raw_log = ctx.get("raw_tool_log")
            if raw_log is not None:
                audit = QB.audit_quotes(pre_candidate, raw_log)
                ext = QB.extract_quotes(pre_candidate)
                for e, q in zip(audit.get("entries", []), ext):
                    if e.get("verification_state") not in ("VERIFIED_EXACT",
                                                           "VERIFIED_NEAR"):
                        continue
                    qs2, qe2 = q.get("char_start"), q.get("char_end")
                    if qs2 is None:
                        continue
                    if any(not (qe2 <= ts or qs2 >= te)
                           for ts, te in target_claims):
                        continue
                    if q.get("text") not in new:
                        lost += 1
        else:
            lost = 0
            nt_violations = 0
        return new, (errs or []), {
            "actions": telemetry,
            "intentional_quote_to_paraphrase": intentional,
            "unintentional_quote_wrapper_loss": unintentional_loss,
            "preexisting_verified_quotes_lost": lost,
            "non_target_changed": nt_violations}


def _protocol_shas():
    src = open(os.path.join(ROOT, "backend", "engine_langgraph.py"),
               encoding="utf-8").read()
    lp = src.split('LOCAL_PATCH_SYSTEM_PROTOCOL = """')[1].split('"""')[0]
    fr = src.split('REPAIR_SYSTEM_PROTOCOL = """')[1].split('"""')[0]
    return {"LOCAL_PATCH": hashlib.sha256(lp.encode()).hexdigest()[:16],
            "FULL_REWRITE": hashlib.sha256(fr.encode()).hexdigest()[:16]}


def classify_history(hist):
    """FINAL-DIAG §4: R1/R2 集合差——真源 validation.history 的 issue_fingerprints
    （initial / after R1 / after R2-terminal 每 state 都有）; 不从 repair_trace 猜。"""
    states = [set(h.get("issue_fingerprints") or []) for h in (hist or [])]
    out = {}
    for k in range(1, len(states)):
        before, after = states[k - 1], states[k]
        out[f"R{k}"] = {"resolved": sorted(before - after),
                        "persisted": sorted(before & after),
                        "introduced": sorted(after - before)}
    return out


QUOTE_CODES = {"UNSUPPORTED_EXACT_QUOTE", "NEAR_QUOTE_NOT_MARKED", "STITCHED_QUOTE"}


def resolution_attribution(cls, hist, trace):
    """RCA-2 报告口径: quote issue 被哪个 action 修好 / paraphrase 轮是否引入新 quote。"""
    by_copy = by_para = para_introduced = 0
    for k in range(1, len(hist)):
        r = cls.get(f"R{k}")
        att = trace[k - 1] if k - 1 < len(trace) else None
        if not r or not att:
            continue
        acts = list((att.get("local_patch") or {}).get("actions") or [])
        acts += list((att.get("finalization") or {}).get("actions") or [])
        fp2act = {a["issue_fingerprint"]: a.get("action")
                  for a in acts if a.get("issue_fingerprint")}
        fp2code_before = dict(zip(hist[k - 1].get("issue_fingerprints") or [],
                                  hist[k - 1].get("issue_codes") or []))
        for fp in r["resolved"]:
            if fp2code_before.get(fp) in QUOTE_CODES:
                if fp2act.get(fp) == "COPY_SLICE":
                    by_copy += 1
                elif fp2act.get(fp) == "PARAPHRASE_CLAIM":
                    by_para += 1
        if any(a.get("action") == "PARAPHRASE_CLAIM" for a in acts):
            fp2code_after = dict(zip(hist[k].get("issue_fingerprints") or [],
                                     hist[k].get("issue_codes") or []))
            para_introduced += sum(
                1 for fp in set(r["introduced"])
                if fp2code_after.get(fp) in QUOTE_CODES)
    return by_copy, by_para, para_introduced


def case_result(case_id, evs):
    """per-case 硬门遥测聚合（纯函数——Q12/F11/F12 直接可测）。
    RCA-2 §metric: anchor/starvation 拆 PREP（诊断） vs LP（硬门）两套口径。"""
    done = next((e for e in reversed(evs) if e.get("type") == "done"), {})
    val = done.get("validation") or {}
    hist = val.get("history") or []
    trace = val.get("repair_trace") or []
    final_codes = [i.get("code") for i in val.get("result", {}).get("issues", [])]
    last_fail = max((i for i, e in enumerate(evs)
                     if e.get("type") == "validation_failed"), default=-1)
    answer = "".join(e.get("content", "") for i, e in enumerate(evs)
                     if e.get("type") == "token" and i > last_fail)
    lp_used = [t for t in trace if t.get("local_patch")]
    fin_rows = [t.get("finalization") for t in trace if t.get("finalization")]
    lp_attempts = [t for t in trace if t.get("repair_output_mode") == "LOCAL_PATCH"]
    fr_attempts = [t for t in trace if t.get("repair_output_mode") == "FULL_REWRITE"]
    pshas = _protocol_shas()
    prep_rows = [b for t in trace for b in (t.get("bundles") or [])]
    lp_rows = [b for t in lp_attempts for b in (t.get("bundles") or [])]
    prep_total = len(prep_rows)
    prep_res = sum(1 for b in prep_rows if b.get("anchor"))
    lp_total = len(lp_rows)
    lp_res = sum(1 for b in lp_rows if b.get("anchor"))
    # evidence 口径（仅 LP attempt; ref 缺失 = NOT_REQUIRED, 不入 starvation 分母）
    ev_required = sum(1 for b in lp_rows if b.get("has_evidence_ref"))
    ev_present = sum(1 for b in lp_rows if b.get("evidence_resolution") == "RESOLVED")
    ev_starved = sum(1 for b in lp_rows if b.get("has_evidence_ref")
                     and b.get("evidence_resolution") == "UNRESOLVED")
    best_effort_missing = sum(1 for b in lp_rows if not b.get("has_evidence_ref")
                              and not b.get("linked_source"))
    ovs = [b.get("source_overlap") for b in lp_rows
           if isinstance(b.get("source_overlap"), (int, float))]
    coverages = [t["lp_gate"]["prompt_issue_coverage"] for t in lp_attempts
                 if isinstance(t.get("lp_gate", {}).get("prompt_issue_coverage"),
                               (int, float))]
    cls = classify_history(hist)
    by_copy, by_para, para_introduced = resolution_attribution(cls, hist, trace)
    all_patch_actions = [a for t in lp_used
                         for a in (t["local_patch"].get("actions") or [])] + \
                        [a for f in fin_rows
                         for a in (f.get("actions") or [])]
    nt_violations = sum(
        1 for t in trace
        if (t.get("local_patch") or {}).get("non_target_changed")
        or (t.get("finalization") or {}).get("non_target_changed"))
    return {"case_id": case_id,
            "published": bool(answer.strip()) and bool(val.get("result", {}).get("ok")),
            "repairs": val.get("repairs_used", 0),
            "issue_counts": [len(h.get("issue_codes") or []) for h in hist],
            "fingerprint_classification": cls,
            "PREP_ANCHOR_TOTAL": prep_total,
            "PREP_ANCHOR_RESOLVED": prep_res,
            "LP_ANCHOR_TOTAL": lp_total,
            "LP_ANCHOR_RESOLVED": lp_res,
            "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE": round(lp_res / lp_total, 3)
                                                  if lp_total else None,
            "PROMPT_ISSUE_COVERAGE": round(sum(coverages) / len(coverages), 3)
                                     if coverages else None,
            "LINKED_EVIDENCE_REQUIRED": ev_required,
            "LINKED_EVIDENCE_PRESENT": ev_present,
            "LINKED_EVIDENCE_STARVATION": ev_starved,
            "BEST_EFFORT_SOURCE_MISSING": best_effort_missing,
            "UNKNOWN_SLICE_IDS": sum(1 for t in lp_used
                                     for e in (t["local_patch"].get("errors") or [])
                                     if "UNKNOWN_SLICE_ID" in str(e)),
            "INTENTIONAL_QUOTE_TO_PARAPHRASE": sum(
                (t.get("local_patch") or {}).get("intentional_quote_to_paraphrase") or 0
                for t in trace),
            "UNINTENTIONAL_QUOTE_WRAPPER_LOSS": sum(
                (t.get("local_patch") or {}).get("unintentional_quote_wrapper_loss") or 0
                for t in trace),
            "PREEXISTING_VERIFIED_QUOTES_OUTSIDE_TARGET_LOST": sum(
                (t.get("local_patch") or {}).get("preexisting_verified_quotes_lost") or 0
                for t in trace),
            "NON_TARGET_TEXT_CHANGED_CHARS": nt_violations,
            "SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE":
                round(sum(1 for v in ovs if v > 0) / len(ovs), 3) if ovs else None,
            "PATCH_FINALIZATION_INVOCATIONS": len(fin_rows),
            "FINALIZATION_TOOL_CALLS": sum(f.get("tool_calls") or 0 for f in fin_rows),
            "VALIDATOR_EMPTY_FINAL": "EMPTY_FINAL" in final_codes,
            # 终态候选空 ≠ 未发布——两个独立机械事实
            "TERMINAL_CANDIDATE_EMPTY": bool(hist) and
                                        (hist[-1].get("candidate_chars") or 0) == 0,
            "PUBLIC_RESPONSE_EMITTED": bool(answer.strip()),
            "UNSUPPORTED_PREP_TO_LOCAL_PATCH": sum(
                1 for t in trace if t.get("repair_output_mode") == "LOCAL_PATCH"
                and t.get("lp_gate", {}).get("supported") is False),
            "BLANK_LOCAL_PATCH_PROMPT_INVOCATIONS": sum(
                1 for t in lp_attempts if not (t.get("lp_prompt_chars") or 0)),
            "LOCAL_PATCH_TRIGGERED": bool(lp_attempts),
            "lp_applied": sum(1 for t in lp_used
                              if t["local_patch"].get("applied")),
            "lp_errors": [e for t in lp_used
                          for e in (t["local_patch"].get("errors") or [])][:3],
            "REPAIR_OUTPUT_MODES": [t.get("repair_output_mode") for t in trace],
            "LOCAL_PATCH_TRACE_PROTOCOL_SHA_CORRECT":
                all(t.get("actual_system_protocol_sha256") == pshas["LOCAL_PATCH"]
                    for t in lp_attempts) if lp_attempts else None,
            "FULL_REWRITE_TRACE_PROTOCOL_SHA_CORRECT":
                all(t.get("actual_system_protocol_sha256") == pshas["FULL_REWRITE"]
                    for t in fr_attempts) if fr_attempts else None,
            "COPY_SLICE_ACTIONS": sum(1 for a in all_patch_actions
                                      if a.get("action") == "COPY_SLICE"),
            "PARAPHRASE_CLAIM_ACTIONS": sum(1 for a in all_patch_actions
                                            if a.get("action") == "PARAPHRASE_CLAIM"),
            "CITATION_REPLACE_TEXT_ACTIONS": sum(
                1 for a in all_patch_actions
                if a.get("action") == "REPLACE_TEXT"
                and a.get("anchor_kind") == "citation"),
            "QUOTE_ISSUES_RESOLVED_BY_COPY": by_copy,
            "QUOTE_ISSUES_RESOLVED_BY_PARAPHRASE": by_para,
            "PARAPHRASE_INTRODUCED_QUOTE_ISSUES": para_introduced,
            "tool_starts": sum(1 for e in evs if e.get("type") == "tool_start"),
            "answer_len": len(answer)}


def run_case(case, mk_normal, mk_repair):
    orig_llm, orig_rllm = EG.get_llm, EG.get_repair_llm
    EG.get_llm = mk_normal
    EG.get_repair_llm = mk_repair
    EG._llm = None
    EG._llm_repair = None

    async def collect():
        evs = []
        async for ev in EG.stream_agent(case["question"], [], "general", "zh",
                                        _evaluation_repair_adapter=LocalPatchAdapter()):
            evs.append(ev)
        return evs
    try:
        evs = asyncio.run(collect())
    finally:
        EG.get_llm, EG.get_repair_llm = orig_llm, orig_rllm
        EG._llm = None
        EG._llm_repair = None
    return case_result(case["case_id"], evs)


def main(run_tag, requested_model="deepseek-v4-flash"):
    # 2026-09-09 用户预算指令: deepseek-v4-pro 禁止作为 agent LLM（过贵）——
    # MODEL_UNDER_TEST 偏差在回执中向 Reviewer 如实披露
    cfg = CC.v4pro_config(dict(CC.RP_B, id="RP-B"),
                          requested_model=requested_model,
                          candidate_id=f"{requested_model}@RP-B")
    mk_n = lambda: CC.build_candidate_langchain_client(cfg, "normal")
    mk_r = lambda: CC.build_candidate_langchain_client(cfg, "repair")
    pool = json.load(open(os.path.join(ROOT, "backend/tools/_tmp",
                                       "o7e_rp2_repair_pool.json"), encoding="utf-8"))
    out_path = os.path.join(ROOT, "backend/tools/_tmp",
                            f"o7e_rca1hook_{run_tag}.json")
    runs = []
    if os.path.exists(out_path):
        runs = json.load(open(out_path, encoding="utf-8"))
    done = {r["case_id"] for r in runs}
    for p in pool:
        if p["case_id"] in done:
            continue
        case = {"case_id": p["case_id"], "question": p["question"]}
        print(f"== {p['case_id']}", flush=True)
        try:
            r = run_case(case, mk_n, mk_r)
        except Exception as e:
            r = {"case_id": p["case_id"], "error": str(e)[:200]}
        runs = [x for x in runs if x["case_id"] != p["case_id"]] + [r]
        json.dump(runs, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"   pub={r.get('published')} LP={r.get('LOCAL_PATCH_TRIGGERED')} "
              f"applied={r.get('lp_applied')} tools={r.get('tool_starts')}", flush=True)
    ok = [r for r in runs if "error" not in r]
    pub = sum(1 for r in ok if r.get("published"))
    trig = [r for r in ok if (r.get("repairs") or 0) > 0]
    conv = sum(1 for r in trig if r.get("published"))
    lp_total = sum(r.get("LP_ANCHOR_TOTAL") or 0 for r in ok)
    lp_res = sum(r.get("LP_ANCHOR_RESOLVED") or 0 for r in ok)
    ovs = [r.get("SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE") for r in ok
           if isinstance(r.get("SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE"),
                         (int, float))]
    covers = [r.get("PROMPT_ISSUE_COVERAGE") for r in ok
              if isinstance(r.get("PROMPT_ISSUE_COVERAGE"), (int, float))]
    out = {"run": run_tag, "model": cfg.requested_model,
           "COMPLETED": len(ok), "PUBLISHED": pub,
           "REPAIR_TRIGGERED": len(trig),
           "REPAIR_CONVERGENCE": round(conv / max(len(trig), 1), 3) if trig else None,
           "LOCAL_PATCH_TRIGGERED": sum(1 for r in ok
                                        if r.get("LOCAL_PATCH_TRIGGERED")),
           "TOOL_LOOP_REAL": all((r.get("tool_starts") or 0) > 0 for r in ok),
           "VALIDATOR_EMPTY_FINAL": sum(1 for r in ok
                                        if r.get("VALIDATOR_EMPTY_FINAL")),
           "TERMINAL_CANDIDATE_EMPTY": sum(1 for r in ok
                                           if r.get("TERMINAL_CANDIDATE_EMPTY")),
           "PUBLIC_RESPONSE_NOT_EMITTED": sum(1 for r in ok
                                              if not r.get("PUBLIC_RESPONSE_EMITTED")),
           "PATCH_PROTOCOL_ERRORS": sum(1 for r in ok if r.get("lp_errors")),
           "PREP_ANCHOR_TOTAL": sum(r.get("PREP_ANCHOR_TOTAL") or 0 for r in ok),
           "PREP_ANCHOR_RESOLVED": sum(r.get("PREP_ANCHOR_RESOLVED") or 0 for r in ok),
           "LP_ANCHOR_TOTAL": lp_total,
           "LP_ANCHOR_RESOLVED": lp_res,
           "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE": round(lp_res / lp_total, 3)
                                                  if lp_total else None,
           "PROMPT_ISSUE_COVERAGE": round(min(covers), 3) if covers else None,
           "LINKED_EVIDENCE_REQUIRED": sum(r.get("LINKED_EVIDENCE_REQUIRED") or 0
                                           for r in ok),
           "LINKED_EVIDENCE_PRESENT": sum(r.get("LINKED_EVIDENCE_PRESENT") or 0
                                          for r in ok),
           "LINKED_EVIDENCE_STARVATION": sum(r.get("LINKED_EVIDENCE_STARVATION") or 0
                                             for r in ok),
           "BEST_EFFORT_SOURCE_MISSING": sum(r.get("BEST_EFFORT_SOURCE_MISSING") or 0
                                             for r in ok),
           "UNKNOWN_SLICE_ID": sum(r.get("UNKNOWN_SLICE_IDS") or 0 for r in ok),
           "INTENTIONAL_QUOTE_TO_PARAPHRASE": sum(
               r.get("INTENTIONAL_QUOTE_TO_PARAPHRASE") or 0 for r in ok),
           "UNINTENTIONAL_QUOTE_WRAPPER_LOSS": sum(
               r.get("UNINTENTIONAL_QUOTE_WRAPPER_LOSS") or 0 for r in ok),
           "PREEXISTING_VERIFIED_QUOTES_OUTSIDE_TARGET_LOST": sum(
               r.get("PREEXISTING_VERIFIED_QUOTES_OUTSIDE_TARGET_LOST") or 0
               for r in ok),
           "NON_TARGET_TEXT_CHANGED_CHARS": sum(r.get("NON_TARGET_TEXT_CHANGED_CHARS")
                                                or 0 for r in ok),
           "SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE":
               round(sum(ovs) / len(ovs), 3) if ovs else None,
           "UNSUPPORTED_PREP_TO_LOCAL_PATCH": sum(
               r.get("UNSUPPORTED_PREP_TO_LOCAL_PATCH") or 0 for r in ok),
           "BLANK_LOCAL_PATCH_PROMPT_INVOCATIONS": sum(
               r.get("BLANK_LOCAL_PATCH_PROMPT_INVOCATIONS") or 0 for r in ok),
           "PATCH_FINALIZATION_INVOCATIONS": sum(
               r.get("PATCH_FINALIZATION_INVOCATIONS") or 0 for r in ok),
           "FINALIZATION_TOOL_CALLS": sum(r.get("FINALIZATION_TOOL_CALLS") or 0
                                          for r in ok),
           "LOCAL_PATCH_TRACE_PROTOCOL_SHA_CORRECT": all(
               r.get("LOCAL_PATCH_TRACE_PROTOCOL_SHA_CORRECT") is not False
               for r in ok),
           "FULL_REWRITE_TRACE_PROTOCOL_SHA_CORRECT": all(
               r.get("FULL_REWRITE_TRACE_PROTOCOL_SHA_CORRECT") is not False
               for r in ok),
           "COPY_SLICE_ACTIONS": sum(r.get("COPY_SLICE_ACTIONS") or 0 for r in ok),
           "PARAPHRASE_CLAIM_ACTIONS": sum(r.get("PARAPHRASE_CLAIM_ACTIONS") or 0
                                           for r in ok),
           "CITATION_REPLACE_TEXT_ACTIONS": sum(
               r.get("CITATION_REPLACE_TEXT_ACTIONS") or 0 for r in ok),
           "QUOTE_ISSUES_RESOLVED_BY_COPY": sum(
               r.get("QUOTE_ISSUES_RESOLVED_BY_COPY") or 0 for r in ok),
           "QUOTE_ISSUES_RESOLVED_BY_PARAPHRASE": sum(
               r.get("QUOTE_ISSUES_RESOLVED_BY_PARAPHRASE") or 0 for r in ok),
           "PARAPHRASE_INTRODUCED_QUOTE_ISSUES": sum(
               r.get("PARAPHRASE_INTRODUCED_QUOTE_ISSUES") or 0 for r in ok)}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "RUN1")
