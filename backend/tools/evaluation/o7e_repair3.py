# -*- coding: utf-8 -*-
"""O7-E Repair-Depth Ablation §2-9: 同 trajectory 2 vs 3 repair counterfactual。

evaluation-only: monkeypatch engine 模块级 MAX_VALIDATION_REPAIRS 引用为 3
（生产 final_validator.MAX_VALIDATION_REPAIRS 常量不动）; 退出恢复。
同一次 E2E trajectory 同时记录 AT_2（WOULD_STOP）与 AT_3 终值——
RP-B repair 确定性解码使配对有效。
"""
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import engine_langgraph as EG
import final_validator as FV
import o7e_candidate_config as CC
import o7e_runner as R

assert FV.MAX_VALIDATION_REPAIRS == 2, "生产常量必须保持 2（本实验 eval-only 覆盖）"

RP_B = CC.RP_B


def _sha(s):
    return hashlib.sha256((s or "").encode()).hexdigest()[:16]


def run_case_paired(case, mk_normal, mk_repair):
    """跑一次 E2E, 修复上限 3; 从 repair_trace 提取 AT_2 反事实。"""
    orig_llm, orig_rllm = EG.get_llm, EG.get_repair_llm
    EG.get_llm = mk_normal
    EG.get_repair_llm = mk_repair
    EG._llm = None
    EG._llm_repair = None
    # eval-only: 覆盖 engine 命名空间里的 MAX_VALIDATION_REPAIRS（函数内 from-import 绑定）
    import final_validator as _FV
    _FV.MAX_VALIDATION_REPAIRS = 3
    # engine 在 stream_agent 内部 from final_validator import ...——是调用时绑定?
    # 检查: import 在函数体内 → 每次调用重新解析 → 覆盖 _FV 模块属性即生效
    t0 = time.time()
    events = []
    import asyncio

    async def collect():
        async for ev in EG.stream_agent(case["question"], [], "general", "zh"):
            events.append(ev)
    try:
        asyncio.run(collect())
    finally:
        _FV.MAX_VALIDATION_REPAIRS = 2
        EG.get_llm, EG.get_repair_llm = orig_llm, orig_rllm
        EG._llm = None
        EG._llm_repair = None
    done = next((e for e in reversed(events) if e.get("type") == "done"), {})
    val = done.get("validation") or {}
    hist = val.get("history") or []
    trace = val.get("repair_trace") or []
    # 最终答案（最后一次失败后 token 段）
    last_fail = max((i for i, e in enumerate(events)
                     if e.get("type") == "validation_failed"), default=-1)
    tokens = [e.get("content", "") for i, e in enumerate(events)
              if e.get("type") == "token" and i > last_fail]
    answer = "".join(tokens)

    # AT_2 反事实: 若上限=2, 最终状态=history[2]（第3次尝试=2 repairs 后）
    at2_ok = None
    if len(hist) >= 3:
        at2_ok = bool(hist[2].get("ok"))       # attempts: initial + r1 + r2
    at3_ok = bool(val.get("result", {}).get("ok")) if done else None
    repairs_used = val.get("repairs_used")

    # issue 计数轨迹
    counts = [len(h.get("issue_codes") or []) for h in hist]
    return {
        "case_id": case["case_id"],
        "INITIAL_ISSUES": counts[0] if counts else None,
        "ISSUE_COUNTS": counts,
        "VALID_AFTER_2": at2_ok,
        "VALID_AFTER_3": at3_ok,
        "repairs_used": repairs_used,
        "candidate_sha_after": [h.get("candidate_sha256") for h in hist[1:]],
        "published_at_2": bool(at2_ok),
        "published_at_3": bool(answer.strip()) and bool(at3_ok),
        "answer_len": len(answer),
        "EMPTY_FINAL": "EMPTY_FINAL" in [
            i.get("code") for i in val.get("result", {}).get("issues", [])],
        "elapsed_s": round(time.time() - t0, 1),
        "protocol_rate": (round(sum(1 for t in trace if t.get("system_protocol_injected"))
                                / max(len(trace), 1), 3) if trace else None),
    }


def main():
    cfg = CC.v4pro_config(dict(RP_B, id="RP-B-3R"))
    mk_n = lambda: CC.build_candidate_langchain_client(cfg, "normal")
    mk_r = lambda: CC.build_candidate_langchain_client(cfg, "repair")
    pool = json.load(open(os.path.join(ROOT, "backend/tools/_tmp",
                                       "o7e_rp2_repair_pool.json"), encoding="utf-8"))
    out_path = os.path.join(ROOT, "backend/tools/_tmp", "o7e_repair3_RP-B.json")
    results = []
    if os.path.exists(out_path):
        results = json.load(open(out_path, encoding="utf-8"))
    done = {r["case_id"] for r in results}
    for p in pool:
        if p["case_id"] in done:
            continue
        case = {"case_id": p["case_id"], "category": "repair3",
                "question": p["question"], "persona": "general",
                "applicability": {}, "evidence_expectation": "PRIMARY_REQUIRED"}
        print(f"== {p['case_id']}", flush=True)
        try:
            r = run_case_paired(case, mk_n, mk_r)
        except Exception as e:
            r = {"case_id": p["case_id"], "error": str(e)[:200]}
        results = [x for x in results if x["case_id"] != p["case_id"]] + [r]
        json.dump(results, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        v2 = r.get("VALID_AFTER_2")
        v3 = r.get("VALID_AFTER_3")
        print(f"   AT2={v2} AT3={v3} issues={r.get('ISSUE_COUNTS')}", flush=True)
    # 聚合
    ok = [r for r in results if "error" not in r]
    pub2 = sum(1 for r in ok if r.get("published_at_2"))
    pub3 = sum(1 for r in ok if r.get("published_at_3"))
    trig = [r for r in ok if len(r.get("ISSUE_COUNTS") or []) > 1]
    conv2 = sum(1 for r in trig if r.get("VALID_AFTER_2"))
    conv3 = sum(1 for r in trig if r.get("VALID_AFTER_3"))
    eligible = [r for r in trig if r.get("VALID_AFTER_2") is False]
    rescued = [r for r in eligible if r.get("VALID_AFTER_3")]
    out = {
        "config": RP_B, "model": cfg.requested_model,
        "PUBLICATIONS_AT_2": pub2, "PUBLICATIONS_AT_3": pub3,
        "REPAIR_TRIGGERED": len(trig),
        "REPAIR_CONVERGENCE_AT_2": round(conv2 / max(len(trig), 1), 3),
        "REPAIR_CONVERGENCE_AT_3": round(conv3 / max(len(trig), 1), 3),
        "REPAIR3_ELIGIBLE_CASES": len(eligible),
        "REPAIR3_RESCUED_CASES": len(rescued),
        "REPAIR3_RESCUE_RATE": round(len(rescued) / max(len(eligible), 1), 3)
                             if eligible else None,
        "EMPTY_FINAL_AT_3": sum(1 for r in ok if r.get("EMPTY_FINAL")),
        "ISSUE_TRAJECTORIES": {r["case_id"]: r.get("ISSUE_COUNTS") for r in ok},
        "rescued_ids": [r["case_id"] for r in rescued],
        "PRODUCTION_MAX_REPAIRS_CHANGED": False,
    }
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
