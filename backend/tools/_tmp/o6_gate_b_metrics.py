# -*- coding: utf-8 -*-
"""O6 Gate B — 最终指标聚合（从冻结的 cases/ + conversations/ 计算 §6–§19 机械指标）。

运行: .venv/Scripts/python.exe backend/tools/_tmp/o6_gate_b_metrics.py
输出: backend/tools/_tmp/o6_gate/gate_b/metrics.json
"""
import glob
import json
import os
import statistics

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "o6_gate", "gate_b")
CASES = os.path.join(HERE, "cases")
CONVS = os.path.join(HERE, "conversations")


def load_cases():
    out = []
    for p in sorted(glob.glob(os.path.join(CASES, "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f)["result"])
    return out


def pctl(vals, q):
    if not vals:
        return 0
    s = sorted(vals)
    idx = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
    return s[idx]


def main():
    cases = load_cases()
    core = [r for r in cases if r["category"] in
            ("A", "B", "C", "D", "E", "F", "G", "H")]
    sup = [r for r in cases if r["category"] not in ("A", "B", "C", "D", "E", "F", "G", "H")]
    pubs = [r for r in cases if r["status"] == "PUBLISHED"]
    rejects = [r for r in cases if r["status"] == "SAFE_REJECT"]

    m = {"by_case": {}, "core": {}, "supplementary": {}, "all": {}, "convos": {}}

    def agg(rs):
        tools = [r["tool_count"] for r in rs]
        durs = [r["duration_s"] for r in rs]
        zero = [r for r in rs if r["tool_count"] == 0]
        repair_att = [r for r in rs if ((r.get("validation") or {}).get("repairs_used") or 0) > 0]
        qb = {k: 0 for k in ("quotes", "verified_exact", "verified_near", "memory_only",
                             "stitched", "unverified_blockquote", "memory_only_exact_claim")}
        for r in pubs:
            s = ((r.get("quote_bound") or {}).get("summary") or {})
            for k in qb:
                qb[k] += s.get(k, 0) or 0
        return {
            "n": len(rs),
            "published": sum(1 for r in rs if r["status"] == "PUBLISHED"),
            "safe_reject": sum(1 for r in rs if r["status"] == "SAFE_REJECT"),
            "engine_fail": sum(1 for r in rs if str(r["status"]).startswith("FAIL")),
            "tools_avg": round(statistics.mean(tools), 2) if tools else 0,
            "tools_median": statistics.median(tools) if tools else 0,
            "tools_p95": pctl(tools, 0.95),
            "tools_max": max(tools) if tools else 0,
            "search_calls": sum(r["search_calls"] for r in rs),
            "read_calls": sum(r["read_calls"] for r in rs),
            "zero_tool": len(zero),
            "zero_tool_published": sum(1 for r in zero if r["status"] == "PUBLISHED"),
            "dup_reused": sum((r.get("budget") or {}).get("duplicate_reused", 0) for r in rs),
            "no_gain": sum((r.get("budget") or {}).get("no_gain", 0) for r in rs),
            "hard_ceiling": sum(1 for r in rs if (r.get("budget") or {}).get("hard")),
            "repair_attempted": len(repair_att),
            "repair_success_after": sum(1 for r in repair_att if r["status"] == "PUBLISHED"),
            "repair_exhausted": sum(1 for r in repair_att if r["status"] != "PUBLISHED"),
            "quote_bound_pub": qb,
            "unverified_citation_pub_cases": sum(
                1 for r in pubs if (r.get("citation_sanitize") or {}).get("unverified_before")),
            "runtime_thinking_events": sum(r["event_audit"]["runtime_thinking_events"] for r in rs),
            "unknown_event_types": sorted({t for r in rs for t in r["event_audit"]["unknown_event_types"]}),
            "duplicate_visible_events": sum(r["event_audit"]["duplicate_visible_events"] for r in rs),
            "unparented_tool_results": sum(r["event_audit"]["unparented_tool_results"] for r in rs),
            "ownership_fingerprint_cases": [r["id"] for r in rs if r["ownership_fingerprints"]],
            "dur_p50": pctl(durs, 0.5), "dur_p95": pctl(durs, 0.95), "dur_max": max(durs) if durs else 0,
        }

    m["core"] = agg(core)
    m["supplementary"] = agg(sup)
    m["all"] = agg(cases)
    for r in cases:
        m["by_case"][r["id"]] = {
            "category": r["category"], "fresh": r["fresh"], "agent": r["agent"],
            "status": r["status"], "tools": r["tool_count"],
            "search": r["search_calls"], "read": r["read_calls"],
            "dur": r["duration_s"], "chars": r["answer_chars"],
            "repairs": (r.get("validation") or {}).get("repairs_used") or 0,
            "hard": bool((r.get("budget") or {}).get("hard")),
            "dup_reused": (r.get("budget") or {}).get("duplicate_reused", 0),
            "no_gain": (r.get("budget") or {}).get("no_gain", 0),
            "quotes": (r.get("quote_bound") or {}).get("summary") or {},
            "validator_ok": bool(((r.get("validation") or {}).get("result") or {}).get("ok")),
            "issue_codes": [i.get("code") for i in (((r.get("validation") or {}).get("result") or {}).get("issues") or [])],
            "thinking_events": r["event_audit"]["thinking_events"],
            "thinking_initiators": r["event_audit"]["thinking_by_initiator"],
            "runtime_thinking": r["event_audit"]["runtime_thinking_events"],
            "unknown_events": r["event_audit"]["unknown_event_types"],
            "dup_visible": r["event_audit"]["duplicate_visible_events"],
            "unparented": r["event_audit"]["unparented_tool_results"],
            "fingerprints": r["ownership_fingerprints"],
            "causal_auto_tools": (r.get("causal") or {}).get("engine_cognitive_auto_tools"),
            "final_owner": (r.get("final_ownership") or {}).get("final_text_owner"),
            "temporal": r.get("temporal"),
        }

    # conversations
    conv_out = {}
    for p in sorted(glob.glob(os.path.join(CONVS, "*.json"))):
        with open(p, encoding="utf-8") as f:
            c = json.load(f)
        conv_out[c["id"]] = {
            "gate": c["gate"], "n_turns": c["n_turns"],
            "published_turns": c["published_turns"],
            "turns": [{"tid": t["id"], "status": t["status"], "tools": t["tool_count"],
                       "dur": t["duration_s"], "chars": t["answer_chars"],
                       "repairs": (t.get("validation") or {}).get("repairs_used") or 0,
                       "runtime_thinking": t["event_audit"]["runtime_thinking_events"],
                       "unknown_events": t["event_audit"]["unknown_event_types"],
                       "unparented": t["event_audit"]["unparented_tool_results"],
                       "dup_visible": t["event_audit"]["duplicate_visible_events"]}
                      for t in c["turns"]],
        }
    m["convos"] = conv_out

    out = os.path.join(HERE, "metrics.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print(f"metrics → {out}")
    print(json.dumps({k: m["all"][k] for k in
                      ("n", "published", "safe_reject", "engine_fail", "tools_avg", "tools_p95",
                       "search_calls", "read_calls", "zero_tool", "zero_tool_published",
                       "hard_ceiling", "repair_attempted", "repair_success_after",
                       "repair_exhausted", "quote_bound_pub", "runtime_thinking_events",
                       "duplicate_visible_events", "unparented_tool_results",
                       "ownership_fingerprint_cases")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
