# -*- coding: utf-8 -*-
"""O7-E Production Freeze §E: canonical academic calibration——生产真实路径。

不再用 evaluation-only 注入模拟: stream_agent 无 seam 参数, General Agent 经
local_patch_runtime production adapter 生产启用（§A/§B）; 模型 = 当前 flash
matched config（用户预算指令: 禁用 V4-Pro）。
产物同时供 §F canonical scholarly judge（o7e_bakeoff_judge2）消费。
"""
import asyncio
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import engine_langgraph as EG
import o7e_candidate_config as CC
from o7e_rca1_hook_eval import case_result

MANIFEST = os.path.join(ROOT, "docs/evidence",
                        "PHIAGENT_O7E_BAKEOFF_EVALUATION_MANIFEST.json")


def _as_list(v):
    return v if isinstance(v, list) else []


def _ev_digest(ev):
    """PF-RP1 复审（Response 2）发现: used_evidence 被 v[:10] 截断会让 judge 看
    不到真正使用的 ev_56/ev_62——used_evidence/citations 全量归档（run 内有界）,
    仅 retrieved_evidence 等大列表截断。"""
    if not isinstance(ev, dict):
        return ev
    # PF-RP5: retrieved/candidate_evidence 也全量归档——截断会饿死 replay 别名池
    # （PROBE1 H02 人性论（全4册）#5 实证）
    full_keys = {"used_evidence", "citations", "unverified_citations", "claims",
                 "retrieved_evidence", "candidate_evidence",
                 "scholarly_records", "scholarly_evidence"}
    out = {}
    for k, v in ev.items():
        if k in full_keys and isinstance(v, list):
            out[k] = v
        elif isinstance(v, list):
            out[k] = v[:10]
        elif isinstance(v, dict):
            out[k] = {kk: v[kk] for kk in list(v)[:10]}
        else:
            out[k] = v
    return out


