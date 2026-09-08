# -*- coding: utf-8 -*-
"""O7-E RCA-2 H1 §9: full-engine LOCAL_PATCH evaluation RUN。

通过 stream_agent(_evaluation_repair_adapter=LocalPatchAdapter) 注入——
真实工具循环/真实预算/repair_mode 语义（§6）; 生产默认 None 行为不变。
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
    """H2 §C-F: V2 合同——slice_id 选择/零 SHA 回显。"""
    def can_handle(self, validation):
        codes = {i.get("code") for i in validation.as_dict().get("issues", [])}
        return bool(codes & RC.LOCAL_PATCH_CODES)

    def build(self, candidate, validation, raw_tool_log, prev_errors=None):
        bundles = RC.build_repair_issue_bundles(candidate, validation, raw_tool_log)
        anchor_ok = all(b.get("anchor") for b in bundles
                        if b["code"] in RC.LOCAL_PATCH_CODES)
        issues = validation.as_dict().get("issues", [])
        locators = [(i or {}).get("locator") or "" for i in issues]
        catalog = RC.build_slice_catalog(bundles, " ".join(locators))
        if not anchor_ok:
            return {"prompt": "", "pre_patch_candidate": candidate,
                    "bundles": bundles, "catalog": catalog, "anchor_ok": False,
                    "issue_fps": [RC.issue_fingerprint((i or {}).get("code"),
                                                       (i or {}).get("locator") or "")
                                  for i in issues]}
        prompt = RC.render_patch_prompt_v2(bundles, catalog, prev_errors)
        return {"prompt": prompt, "pre_patch_candidate": candidate,
                "bundles": bundles, "catalog": catalog, "anchor_ok": True,
                "issue_fps": [RC.issue_fingerprint((i or {}).get("code"),
                                                   (i or {}).get("locator") or "")
                              for i in issues]}

    def parse_and_apply(self, pre_candidate, model_output, ctx):
        if not ctx.get("anchor_ok", True):
            return None, ["LOCAL_PATCH_UNSUPPORTED: anchor unresolved"]
        new, errs = RC.apply_main_agent_patches_v2(
            pre_candidate, model_output, ctx["bundles"],
            ctx.get("catalog") or {})
        return new, (errs or [])


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
    done = next((e for e in reversed(evs) if e.get("type") == "done"), {})
    val = done.get("validation") or {}
    hist = val.get("history") or []
    trace = val.get("repair_trace") or []
    last_fail = max((i for i, e in enumerate(evs)
                     if e.get("type") == "validation_failed"), default=-1)
    answer = "".join(e.get("content", "") for i, e in enumerate(evs)
                     if e.get("type") == "token" and i > last_fail)
    lp_used = [t for t in trace if t.get("local_patch")]
    final_codes = [i.get("code") for i in val.get("result", {}).get("issues", [])]
    return {"case_id": case["case_id"],
            "published": bool(answer.strip()) and bool(val.get("result", {}).get("ok")),
            "repairs": val.get("repairs_used", 0),
            "issue_counts": [len(h.get("issue_codes") or []) for h in hist],
            "final_issues": final_codes[:4],
            "VALIDATOR_EMPTY_FINAL": "EMPTY_FINAL" in final_codes,
            "TERMINAL_EMPTY_ANSWER": not answer.strip() and
                                     "EMPTY_FINAL" not in final_codes,
            "LOCAL_PATCH_TRIGGERED": bool(lp_used),
            "lp_applied": sum(1 for t in lp_used if t["local_patch"].get("applied")),
            "lp_errors": [e for t in lp_used
                          for e in (t["local_patch"].get("errors") or [])][:3],
            "tool_starts": sum(1 for e in evs if e.get("type") == "tool_start"),
            "answer_len": len(answer)}


def main(run_tag):
    cfg = CC.v4pro_config(dict(CC.RP_B, id="RP-B"))
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
    lp_trig = sum(1 for r in ok if r.get("LOCAL_PATCH_TRIGGERED"))
    out = {"run": run_tag, "model": cfg.requested_model,
           "COMPLETED": len(ok), "PUBLISHED": pub,
           "REPAIR_TRIGGERED": len(trig),
           "REPAIR_CONVERGENCE": round(conv / max(len(trig), 1), 3) if trig else None,
           "LOCAL_PATCH_TRIGGERED": lp_trig,
           "TOOL_LOOP_REAL": all((r.get("tool_starts") or 0) > 0 for r in ok),
           "VALIDATOR_EMPTY_FINAL": sum(1 for r in ok
                                        if r.get("VALIDATOR_EMPTY_FINAL")),
           "TERMINAL_EMPTY_ANSWER": sum(1 for r in ok
                                        if r.get("TERMINAL_EMPTY_ANSWER")),
           "PATCH_PROTOCOL_ERRORS": sum(1 for r in ok if r.get("lp_errors"))}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
