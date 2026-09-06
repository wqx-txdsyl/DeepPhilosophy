# -*- coding: utf-8 -*-
"""O7-E E2E runner——生产模型（deepseek-chat）全链路跑案例, 捕获:
  final answer / tool trace / evidence digest / delivery metrics（双轴 B）。

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_runner.py CAL|HOLDOUT|SMOKE [case_id]
产出: backend/tools/_tmp/o7e_runs_<scope>.json（支持断点续跑）
"""
import asyncio
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7e_cases as CASES
import engine_langgraph as ENG

TMP = os.path.join(ROOT, "backend", "tools", "_tmp")


def _as_list(v, n=20):
    if isinstance(v, list):
        return v[:n]
    if isinstance(v, dict):
        return {k: v[k] for k in list(v)[:n]}
    return v


def _ev_digest(ev):
    """证据摘要（judge 输入用）: primary 检索与 scholarly 记录。"""
    if not isinstance(ev, dict):
        return ev
    out = {}
    for k, v in ev.items():
        if isinstance(v, list):
            out[k] = v[:10]
        elif isinstance(v, dict):
            out[k] = {kk: v[kk] for kk in list(v)[:10]}
        else:
            out[k] = v
    return out


def run_case(case):
    """全链路跑一个案例; 返回 answer/tool_trace/delivery/事件摘要。"""
    events = []
    t0 = time.time()

    async def collect():
        async for ev in ENG.stream_agent(case["question"], [], case["persona"], "zh"):
            events.append(ev)

    asyncio.run(collect())
    # 最终答案 = 最后一次 validation_failed 之后的 token 段（修复轮文本不计入发布答案）
    last_fail = max((i for i, e in enumerate(events)
                     if e.get("type") == "validation_failed"), default=-1)
    tokens = [e.get("content", "") for i, e in enumerate(events)
              if e.get("type") == "token" and i > last_fail]
    answer = "".join(tokens)
    tools = [e for e in events if e.get("type") in ("tool", "tool_start")]
    tool_names = []
    for e in tools:
        n = e.get("name") or e.get("tool")
        if n and n not in tool_names:
            tool_names.append(n)
    done = next((e for e in reversed(events) if e.get("type") == "done"), {})
    # RP1 Final Closure C: run_status 分类——余额类阻断 ≠ 产品交付失败, 不入发布分母
    err_blob = " ".join(str(e.get("content") or e.get("message") or "")
                        for e in events if e.get("type") == "error")
    if "余额不足" in err_blob or "Insufficient Balance" in err_blob or "402" in err_blob:
        run_status = "BLOCKED_MODEL_BILLING"
    elif answer.strip() or done:
        run_status = "COMPLETED"
    else:
        run_status = "RUN_ERROR"
    # O7-E RP1 §4: 真值来自 done.validation（repairs_used/history）, 不再从 SSE 计数推导
    val = (done.get("validation") or {})
    repairs_used = val.get("repairs_used", 0)
    hist = val.get("history") or []
    val_failures = sum(1 for h in hist if not h.get("ok"))
    val_fails = [e for e in events if e.get("type") == "validation_failed"]
    errors = [e for e in events if e.get("type") == "error"]
    return {
        "case_id": case["case_id"], "category": case["category"],
        "question": case["question"], "persona": case["persona"],
        "answer": answer,
        "tool_calls": tool_names,
        "tool_call_count": len([e for e in events if e.get("type") == "tool_start"]),
        "delivery": {
            "run_status": run_status,
            "publication_denominator_member": run_status == "COMPLETED",
            "published": (bool(answer.strip()) and not errors
                          if run_status == "COMPLETED" else None),
            "validation_attempts": len(hist),
            "validation_failures": val_failures,
            "repair_attempts": repairs_used,
            "repair_success": (repairs_used > 0 and bool(answer.strip()) and
                               not errors) if repairs_used else None,
            "repair_exhaustion": (repairs_used >= (val.get("max_validation_repairs") or 2)
                                  and not bool(val.get("result", {}).get("ok"))),
            "final_validation_result": bool(val.get("result", {}).get("ok")),
            "final_validation_issue_codes": [i.get("code") for i in
                                             val.get("result", {}).get("issues", [])][:8],
            "terminal_pending": (bool(errors) and not answer.strip()
                                 and run_status == "COMPLETED"),
            "tool_loop_abort": any("预算" in str(e.get("content") or e.get("message", "")) or
                                   e.get("type") == "tool_cancel" for e in events),
        },
        "done_payload_keys": sorted(done.keys()) if done else [],
        "citations": _as_list(done.get("citations")) if done else [],
        "quote_bound": _as_list(done.get("quote_bound")) if done else [],
        "evidence_digest": _ev_digest(done.get("evidence")) if done else None,
        "elapsed_s": round(time.time() - t0, 1),
        "error_messages": [str(e.get("content") or e.get("message", ""))[:300]
                           for e in errors][:3],
    }


def main(scope, only=None):
    cases = {"CAL": CASES.CALIBRATION_CASES,
             "HOLDOUT": CASES.HOLDOUT_CASES,
             "SMOKE": CASES.LIVE_SMOKE_CASES}[scope]
    out_path = os.path.join(TMP, f"o7e_runs_{scope}.json")
    runs = []
    if os.path.exists(out_path):
        runs = json.load(open(out_path, encoding="utf-8"))
    done_ids = {r["case_id"] for r in runs}
    for c in cases:
        if only and c["case_id"] != only:
            continue
        if c["case_id"] in done_ids:
            continue
        print(f"== {c['case_id']} [{c['category']}]", flush=True)
        try:
            r = run_case(c)
        except Exception as e:
            r = {"case_id": c["case_id"], "question": c["question"],
                 "run_error": str(e)[:400], "delivery": {"published": False}}
        runs = [x for x in runs if x["case_id"] != c["case_id"]] + [r]
        json.dump(runs, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        d = r.get("delivery", {})
        print(f"   published={d.get('published')} tools={r.get('tool_call_count')} "
              f"val_rej={d.get('validation_rejections')} {r.get('elapsed_s','?')}s "
              f"len={len(r.get('answer',''))}", flush=True)
    completed = [r for r in runs if r.get("delivery", {}).get("run_status") == "COMPLETED"]
    pub = sum(1 for r in completed if r.get("delivery", {}).get("published"))
    blocked = sum(1 for r in runs if r.get("delivery", {}).get("run_status") == "BLOCKED_MODEL_BILLING")
    errs = len(runs) - len(completed) - blocked
    required = {"CAL": 12, "HOLDOUT": 28, "SMOKE": 8}[scope]
    status = ("BLOCKED_INCOMPLETE" if len(completed) < required else
              ("PASS_RATE" if pub / max(len(completed), 1) >= 0.9 else "RATE_FAIL"))
    print(json.dumps({"scope": scope, "cases": len(runs),
                      "completed": len(completed), "published_among_completed": pub,
                      "publication_rate_completed": round(pub / max(len(completed), 1), 3),
                      "blocked_model_billing": blocked, "run_errors": errs,
                      "FINAL_GATE_STATUS": status}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
