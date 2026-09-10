# -*- coding: utf-8 -*-
"""O7-E V3-RP2: Scholarly Retrieval Coverage RCA——零 Agent/零 Judge/零网络。

§1 从已存在 V3 artifact 提取 R25 真实 retrieval trace;
§2 离线探测 O7-D 本地 curated registry（FTS5, 只读）对 RCA query families 的覆盖。
输出 docs/evidence/V3_R25_RETRIEVAL_RCA.json。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

QUERY_FAMILIES = [
    {"family": "wang_yangming_cn", "queries": ["王阳明"]},
    {"family": "wang_yangming_en", "queries": ["Wang Yangming"]},
    {"family": "wang_shouren", "queries": ["Wang Shouren"]},
    {"family": "zhu_xi_cn", "queries": ["朱熹"]},
    {"family": "zhu_xi_en", "queries": ["Zhu Xi"]},
    {"family": "zhixingheyi", "queries": ["知行合一"]},
    {"family": "unity_knowledge_action", "queries": ["unity of knowledge and action"]},
    {"family": "gewu_cn", "queries": ["格物"]},
    {"family": "gewu_en", "queries": ["gewu", "investigation of things"]},
    {"family": "neo_confucianism", "queries": ["Neo-Confucianism",
                                               "Song-Ming Confucianism"]},
    {"family": "great_learning", "queries": ["Great Learning", "Daxue"]},
]


def extract_r25_trace(v3_artifact_path):
    runs = json.load(open(v3_artifact_path, encoding="utf-8"))
    r25 = next(r for r in runs if r["case_id"] == "R25")
    sp = r25.get("scholarly_provenance") or {}
    calls = []
    # per-call query/args 未归档（done.tool_calls 未入 artifact）→ 如实记 null;
    # 可机械给出的是: 调用次数 + 合并后的返回记录
    for i in range(sp.get("SCHOLARLY_SEARCH_CALLS") or 0):
        calls.append({"call_index": i + 1, "query": None,
                      "args": None, "provider_mode": None,
                      "returned_count": None,
                      "note": "per-call 数据未归档（done.result_full 已剥离）"})
    fetches = []
    for e in sp.get("scholarly_evidence") or []:
        fetches.append({"source_record_id": e.get("source_record_id"),
                        "access_level_after": e.get("access_level_after"),
                        "content_evidence": e.get("content_evidence")})
    records = []
    for rec in sp.get("scholarly_records") or []:
        records.append({"source_record_id": rec.get("source_record_id"),
                        "title": rec.get("title"),
                        "year": rec.get("publication_year"),
                        "source_category": rec.get("source_category"),
                        "access_level": rec.get("access_level"),
                        "provider": rec.get("provider"),
                        "rank": None})
    return {
        "actual_scholarly_search_calls": sp.get("SCHOLARLY_SEARCH_CALLS", 0),
        "actual_fetch_calls": sp.get("SCHOLARLY_SOURCE_FETCH_CALLS", 0),
        "content_evidence_count": sum(1 for e in (sp.get("scholarly_evidence") or [])
                                      if e.get("content_evidence")),
        "calls": calls,
        "records": records,
        "fetches": fetches,
        "tool_trajectory": r25.get("tool_trajectory") or [],
    }


def probe_local_corpus():
    """§2: 离线只读探测本地 curated registry（FTS5 BM25）。"""
    import scholarly_sources as SS
    import scholarly_registry as SR
    families = []
    total = 0
    for fam in QUERY_FAMILIES:
        hits = []
        for q in fam["queries"]:
            try:
                res = SS._local_results(q, limit=8)
            except Exception:
                res = []
            hits.extend({"query": q,
                         "source_record_id": r.get("source_record_id"),
                         "title": (r.get("title") or "")[:80],
                         "retrieval_origin": r.get("retrieval_origin")}
                        for r in res)
        total += len(hits)
        families.append({"family": fam["family"],
                         "queries": fam["queries"],
                         "hit_count": len(hits),
                         "hits": hits[:5]})
    return {"families": families, "total_hits": total}


def main():
    v3_path = os.path.join(ROOT, "docs/evidence/o7e_calib_V3_HOLDOUT.json")
    trace = extract_r25_trace(v3_path)
    corpus = probe_local_corpus()
    out = {"V3_R25_RETRIEVAL_RCA": True,
           "NETWORK_CALLS": 0,
           "NEW_AGENT_RUN": False,
           "NEW_JUDGE_RUN": False,
           "r25_trace": trace,
           "local_corpus_probe": corpus}
    out_path = os.path.join(ROOT, "docs/evidence/V3_R25_RETRIEVAL_RCA.json")
    json.dump(out, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"families_total_hits": corpus["total_hits"],
                      "r25_search_calls": trace["actual_scholarly_search_calls"],
                      "r25_records": len(trace["records"]),
                      "r25_content_evidence": trace["content_evidence_count"]},
                     ensure_ascii=False))
    for f in corpus["families"]:
        print(" ", f["family"], "hits:", f["hit_count"])


if __name__ == "__main__":
    main()
