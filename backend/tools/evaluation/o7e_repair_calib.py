# -*- coding: utf-8 -*-
"""O7-E RP2 §20: repair calibration——旧失败池（REPAIR_CALIBRATION_POOL）重跑。

要求: >=8 案例, EMPTY_FINAL=0; 若 attempts>=5 则 success>=0.80 才可进 Stage B。
用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_repair_calib.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7e_runner as R

POOL = os.path.join(ROOT, "backend", "tools", "_tmp", "o7e_rp2_repair_pool.json")
OUT = os.path.join(ROOT, "backend", "tools", "_tmp", "o7e_rp2_repair_calib.json")


def main():
    pool = json.load(open(POOL, encoding="utf-8"))
    runs = []
    if os.path.exists(OUT):
        runs = json.load(open(OUT, encoding="utf-8"))
    done = {r["case_id"] for r in runs}
    for p in pool:
        if p["case_id"] in done:
            continue
        case = {"case_id": p["case_id"], "category": "repair_calibration",
                "question": p["question"], "persona": "general",
                "applicability": {}, "evidence_expectation": "PRIMARY_REQUIRED"}
        print(f"== {p['case_id']} (was: {','.join(p['codes'])})", flush=True)
        try:
            r = R.run_case(case)
        except Exception as e:
            r = {"case_id": p["case_id"], "question": p["question"],
                 "run_error": str(e)[:300],
                 "delivery": {"run_status": "RUN_ERROR", "published": None}}
        runs = [x for x in runs if x["case_id"] != p["case_id"]] + [r]
        json.dump(runs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        d = r.get("delivery", {})
        print(f"   {d.get('run_status')} pub={d.get('published')} "
              f"rep={d.get('repair_attempts')} exh={d.get('repair_exhaustion')}",
              flush=True)
    # 汇总
    # O7-E RP2 Closure A: case-convergence 口径（不是 invocation 效率）
    comp = [r for r in runs if r.get("delivery", {}).get("run_status") == "COMPLETED"]
    pub = [r for r in comp if r["delivery"]["published"]]
    triggered = [r for r in comp if (r["delivery"].get("repair_attempts") or 0) > 0]
    converged = [r for r in triggered if r["delivery"]["published"]]
    atts = sum(r["delivery"].get("repair_attempts") or 0 for r in triggered)
    exhausted = [r for r in comp if r["delivery"].get("repair_exhaustion")]
    empty = sum(1 for r in comp
                if "EMPTY_FINAL" in (r["delivery"].get("final_validation_issue_codes") or []))
    # RP-DEC §5: E2E 真值（从真实 run artifact 的 repair_trace 计算）
    traces = [t for r in comp for t in (r.get("repair_trace") or [])]
    e2e_attempts = len(traces)
    e2e_proto = sum(1 for t in traces if t.get("system_protocol_injected"))
    packet_expected = sum(1 for t in traces if t.get("evidence_refs"))
    packet_present = sum(1 for t in traces if t.get("packet_present"))
    out = {
        "cases": len(runs), "completed": len(comp), "published": len(pub),
        "E2E_REPAIR_ATTEMPTS": e2e_attempts,
        "E2E_PROTOCOL_INJECTED_ATTEMPTS": e2e_proto,
        "E2E_REPAIR_PROTOCOL_INJECTION_RATE":
            round(e2e_proto / max(e2e_attempts, 1), 3) if e2e_attempts else None,
        "E2E_PACKET_EXPECTED_ATTEMPTS": packet_expected,
        "E2E_PACKET_PRESENT_ATTEMPTS": packet_present,
        "E2E_PACKET_TELEMETRY_MISSING":
            packet_expected - packet_present,
        "REPAIR_TRIGGERED_CASES": len(triggered),
        "REPAIR_CONVERGED_CASES": len(converged),
        "REPAIR_CASE_CONVERGENCE_RATE":
            round(len(converged) / max(len(triggered), 1), 3) if triggered else None,
        "REPAIR_TOTAL_INVOCATIONS": atts,
        "REPAIR_INVOCATION_EFFICIENCY":          # diagnostic only, 非 gate
            round(len(converged) / max(atts, 1), 3),
        "MEAN_REPAIR_INVOCATIONS_PER_TRIGGERED_CASE":
            round(atts / max(len(triggered), 1), 2),
        "REPAIR_EXHAUSTED_CASES": len(exhausted),
        "EMPTY_FINAL": empty,
        "publish_rate_completed": round(len(pub) / max(len(comp), 1), 3)}
    print(json.dumps(out, ensure_ascii=False))
    json.dump(out, open(OUT.replace(".json", "_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
