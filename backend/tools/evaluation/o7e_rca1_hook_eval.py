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
        # §6: wrapper 保留 / 非目标字节机械校验（apply 成功才有意义）
        wrapper_loss, nt_violations = 0, 0
        if new is not None:
            spans = []
            for rec in telemetry:
                b = next((x for x in (ctx.get("bundles") or [])
                          if x["issue_id"] == rec.get("issue_id")), None)
                a = (b or {}).get("anchor") or {}
                cs, ce = a.get("content_start"), a.get("content_end")
                if cs is None or ce is None:
                    continue
                spans.append((cs, ce))
                qs, qe = a.get("claim_start"), a.get("claim_end")
                if qs is None or qe is None or (qs == cs and qe == ce):
                    continue   # citation anchor 或 content==claim（无 wrapper）
                if qs < cs and pre_candidate[qs:cs] and pre_candidate[qs:cs] not in new:
                    wrapper_loss += 1
                if ce < qe and pre_candidate[ce:qe] and pre_candidate[ce:qe] not in new:
                    wrapper_loss += 1
            if RC.non_target_changed_chars(pre_candidate, new, spans) != 0:
                nt_violations = 1
        return new, (errs or []), {"actions": telemetry,
                                   "quote_wrapper_loss": wrapper_loss,
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


def case_result(case_id, evs):
    """per-case 硬门遥测聚合（纯函数——F11/F12 直接可测）。"""
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
    # anchors / starvation / overlap（trace bundles 由 engine 从 prepare 落笔）
    bundle_rows = [b for t in trace for b in (t.get("bundles") or [])]
    anchor_total = len(bundle_rows)
    anchor_resolved = sum(1 for b in bundle_rows if b.get("anchor"))
    ovs = [b.get("source_overlap") for b in bundle_rows
           if isinstance(b.get("source_overlap"), (int, float))]
    coverages = [t["lp_gate"]["prompt_issue_coverage"] for t in lp_attempts
                 if isinstance(t.get("lp_gate", {}).get("prompt_issue_coverage"),
                               (int, float))]
    nt_violations = sum(
        1 for t in trace
        if (t.get("local_patch", {}) or {}).get("non_target_changed"))
    return {"case_id": case_id,
            "published": bool(answer.strip()) and bool(val.get("result", {}).get("ok")),
            "repairs": val.get("repairs_used", 0),
            "issue_counts": [len(h.get("issue_codes") or []) for h in hist],
            "fingerprint_classification": classify_history(hist),
            "ANCHOR_TOTAL": anchor_total,
            "ANCHOR_RESOLVED": anchor_resolved,
            "ANCHOR_RESOLUTION_RATE": round(anchor_resolved / anchor_total, 3)
                                      if anchor_total else None,
            "PROMPT_ISSUE_COVERAGE": round(sum(coverages) / len(coverages), 3)
                                     if coverages else None,
            "LINKED_EVIDENCE_STARVATION": sum(1 for b in bundle_rows
                                              if not b.get("linked_source")),
            "UNKNOWN_SLICE_IDS": sum(1 for t in lp_used
                                     for e in (t["local_patch"].get("errors") or [])
                                     if "UNKNOWN_SLICE_ID" in str(e)),
            "QUOTE_WRAPPER_LOSS": sum(
                (t.get("local_patch", {}) or {}).get("quote_wrapper_loss") or 0
                for t in trace),
            "NON_TARGET_TEXT_CHANGED_CHARS": nt_violations,
            "SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE":
                round(sum(1 for v in ovs if v > 0) / len(ovs), 3) if ovs else None,
            "PATCH_FINALIZATION_INVOCATIONS": len(fin_rows),
            "FINALIZATION_TOOL_CALLS": sum(f.get("tool_calls") or 0 for f in fin_rows),
            "VALIDATOR_EMPTY_FINAL": "EMPTY_FINAL" in final_codes,
            # §4b: 终态候选空 ≠ 未发布——两个独立机械事实
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
            "PATCH_ACTIONS": [a for t in lp_used
                              for a in (t["local_patch"].get("actions") or [])],
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
    a_total = sum(r.get("ANCHOR_TOTAL") or 0 for r in ok)
    a_res = sum(r.get("ANCHOR_RESOLVED") or 0 for r in ok)
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
           "ANCHOR_RESOLUTION_RATE": round(a_res / a_total, 3) if a_total else None,
           "PROMPT_ISSUE_COVERAGE": round(min(covers), 3) if covers else None,
           "LINKED_EVIDENCE_STARVATION": sum(r.get("LINKED_EVIDENCE_STARVATION") or 0
                                             for r in ok),
           "UNKNOWN_SLICE_ID": sum(r.get("UNKNOWN_SLICE_IDS") or 0 for r in ok),
           "QUOTE_WRAPPER_LOSS": sum(r.get("QUOTE_WRAPPER_LOSS") or 0 for r in ok),
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
               for r in ok)}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "RUN1")
