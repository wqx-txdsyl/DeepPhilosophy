# -*- coding: utf-8 -*-
"""O7-E Bakeoff Stage B——合格候选的 8-case 全链路 E2E。

引擎临时切候选模型（同 AG.MODEL/API_URL/API_KEY 注入, 生产解码=候选声明;
repair=temp 0）——评价-only, 不动生产配置文件。
用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_bakeoff_b.py <candidate_id>
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

CAND = {"deepseek-chat": ("DEEPSEEK_API_KEY", "https://api.deepseek", "deepseek-chat"),
        "glm-4-plus": ("ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4", "glm-4-plus"),
        "glm-4.6": ("ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4", "glm-4.6"),
        "glm-4-air": ("ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4", "glm-4-air")}

import routes.agent as AG
import o7e_runner as R
import o7e_evidence_checks as EVCHK

POOL = os.path.join(ROOT, "backend", "tools", "_tmp", "o7e_rp2_repair_pool.json")


def main(mid):
    envkey, api_url, model = CAND[mid]
    key = None
    for l in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        if l.startswith(envkey + "="):
            key = l.split("=", 1)[1].strip().strip('"').strip("'")
    # 临时注入候选（AG 是 get_llm 的配置源; extra_body 仅 deepseek）
    orig = (AG.API_KEY, AG.API_URL, AG.MODEL)
    AG.API_KEY, AG.API_URL, AG.MODEL = key, api_url, model
    import engine_langgraph as EG
    EG._llm = None
    EG._llm_repair = None
    out_path = os.path.join(ROOT, "backend", "tools", "_tmp",
                            f"o7e_bakeoff_B_{mid.replace('.', '_')}.json")
    runs = []
    if os.path.exists(out_path):
        runs = json.load(open(out_path, encoding="utf-8"))
    done = {r["case_id"] for r in runs}
    pool = json.load(open(POOL, encoding="utf-8"))
    for p in pool:
        if p["case_id"] in done:
            continue
        case = {"case_id": p["case_id"], "category": "bakeoff_b",
                "question": p["question"], "persona": "general",
                "applicability": {}, "evidence_expectation": "PRIMARY_REQUIRED"}
        print(f"== {p['case_id']}", flush=True)
        try:
            r = R.run_case(case)
        except Exception as e:
            r = {"case_id": p["case_id"], "delivery": {"run_status": "RUN_ERROR",
                                                       "published": None}}
            print("   err", str(e)[:100], flush=True)
        try:
            r["primary_gate"] = EVCHK.check_case(case, r)
        except Exception:
            r["primary_gate"] = {}
        runs = [x for x in runs if x["case_id"] != p["case_id"]] + [r]
        json.dump(runs, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        d = r.get("delivery", {})
        print(f"   {d.get('run_status')} pub={d.get('published')} rep={d.get('repair_attempts')}",
              flush=True)
    AG.API_KEY, AG.API_URL, AG.MODEL = orig
    EG._llm = None
    EG._llm_repair = None
    # 汇总（与校准同口径）
    comp = [r for r in runs if r.get("delivery", {}).get("run_status") == "COMPLETED"]
    pub = [r for r in comp if r["delivery"].get("published")]
    trig = [r for r in comp if (r["delivery"].get("repair_attempts") or 0) > 0]
    conv = [r for r in trig if r["delivery"].get("published")]
    traces = [t for r in comp for t in (r.get("repair_trace") or [])]
    proto = sum(1 for t in traces if t.get("system_protocol_injected"))
    out = {"candidate": mid, "COMPLETED": len(comp), "PUBLISHED": len(pub),
           "publication_rate": round(len(pub) / max(len(comp), 1), 3),
           "REPAIR_TRIGGERED": len(trig),
           "REPAIR_CONVERGED": len(conv),
           "case_convergence": round(len(conv) / max(len(trig), 1), 3) if trig else None,
           "E2E_PROTOCOL_RATE": round(proto / max(len(traces), 1), 3) if traces else None,
           "EMPTY_FINAL": sum(1 for r in comp if "EMPTY_FINAL" in
                              (r["delivery"].get("final_validation_issue_codes") or []))}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
