# -*- coding: utf-8 -*-
"""O8-R2 报告组装器（evaluation-only）。

读取 backend/tools/_tmp/ 下全部测量产物, 产出 docs/evidence/ 下 7 个交付物:
O8_R2_CAPABILITY_RESULTS / O8_R2_TOOL_AUDIT / O8_R2_EFFICIENCY /
O8_R2_RETRIEVAL_CENSUS / O8_R2_REPAIR_SAFETY_AUDIT /
O8_R2_INTERACTION_OWNERSHIP / O8_R2_FINAL_REPORT.md（CASESET 单独已冻结提交）。
"""
import json
import os
import statistics
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
TMP = os.path.join(ROOT, "backend/tools/_tmp")
EVID = os.path.join(ROOT, "docs/evidence")


def load(name):
    p = os.path.join(TMP, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def dim_scores(judged):
    dims = {}
    for j in judged:
        d = (j.get("judge") or {}).get("dimensions") or {}
        for k, v in d.items():
            if isinstance(v, (int, float)):
                dims.setdefault(k, []).append(v)
    return {k: {"mean": round(statistics.mean(v), 2), "median": statistics.median(v),
                "n": len(v), "lt2": sum(1 for x in v if x < 2)}
            for k, v in dims.items()}


def main():
    bench = load("o8r2_bench.json") or []
    judged = load("o8r2_judge.json") or []
    mech = load("o8r2_mechanical.json") or []
    agen = load("o8r2_agentic.json") or []
    census = load("o8r2_census.json") or {}
    repair = load("o8r2_repair_safety.json") or {}
    own = load("o8r2_ownership.json") or []
    caseset = json.load(open(os.path.join(EVID, "O8_R2_CASESET.json"), encoding="utf-8"))

    jmap = {j["case_id"]: j for j in judged}
    ok = [r for r in bench if (r.get("delivery") or {}).get("run_status") == "COMPLETED"]

    # ── 1. CAPABILITY RESULTS ──────────────────────────────────────
    per_case = []
    for r in bench:
        j = jmap.get(r["case_id"], {})
        rec = {"case_id": r["case_id"], "category": r["category"],
               "publication_state": (r.get("delivery") or {}).get("published"),
               "failure_codes": r.get("failure_codes"),
               "judge_status": j.get("judge_status"),
               "axes": (j.get("judge") or {}).get("axes"),
               "dimensions": (j.get("judge") or {}).get("dimensions"),
               "honesty_flag": (j.get("judge") or {}).get("honesty_flag"),
               "overresearch_flag": (j.get("judge") or {}).get("overresearch_flag"),
               "summary": (j.get("judge") or {}).get("summary"),
               "evidence_refs": r.get("evidence_refs", {}).get("scholarly_provenance"),
               "repair_history": r.get("repair_history")}
        per_case.append(rec)
    cat_perf = {}
    for cat in caseset["categories"]:
        rs = [r for r in bench if r["category"] == cat]
        js = [jmap[r["case_id"]].get("judge") for r in rs if r["case_id"] in jmap]
        pub = sum(1 for r in rs if (r.get("delivery") or {}).get("published"))
        cat_perf[cat] = {
            "cases": len(rs), "published": pub,
            "honesty_flags": sum(1 for j in js if j and j.get("honesty_flag")),
            "overresearch_flags": sum(1 for j in js if j and j.get("overresearch_flag")),
            "dim_mean_overall": round(statistics.mean(
                [v for j in js for v in (j or {}).get("dimensions", {}).values()
                 if isinstance(v, (int, float))]), 2) if js else None,
        }
    capability = {
        "O8_R2_CAPABILITY_RESULTS": True,
        "REVIEWED_BASE": caseset["REVIEWED_BASE"],
        "caseset": {"CASE_COUNT": caseset["CASE_COUNT"], "frozen": caseset["frozen_before_run"],
                    "categories": caseset["categories"]},
        "totals": {"executed": len(bench), "completed": len(ok),
                   "published": sum(1 for r in ok if (r.get("delivery") or {}).get("published")),
                   "judged": len(judged),
                   "honesty_flags_total": sum(1 for j in judged
                                              if (j.get("judge") or {}).get("honesty_flag")),
                   "overresearch_total": sum(1 for j in judged
                                             if (j.get("judge") or {}).get("overresearch_flag"))},
        "category_performance": cat_perf,
        "dimension_statistics": dim_scores(judged),
        "per_case": per_case,
    }
    json.dump(capability, open(os.path.join(EVID, "O8_R2_CAPABILITY_RESULTS.json"),
                               "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── 2. EFFICIENCY ──────────────────────────────────────────────
    def agg(vals):
        vals = [v for v in vals if isinstance(v, (int, float))]
        return {"mean": round(statistics.mean(vals), 2), "median": statistics.median(vals),
                "max": max(vals), "total": sum(vals)} if vals else None
    eff_rows = []
    for r in bench:
        e = r.get("efficiency") or {}
        eff_rows.append({"case_id": r["case_id"], "category": r["category"], **e})
    tok_in = sum((e.get("TOKEN_USAGE") or {}).get("input_tokens") or 0 for e in eff_rows)
    tok_out = sum((e.get("TOKEN_USAGE") or {}).get("output_tokens") or 0 for e in eff_rows)
    efficiency = {
        "O8_R2_EFFICIENCY": True,
        "per_case": eff_rows,
        "aggregate": {
            "LLM_CALLS": agg([e.get("LLM_CALLS") for e in eff_rows]),
            "TOOL_CALLS": agg([e.get("TOOL_CALLS") for e in eff_rows]),
            "RETRIEVAL_ROUNDS": agg([e.get("RETRIEVAL_ROUNDS") for e in eff_rows]),
            "DUPLICATE_CALLS": {"total": sum(e.get("DUPLICATE_CALLS") or 0 for e in eff_rows),
                                "cases_with_dups": sum(1 for e in eff_rows
                                                       if (e.get("DUPLICATE_CALLS") or 0) > 0)},
            "REPAIR_COUNT": {"total": sum(e.get("REPAIR_COUNT") or 0 for e in eff_rows),
                             "cases_with_repair": sum(1 for e in eff_rows
                                                      if (e.get("REPAIR_COUNT") or 0) > 0)},
            "TOTAL_LATENCY": agg([e.get("TOTAL_LATENCY_S") for e in eff_rows]),
            "TOKEN_USAGE": {"input_tokens": tok_in, "output_tokens": tok_out,
                            "total_tokens": tok_in + tok_out},
            "TOKEN_COST": None, "COST_SOURCE": "UNAVAILABLE（无可靠价格/账单来源, 禁止编造估价）",
        },
        "overresearch_analysis": {
            "note": "cat 10 SHOULD_NOT_OVERRESEARCH 的 TOOL_CALLS/LLM_CALLS 对比其他类",
            "cat10": {k: agg([e.get(k) for e in eff_rows if e["category"] == "10_simple_not_overresearch"])
                      for k in ("LLM_CALLS", "TOOL_CALLS", "RETRIEVAL_ROUNDS")},
            "hard_cats": {k: agg([e.get(k) for e in eff_rows
                                  if e["category"] in ("09_research_survey", "11_deep_research")])
                          for k in ("LLM_CALLS", "TOOL_CALLS", "RETRIEVAL_ROUNDS")},
        },
    }
    json.dump(efficiency, open(os.path.join(EVID, "O8_R2_EFFICIENCY.json"),
                               "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── 3. TOOL AUDIT（mechanical + agentic + 分类）─────────────────
    agen_judged = []
    for a in agen:
        rec = a.get("record") or {}
        traj = (rec.get("public_thinking_summary") or {}).get("tool_sequence") or []
        agen_judged.append({"case_id": a["case_id"], "scenario": a["scenario"],
                            "tool": a.get("tool"), "trajectory": traj[:12],
                            "judge_hit": (a.get("judge") or {}).get("SHOULD_CALL_HIT")})
    notcall_traj = next((a["trajectory"] for a in agen_judged
                         if a["scenario"] == "NOTCALL"), [])
    tool_audit = {
        "O8_R2_TOOL_AUDIT": True,
        "TOOL_COUNT": len(mech),
        "mechanical": mech,
        "mechanical_summary": {
            c: dict(Counter(r["checks"].get(c, "MISSING") for r in mech))
            for c in ("VALID_INPUT", "INVALID_INPUT", "EMPTY_RESULT", "BOUNDARY",
                      "FAILURE_PATH", "SCHEMA", "PROVENANCE", "CITATION", "SECURITY")},
        "agentic": agen_judged,
        "should_call_hits": {a["tool"]: a["judge_hit"] for a in agen_judged
                             if a["scenario"] == "SHOULD_CALL"},
        "shared_negative_trajectory": notcall_traj,
        "mechanical_findings": [
            {"id": "O8R2-MECH-1", "severity": "P1",
             "finding": "philosopher_debate 在 speakers 为 JSON 数组时崩溃（agent_tools_memory.py:520 speakers.replace 假设 str）",
             "evidence": "mechanical gate VALID_INPUT=FAIL + 定位 traceback"},
            {"id": "O8R2-MECH-2", "severity": "P1",
             "finding": "search_books 向量路径无空查询守卫且相似度地板 0.35 过低——伪查询/空查询返回不相关结果, EMPTY_RESULT 语义不可达",
             "evidence": "mechanical gate EMPTY_RESULT/FAILURE_PATH=FAIL + 直接探测"},
            {"id": "O8R2-MECH-3", "severity": "P2",
             "finding": "query_graph/get_philosopher/get_school 空字符串输入静默回退到默认实体（柏拉图）而非优雅拒绝",
             "evidence": "mechanical gate FAILURE_PATH=FAIL + 直接探测"},
            {"id": "O8R2-MECH-4", "severity": "P2",
             "finding": "concept_trace 对不存在概念返回模糊命中（无相关性地板）; list_books/history_timeline 过滤器无命中时返回全集",
             "evidence": "mechanical gate EMPTY_RESULT=FAIL"},
        ],
    }
    json.dump(tool_audit, open(os.path.join(EVID, "O8_R2_TOOL_AUDIT.json"),
                               "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── 4. RETRIEVAL CENSUS（回填 72-case 命中）──────────────────────
    ss_cases = [r for r in bench
                if (r.get("evidence_refs") or {}).get("scholarly_provenance", {})
                .get("SCHOLARLY_SEARCH_CALLS")]
    lc_ids = set()
    for r in bench:
        for ev in ((r.get("evidence_refs") or {}).get("scholarly_provenance") or {}).get("scholarly_records_ids", []) or []:
            lc_ids.add(ev)
    primary_hits = sum(1 for r in bench
                       if any(t in ((r.get("public_thinking_summary") or {}).get("tool_sequence") or [])
                              for t in ("search_books", "get_chapter")))
    census_out = dict(census)
    census_out["O8R2_CASE_HITS"] = {
        "cases_using_scholarly_search": len(ss_cases),
        "cases_using_primary_retrieval": primary_hits,
        "local_curated_record_ids_hit": len(lc_ids),
        "quote_verifiable_hit_note": "judge honesty_flag=false 比例 + citations 抽样",
        "honest_degradation_cases": ["O8R2-34（正蒙不在库）", "AG-SHARE-DEGRADED"],
    }
    census_out["O8_R2_RETRIEVAL_CENSUS"] = True
    json.dump(census_out, open(os.path.join(EVID, "O8_R2_RETRIEVAL_CENSUS.json"),
                               "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── 5. REPAIR SAFETY ───────────────────────────────────────────
    repair_out = dict(repair)
    repair_out["O8_R2_REPAIR_SAFETY_AUDIT"] = True
    json.dump(repair_out, open(os.path.join(EVID, "O8_R2_REPAIR_SAFETY_AUDIT.json"),
                               "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── 6. INTERACTION / OWNERSHIP ─────────────────────────────────
    interaction = {
        "O8_R2_INTERACTION_OWNERSHIP": True,
        "orphans": own,
        "ruling_note": "Reviewer C 项裁定: 本轮全部不删除不入库; 本审计仅产 KEEP/DEPRECATE/DELETE 建议与证据",
        "interaction_cases_note": "cat 12 多轮/Reader Context/工具模式案例见 O8_R2_CAPABILITY_RESULTS per_case O8R2-67..72",
    }
    json.dump(interaction, open(os.path.join(EVID, "O8_R2_INTERACTION_OWNERSHIP.json"),
                                "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("assembled:",
          ["O8_R2_CAPABILITY_RESULTS.json", "O8_R2_EFFICIENCY.json",
           "O8_R2_TOOL_AUDIT.json", "O8_R2_RETRIEVAL_CENSUS.json",
           "O8_R2_REPAIR_SAFETY_AUDIT.json", "O8_R2_INTERACTION_OWNERSHIP.json"])
    print("bench:", len(bench), "judged:", len(judged), "mech:", len(mech),
          "agentic:", len(agen))


if __name__ == "__main__":
    main()
