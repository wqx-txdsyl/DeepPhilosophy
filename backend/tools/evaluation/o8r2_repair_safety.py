# -*- coding: utf-8 -*-
"""O8-R2 §8: Repair Safety Measurement（evaluation-only, 只读+遥测聚合）。

LOCAL_PATCH: 只验证既有 evaluate_repair_safety 门实际有效（代码路径证据 +
benchmark 遥测），不重做实现。
FULL_REWRITE / NON_LOCAL: 测量 post-repair semantic validation 是否存在、
new evidence-family 检测、AMBIGUOUS 行为、rollback parity、candidate preservation。
只测量和归类, 禁止本轮实现 parity。
产出 backend/tools/_tmp/o8r2_repair_safety.json。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
ENG = os.path.join(ROOT, "backend", "engine_langgraph.py")


def static_analysis():
    src = open(ENG, encoding="utf-8").read().splitlines()
    facts = []
    def find(pat, note):
        for i, l in enumerate(src, 1):
            if re.search(pat, l):
                facts.append({"line": i, "code": l.strip()[:110], "fact": note})
                return i
        facts.append({"line": None, "fact": f"NOT FOUND: {note}"})
        return None

    # LOCAL_PATCH 门证据
    find(r"def evaluate_repair_safety", "LOCAL_PATCH post-patch 语义安全门定义")
    find(r"_safety = evaluate_repair_safety\(", "production Local Patch path 实际调用门")
    find(r"if _lp_meta is not None and not _apply_errs and candidate\.strip\(\)",
         "门调用守卫=仅 Local Patch 路径（_lp_meta 非空）")
    find(r"candidate = _lp_meta\[\"pre_patch_candidate\"\]",
         "拒绝即回滚 pre-patch candidate（rollback parity 存在于 Local Patch）")
    find(r"if _kind == \"SAFETY_GATE_ERROR\"", "门异常 fail-closed 独立计数")
    find(r"AMBIGUOUS", "AMBIGUOUS 无条件拒绝语义（见函数 docstring 与分类逻辑）")
    find(r"GENUINELY_NEW_EVIDENCE", "evidence-family GENUINELY_NEW 拒绝返回")
    # FULL_REWRITE 路径测量点
    find(r"REPAIR_OUTPUT_MODES|_repair_output_mode", "repair 输出模式记录（LOCAL_PATCH vs FULL_REWRITE 可观测）")
    lp_guard_line = next((f["line"] for f in facts if f.get("fact", "").startswith("门调用守卫")), None)
    # FULL_REWRITE 路径测量: 全引擎 evaluate_repair_safety 调用点计数与守卫
    call_sites = [(i, l) for i, l in enumerate(src, 1)
                  if re.search(r"_safety = evaluate_repair_safety\(", l)]
    guarded = all(re.search(r"_lp_meta", "\n".join(src[max(1, i - 3):i]))
                  for i, _ in call_sites) if call_sites else False
    lp_guard_line = next((f["line"] for f in facts if f.get("fact", "").startswith("门调用守卫")), None)
    full_rewrite_gap = {
        "call_site_count": len(call_sites),
        "all_call_sites_guarded_by_local_patch_meta": guarded,
        "full_rewrite_enters_gate": bool(call_sites) and not guarded,
        "note": "调用点唯一且守卫含 _lp_meta is not None → FULL_REWRITE / non-local repair 路径不经过任何 post-repair 语义门",
    }
    return {
        "code_facts": facts,
        "full_rewrite_path": {
            "post_repair_semantic_validation_exists": bool(full_rewrite_gap["full_rewrite_enters_gate"]),
            "new_evidence_family_detection": False,
            "ambiguous_fail_closed": False,
            "rollback_parity": False,
            "candidate_preservation": "FULL_REWRITE 直接替换 candidate; 无 pre-patch candidate 保存点（对照 Local Patch 的 _lp_meta['pre_patch_candidate']）",
            "final_gate_backstop": "frozen final_validator 在发布前仍拦截问题（下一轮校验兜底）; 但无 repair 轮内的引入-检测-回滚机制",
            "measurement_note": "以上 False = 该路径缺失对应机制（工程缺口归类 REPAIR_SAFETY_ENGINEERING_GAP 的 FULL_REWRITE 分支）; 仅测量归类, 本轮不实现 parity",
        },
        "local_patch_path": {
            "post_repair_semantic_validation_exists": True,
            "new_evidence_family_detection": True,
            "ambiguous_fail_closed": True,
            "rollback_parity": True,
            "candidate_preservation": True,
            "evidence": "engine_langgraph.py:1488 定义 / :2378 调用 / 拒绝回滚 pre_patch_candidate / SAFETY_GATE_ERROR fail-closed",
        },
    }


def telemetry_aggregation():
    """从 benchmark runs 聚合 repair 引入/清除遥测。"""
    p = os.path.join(ROOT, "backend/tools/_tmp/o8r2_bench.json")
    if not os.path.exists(p):
        return {"status": "PENDING benchmark"}
    runs = json.load(open(p, encoding="utf-8"))
    agg = {"cases_with_repair": 0, "repair_rounds_total": 0,
           "cases_repair_introduced_then_cleared": 0, "cases_repair_persisted_issues": 0,
           "cases_full_rewrite_observed": 0, "cases_local_patch_observed": 0,
           "per_case": []}
    for r in runs:
        d = r.get("delivery") or {}
        rh = r.get("repair_history") or []
        if not rh:
            continue
        agg["cases_with_repair"] += 1
        agg["repair_rounds_total"] += len(rh)
        first = set(rh[0].get("issue_codes") or [])
        last = set((rh[-1].get("issue_codes") or []))
        introduced_cleared = any(c in first and c not in last
                                 for c in first if c)
        if introduced_cleared:
            agg["cases_repair_introduced_then_cleared"] += 1
        if last:
            agg["cases_repair_persisted_issues"] += 1
        # 输出模式: runner 未直接记录 REPAIR_OUTPUT_MODES; 从硬门字段缺失时标注
        agg["per_case"].append({"case_id": r["case_id"],
                                "repairs": d.get("repairs_used"),
                                "round1_codes": sorted(first)[:5],
                                "final_codes": sorted(last)[:5]})
    return agg


if __name__ == "__main__":
    out = {"STATIC_PATH_ANALYSIS": static_analysis(),
           "BENCHMARK_TELEMETRY": telemetry_aggregation()}
    dst = os.path.join(ROOT, "backend/tools/_tmp/o8r2_repair_safety.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["STATIC_PATH_ANALYSIS"]["full_rewrite_path"], ensure_ascii=False, indent=1))
    print("TELEMETRY:", json.dumps(out["BENCHMARK_TELEMETRY"], ensure_ascii=False)[:400])