def run_case_production(case, mk_normal, mk_repair):
    """§E: 真实生产路径（无 adapter 注入; production adapter 经 §B 默认启用）。"""
    orig_llm, orig_rllm = EG.get_llm, EG.get_repair_llm
    EG.get_llm = mk_normal
    EG.get_repair_llm = mk_repair
    EG._llm = None
    EG._llm_repair = None

    async def collect():
        evs = []
        async for ev in EG.stream_agent(case["question"], [], "general", "zh"):
            evs.append(ev)
        return evs
    try:
        evs = asyncio.run(collect())
    finally:
        EG.get_llm, EG.get_repair_llm = orig_llm, orig_rllm
        EG._llm = None
        EG._llm_repair = None

    done = next((e for e in reversed(evs) if e.get("type") == "done"), {})
    errors = [e for e in evs if e.get("type") == "error"]
    # V4 §2: scholarly 调用明细归档——V5-F2 §E 修复: args 只存在于 type="tool"
    # 事件（tool_start 仅 name/tool_call_id, 无 args → V5 归档 query 全 null）;
    # 从 tool 事件保存 tool_call_id/name/args/result, 原始 query 可恢复
    scholarly_calls_detail = []
    for e in evs:
        if e.get("type") == "tool" and e.get("name") in (
                "search_scholarship", "get_scholarly_source"):
            scholarly_calls_detail.append({"tool": e.get("name"),
                                           "tool_call_id": e.get("tool_call_id"),
                                           "args": e.get("args"),
                                           "result": (e.get("result") or "")[:300]})
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    val = done.get("validation") or {}
    tel = case_result(case["case_id"], evs)
    published = bool(tel["published"])
    final_codes = [i.get("code") for i in val.get("result", {}).get("issues", [])]
    # PF-RP3B §D: run-time scholarly provenance（安全投影: abstract/passages 是
    # tool evidence 可存; 零 provider CoT）
    _ss_done = done.get("scholarly_sources") or {}
    scholarly_provenance = {
        "SCHOLARLY_SEARCH_CALLS": _ss_done.get("scholarly_search_calls", 0),
        "SCHOLARLY_SOURCE_FETCH_CALLS": _ss_done.get("scholarly_source_fetch_calls", 0),
        "SCHOLARLY_RECORD_IDS": [r.get("source_record_id")
                                 for r in _ss_done.get("scholarly_records") or []],
        "SCHOLARLY_EVIDENCE_RECORD_IDS": [e.get("source_record_id")
                                          for e in _ss_done.get("scholarly_evidence") or []],
        "SCHOLARLY_ACCESS_LEVELS": _ss_done.get("scholarly_access") or {},
        "scholarly_records": _ss_done.get("scholarly_records") or [],
        "scholarly_evidence": _ss_done.get("scholarly_evidence") or [],
    }
    # §E delivery 新字段。terminal_pending = 未达终态校验（流崩溃/无 done 事件）——
    # 耗尽修复后的干净拒绝（有 done、终态候选非空）不是 pending。
    # PF-RP1 §B: access overclaim 是语义学术判断, 不伪装成机械 delivery gate
    # → 不在 delivery 层测, DEFERRED 给 canonical scholarly judge（LITERATURE_ACCESS_OVERCLAIM）
    terminal_pending = not bool(done)
    public_invalid_citations = 1 if (published and "UNVERIFIED_CITATION" in final_codes) else 0
    public_unverified_quotes = 1 if (published and "UNSUPPORTED_EXACT_QUOTE" in final_codes) else 0
    # V3 final holdout gate instrumentation
    stitched_public = 1 if (published and "STITCHED_QUOTE" in final_codes) else 0
    tool_loop_aborts = sum(1 for e in evs if e.get("type") == "tool_cancel")
    cls_all = tel.get("fingerprint_classification") or {}
    repair_new_fatal = 1 if any((cls_all.get(f"R{k}") or {}).get("introduced")
                                for k in range(1, 8)) else 0
    record = {"case_id": case["case_id"],
              "question": case["question"],
              "task_category": case.get("category") or case.get("task_category"),
              "agent_identity": case.get("agent_identity") or "DeepPhilosophy",
              "applicability": case.get("applicability") or {},
              "answer": answer,
              "delivery": {
                  "run_status": "COMPLETED" if done else "RUN_ERROR",
                  "published": published,
                  "repairs_used": val.get("repairs_used", 0),
                  "terminal_pending": terminal_pending,
                  "public_invalid_citations": public_invalid_citations,
                  "public_unverified_exact_quotes": public_unverified_quotes,
                  "public_access_overclaims": "DEFERRED_TO_CANONICAL_JUDGE",
                  "final_validation_result": bool(val.get("result", {}).get("ok")),
                  "final_validation_issue_codes": final_codes[:6],
              },
              "errors": [str(e.get("content") or "")[:200] for e in errors][:3],
              "citations": _as_list(done.get("citations")),
              "quote_bound": _as_list(done.get("quote_bound")),
              "evidence_digest": _ev_digest(done.get("evidence")) if done else None,
              "scholarly_provenance": scholarly_provenance,
              "scholarly_calls_detail": scholarly_calls_detail,
              "STITCHED_PUBLIC_QUOTES": stitched_public,
              "REPAIR_CREATES_NEW_FATAL_ERROR": repair_new_fatal,
              "TOOL_LOOP_ABORTS": tool_loop_aborts,
              # PF-RP4 §3: 真实工具选择轨迹（declared tool 序列, 机械事实）
              "tool_trajectory": [e.get("name") for e in evs
                                  if e.get("type") == "tool_start"
                                  and e.get("initiated_by") == "main_agent"],
              "hard_gate": {k: tel[k] for k in (
                  "PREP_ANCHOR_TOTAL", "PREP_ANCHOR_RESOLVED",
                  "LP_ANCHOR_TOTAL", "LP_ANCHOR_RESOLVED",
                  "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE", "PROMPT_ISSUE_COVERAGE",
                  "LINKED_EVIDENCE_REQUIRED", "LINKED_EVIDENCE_PRESENT",
                  "LINKED_EVIDENCE_STARVATION", "BEST_EFFORT_SOURCE_MISSING",
                  "UNKNOWN_SLICE_IDS", "INTENTIONAL_QUOTE_TO_PARAPHRASE",
                  "UNINTENTIONAL_QUOTE_WRAPPER_LOSS",
                  "PREEXISTING_VERIFIED_QUOTES_OUTSIDE_TARGET_LOST",
                  "NON_TARGET_TEXT_CHANGED_CHARS",
                  "COPY_SLICE_ACTIONS", "PARAPHRASE_CLAIM_ACTIONS",
                  "CITATION_REPLACE_TEXT_ACTIONS",
                  "QUOTE_ISSUES_RESOLVED_BY_COPY", "QUOTE_ISSUES_RESOLVED_BY_PARAPHRASE",
                  "PARAPHRASE_INTRODUCED_QUOTE_ISSUES",
                  "TERMINAL_CANDIDATE_EMPTY", "PUBLIC_RESPONSE_EMITTED",
                  "REPAIR_OUTPUT_MODES", "lp_errors", "repairs", "issue_counts",
                  "fingerprint_classification")},
              }
    return record


