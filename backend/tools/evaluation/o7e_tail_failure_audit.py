# -*- coding: utf-8 -*-
"""O7-E V3-RP1: tail failure audit——离线机械提取所有 REQUIRED ∧ median<2。

SOURCE = V3_FINAL_HOLDOUT_JUDGE(.json/_summary.json) + o7e_calib_V3_HOLDOUT.json
零 post-hoc rejudge / 零新检索。输出 docs/evidence/V3_TAIL_FAILURE_AUDIT.json。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


def build_audit(judge_path, runs_path, summary_path):
    judged = json.load(open(judge_path, encoding="utf-8"))
    runs = {r["case_id"]: r for r in json.load(open(runs_path, encoding="utf-8"))}
    summary = json.load(open(summary_path, encoding="utf-8"))
    entries = []
    for j in judged:
        cid = j["case_id"]
        run = runs.get(cid, {})
        sp = run.get("scholarly_provenance") or {}
        rm = j.get("replay_meta") or {}
        for d, dv in (j.get("dims") or {}).items():
            if dv.get("applicability") != "REQUIRED":
                continue
            if not isinstance(dv.get("median"), (int, float)) or dv["median"] >= 2:
                continue
            votes_archive = j.get("votes_archive") or []
            scores, rationales, spans = [], [], []
            for v in votes_archive:
                vd = (v.get("dimensions") or {}).get(d) or {}
                scores.append(vd.get("score"))
                rationales.append(vd.get("rationale"))
                spans.append(vd.get("supporting_spans"))
            entries.append({
                "case_id": cid,
                "question": run.get("question"),
                "dimension": d,
                "median": dv["median"],
                "vote_scores": scores,
                "vote_rationales": [str(x)[:400] for x in rationales],
                "supporting_spans": spans,
                "missing_requirements": [],
                "scholarly_search_calls": sp.get("SCHOLARLY_SEARCH_CALLS", 0),
                "scholarly_fetch_calls": sp.get("SCHOLARLY_SOURCE_FETCH_CALLS", 0),
                "content_evidence_count": sum(
                    1 for e in (sp.get("scholarly_evidence") or [])
                    if e.get("content_evidence")),
                "access_levels": sp.get("SCHOLARLY_ACCESS_LEVELS") or {},
                "read_chapters_recorded": rm.get("read_chapters_recorded"),
                "read_chapters_materialized": rm.get("read_chapters_materialized"),
                "read_chapters_materialize_failed":
                    rm.get("read_chapters_materialize_failed"),
                "fatal_flags": j.get("fatal") or [],
            })
    return {
        "V3_TAIL_FAILURE_AUDIT": True,
        "SOURCE": ["docs/evidence/V3_FINAL_HOLDOUT_JUDGE.json",
                   "docs/evidence/V3_FINAL_HOLDOUT_JUDGE_summary.json",
                   "docs/evidence/o7e_calib_V3_HOLDOUT.json"],
        "NO_POSTHOC_REJUDGE": True,
        "NO_NEW_RETRIEVAL": True,
        "TAIL_FAILURE_COUNT": len(entries),
        "SOURCE_SUMMARY_REQUIRED_DIMENSION_MEDIAN_LT_2":
            summary.get("REQUIRED_DIMENSION_MEDIAN_LT_2"),
        "entries": entries,
    }


def main():
    base = os.path.join(ROOT, "docs/evidence")
    audit = build_audit(
        os.path.join(base, "V3_FINAL_HOLDOUT_JUDGE.json"),
        os.path.join(base, "o7e_calib_V3_HOLDOUT.json"),
        os.path.join(base, "V3_FINAL_HOLDOUT_JUDGE_summary.json"))
    out = os.path.join(base, "V3_TAIL_FAILURE_AUDIT.json")
    json.dump(audit, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: audit[k] for k in ("TAIL_FAILURE_COUNT",
         "SOURCE_SUMMARY_REQUIRED_DIMENSION_MEDIAN_LT_2")}, ensure_ascii=False))
    for e in audit["entries"]:
        print(" ", e["case_id"], e["dimension"], "median=", e["median"],
              "votes=", e["vote_scores"])


if __name__ == "__main__":
    main()
