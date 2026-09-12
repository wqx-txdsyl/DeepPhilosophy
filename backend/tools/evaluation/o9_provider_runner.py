# -*- coding: utf-8 -*-
"""O9 provider benchmark runner（evaluation-only）。

同一冻结 30-query set × provider 配置:
A=Crossref, B=OpenAlex, C=Crossref+OpenAlex(合并去重 Top-10),
D=MetaSo, E=MetaSo+Crossref+OpenAlex —— D/E 受 AUTH 限制（无 credential）时
按任务书记录 AUTHENTICATION_REQUIRED=true 并暂停该部分。
复用生产 scholarly_sources 客户端（测量真实生产检索行为）+ MetaSo MCP 直连探测。
原始结果全量保留（RAW_RESULTS_PRESERVED）。
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
EVID = os.path.join(ROOT, "docs/evidence")
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import scholarly_sources as SS  # noqa: E402  生产 Crossref/OpenAlex 客户端

TOP_K = 10
OUT = os.path.join(ROOT, "backend/tools/_tmp/o9_provider_results.json")
METASO_ENDPOINT = "https://metaso.cn/api/mcp"


def _norm(s):
    return (s or "").lower()


def term_hit(query, rec):
    """机械相关性: 查询核心词命中 title/abstract（>=2 字词元）。"""
    terms = [t for t in _norm(query).replace("？", " ").split() if len(t) >= 2]
    hay = _norm((rec.get("title") or "")) + " " + _norm(rec.get("abstract_text") or "")
    return any(t in hay for t in terms)


def measure(records, query):
    n = len(records)
    relevant = sum(1 for r in records if term_hit(query, r))
    doi = sum(1 for r in records if r.get("doi"))
    abstract = sum(1 for r in records if r.get("abstract_text"))
    meta_ok = sum(1 for r in records if r.get("title") and r.get("authors")
                  and r.get("publication_year"))
    cjk = sum(1 for r in records
              if any("\u4e00" <= ch <= "\u9fff" for ch in (r.get("title") or "")))
    fps = [r.get("fingerprint") for r in records if r.get("fingerprint")]
    dup = len(fps) - len(set(fps))
    return {"records": n, "relevant_topk": relevant,
            "TOP_K_RELEVANCE": round(relevant / max(TOP_K, 1), 3),
            "DOI_COVERAGE": round(doi / max(n, 1), 3),
            "ABSTRACT_RATE": round(abstract / max(n, 1), 3),
            "METADATA_ACCURACY": round(meta_ok / max(n, 1), 3),
            "CJK_TITLES": cjk, "DUPLICATE_RATE": round(dup / max(n, 1), 3)}


def fingerprinted(recs):
    for r in recs:
        if not r.get("fingerprint"):
            try:
                r["fingerprint"] = SS._fingerprint(
                    r.get("title"), (r.get("authors") or [{}])[0].get("name"),
                    r.get("publication_year"), r.get("container_title"))
            except Exception:
                r["fingerprint"] = None
    return recs


def run_crossref(q):
    t0 = time.perf_counter()
    try:
        recs = SS.search_crossref(q, limit=TOP_K)
        return recs, time.perf_counter() - t0, None
    except Exception as e:
        return [], time.perf_counter() - t0, str(e)[:160]


def run_openalex(q):
    t0 = time.perf_counter()
    try:
        recs = SS.search_openalex(q, limit=TOP_K)
        return recs, time.perf_counter() - t0, None
    except Exception as e:
        return [], time.perf_counter() - t0, str(e)[:160]


def merge_c(a, b):
    seen, merged = set(), []
    for r in a + b:
        fp = r.get("fingerprint") or r.get("doi")
        key = r.get("doi") or fp
        if key and key in seen:
            continue
        seen.add(key)
        merged.append(r)
    return merged[:TOP_K]


def metaso_search(q, key=None, size=TOP_K, scope="paper", include_summary=True):
    """MetaSo MCP 直连（Bearer 认证）。无 key 时按协议探测并抛错。"""
    body = {"jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": "metaso_web_search",
                       "arguments": {"q": q, "scope": scope, "size": size,
                                     "includeSummary": include_summary}},
            "id": 1}
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(METASO_ENDPOINT, data=json.dumps(body).encode(),
                                 headers=headers)
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data, time.perf_counter() - t0


def main(only_cats=None):
    qs = json.load(open(os.path.join(EVID, "O9_QUERYSET.json"), encoding="utf-8"))
    runs = []
    if os.path.exists(OUT):
        runs = json.load(open(OUT, encoding="utf-8"))
    done = {r["query_id"] for r in runs}
    for case in qs["cases"]:
        if case["query_id"] in done:
            continue
        if only_cats and case["category"] not in only_cats:
            continue
        q = case["query"]
        print(f"== {case['query_id']}: {q[:40]}", flush=True)
        a, la, ea = run_crossref(q)
        b, lb, eb = run_openalex(q)
        a = fingerprinted(a)
        b = fingerprinted(b)
        c = fingerprinted(merge_c(a, b))
        row = {"query_id": case["query_id"], "category": case["category"],
               "query": q,
               "providers": {
                   "A_crossref": {"latency_s": round(la, 2), "error": ea,
                                  "metrics": measure(a, q), "raw": a[:TOP_K]},
                   "B_openalex": {"latency_s": round(lb, 2), "error": eb,
                                  "metrics": measure(b, q), "raw": b[:TOP_K]},
                   "C_crossref+openalex": {"metrics": measure(c, q), "raw": c[:TOP_K]},
               }}
        runs.append(row)
        json.dump(runs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   A n={len(a)} rel={row['providers']['A_crossref']['metrics']['TOP_K_RELEVANCE']}"
              f" | B n={len(b)} rel={row['providers']['B_openalex']['metrics']['TOP_K_RELEVANCE']}"
              f" | C rel={row['providers']['C_crossref+openalex']['metrics']['TOP_K_RELEVANCE']}",
              flush=True)
    print(f"BASELINE DONE: {len(runs)}/30", flush=True)


if __name__ == "__main__":
    main(only_cats=(sys.argv[1].split(",") if len(sys.argv) > 1 else None))