def main(run_tag="CAL1", requested_model="deepseek-v4-flash", only=None,
         manifest_path=None):
    manifest_raw = json.load(open(manifest_path or MANIFEST, encoding="utf-8"))
    # V3_HOLDOUT_MANIFEST 为 {meta..., cases: [...]} 包装; 兼容裸列表
    manifest = manifest_raw.get("cases") if isinstance(manifest_raw, dict) \
        else manifest_raw
    manifest = manifest or []
    cfg = CC.v4pro_config(dict(CC.RP_B, id="RP-B"),
                          requested_model=requested_model,
                          candidate_id=f"{requested_model}@RP-B")
    mk_n = lambda: CC.build_candidate_langchain_client(cfg, "normal")
    mk_r = lambda: CC.build_candidate_langchain_client(cfg, "repair")
    out_path = os.path.join(ROOT, "backend/tools/_tmp", f"o7e_calib_{run_tag}.json")
    runs = []
    if os.path.exists(out_path):
        runs = json.load(open(out_path, encoding="utf-8"))
    done_ids = {r["case_id"] for r in runs}
    for m in manifest:
        if only and m["case_id"] not in only:
            continue
        if m["case_id"] in done_ids:
            continue
        print(f"== {m['case_id']}", flush=True)
        try:
            r = run_case_production(m, mk_n, mk_r)
        except Exception as e:
            r = {"case_id": m["case_id"], "error": str(e)[:200],
                 "delivery": {"run_status": "RUN_ERROR", "published": False}}
        runs = [x for x in runs if x["case_id"] != m["case_id"]] + [r]
        json.dump(runs, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        d = r.get("delivery", {})
        print(f"   pub={d.get('published')} repairs={d.get('repairs_used')}", flush=True)

    ok = [r for r in runs if "error" not in r]
    pub = sum(1 for r in ok if r.get("delivery", {}).get("published"))
    trig = [r for r in ok if (r.get("delivery", {}).get("repairs_used") or 0) > 0]
    conv = sum(1 for r in trig if r.get("delivery", {}).get("published"))
    hg = [r.get("hard_gate", {}) for r in ok]
    lp_total = sum(h.get("LP_ANCHOR_TOTAL") or 0 for h in hg)
    lp_res = sum(h.get("LP_ANCHOR_RESOLVED") or 0 for h in hg)
    covers = [h.get("PROMPT_ISSUE_COVERAGE") for h in hg
              if isinstance(h.get("PROMPT_ISSUE_COVERAGE"), (int, float))]
    out = {"run": run_tag, "model": cfg.requested_model,
           "CALIBRATION_COMPLETED": len(ok),
           "CALIBRATION_PUBLISHED": pub,
           "CALIBRATION_REPAIR_TRIGGERED": len(trig),
           "CALIBRATION_REPAIR_CONVERGED": conv,
           "CALIBRATION_REPAIR_CONVERGENCE": round(conv / max(len(trig), 1), 3)
                                             if trig else None,
           "TERMINAL_PENDING": sum(1 for r in ok
                                   if r.get("delivery", {}).get("terminal_pending")),
           "VALIDATOR_EMPTY_FINAL": sum(
               1 for r in ok if "EMPTY_FINAL"
               in (r.get("delivery", {}).get("final_validation_issue_codes") or [])),
           "TERMINAL_CANDIDATE_EMPTY": sum(
               1 for h in hg if h.get("TERMINAL_CANDIDATE_EMPTY")),
           "PUBLIC_INVALID_CITATIONS": sum(
               1 for r in ok if r.get("delivery", {}).get("public_invalid_citations")),
           "UNVERIFIED_PUBLIC_EXACT_QUOTES": sum(
               1 for r in ok if r.get("delivery", {}).get("public_unverified_exact_quotes")),
           # PF-RP1 §B: access overclaim 交由 canonical judge（不再伪报机械 0）
           "PUBLIC_ACCESS_OVERCLAIMS_MEASURED": False,
           "ACCESS_OVERCLAIM_GATE": "DEFERRED_TO_CANONICAL_JUDGE",
           "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE": round(lp_res / lp_total, 3)
                                                  if lp_total else None,
           "PROMPT_ISSUE_COVERAGE": round(min(covers), 3) if covers else None,
           "LINKED_EVIDENCE_STARVATION": sum(
               h.get("LINKED_EVIDENCE_STARVATION") or 0 for h in hg),
           "UNKNOWN_SLICE_ID": sum(h.get("UNKNOWN_SLICE_IDS") or 0 for h in hg),
           "UNINTENTIONAL_QUOTE_WRAPPER_LOSS": sum(
               h.get("UNINTENTIONAL_QUOTE_WRAPPER_LOSS") or 0 for h in hg),
           "NON_TARGET_TEXT_CHANGED_CHARS": sum(
               h.get("NON_TARGET_TEXT_CHANGED_CHARS") or 0 for h in hg),
           "INTENTIONAL_QUOTE_TO_PARAPHRASE": sum(
               h.get("INTENTIONAL_QUOTE_TO_PARAPHRASE") or 0 for h in hg),
           "PARAPHRASE_INTRODUCED_QUOTE_ISSUES": sum(
               h.get("PARAPHRASE_INTRODUCED_QUOTE_ISSUES") or 0 for h in hg),
           "SCHOLARLY_SEARCH_CASES": sum(
               1 for r in ok if (r.get("scholarly_provenance") or {})
               .get("SCHOLARLY_SEARCH_CALLS")),
           "SCHOLARLY_SOURCE_FETCH_CASES": sum(
               1 for r in ok if (r.get("scholarly_provenance") or {})
               .get("SCHOLARLY_SOURCE_FETCH_CALLS")),
           "SCHOLARLY_RECORD_COUNT": sum(
               len((r.get("scholarly_provenance") or {}).get("SCHOLARLY_RECORD_IDS")
                   or []) for r in ok),
           # PF-RP4B §metric: 模糊的 SCHOLARLY_EVIDENCE_COUNT 废弃, 拆为:
           "SCHOLARLY_FETCH_RESULT_COUNT": sum(
               len((r.get("scholarly_provenance") or {}).get("SCHOLARLY_EVIDENCE_RECORD_IDS")
                   or []) for r in ok),
           "SCHOLARLY_CONTENT_EVIDENCE_COUNT": sum(
               1 for r in ok
               for e in ((r.get("scholarly_provenance") or {})
                         .get("scholarly_evidence") or [])
               if e.get("content_evidence")),
           "FINAL_PUBLICATION_RATE": round(pub / max(len(ok), 1), 3),
           "STITCHED_PUBLIC_QUOTES": sum(1 for r in ok
                                         if r.get("STITCHED_PUBLIC_QUOTES")),
           "REPAIR_CREATES_NEW_FATAL_ERROR": sum(
               1 for r in ok if r.get("REPAIR_CREATES_NEW_FATAL_ERROR")),
           "TOOL_LOOP_ABORTS": sum(r.get("TOOL_LOOP_ABORTS") or 0 for r in ok),
           }
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    # 用法: o7e_production_calibration.py RUN_TAG [case_ids 逗号分隔 | -] [manifest.json]
    _tag = sys.argv[1] if len(sys.argv) > 1 else "CAL1"
    _only = None
    _man = None
    for a in sys.argv[2:]:
        if a.endswith(".json"):
            _man = a
        elif a not in ("-", ""):
            _only = a.split(",")
    main(_tag, requested_model="deepseek-v4-flash", only=_only,
         manifest_path=_man)
