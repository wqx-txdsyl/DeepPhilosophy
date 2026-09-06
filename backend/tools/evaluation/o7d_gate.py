# -*- coding: utf-8 -*-
"""O7-D §38-44: Corpus gates——offline local / combined retrieval + 全审计。

模式:
  L (local-only): 双 live provider 强制失败（网络禁用语义）→ LOCAL_CURATED
  C (combined):  LOCAL + live（当前 Crossref 可用; OpenAlex 当日预算耗尽如实记录）
审计:
  R registry integrity / D DOI 100% / B bibliographic sample>=50 / E evidence
产出: docs/evidence/PHIAGENT_O7D_CORPUS_GATE.json

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7d_gate.py L|C|R|D|B|E|ALL
"""
import hashlib
import json
import os
import random
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import scholarly_sources as SS
import scholarly_registry as SR

OUT = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_CORPUS_GATE.json")
SEED = 20260906

# 固定查询宇宙（分母; 含 O7-C canonical 6）——零结果不消失（§41）
QUERIES = [
    ("kant thing in itself two aspect interpretation", "C1"),
    ("kant transcendental deduction interpretation", "C2"),
    ("nietzsche eternal recurrence", "C3"),
    ("wittgenstein private language argument", "C4"),
    ("plato third man argument", "C5"),
    ("confucius ren li ritual", "C6"),
    ("aristotle function argument eudaimonia", "Q1"),
    ("augustine free will grace", "Q2"),
    ("anselm ontological argument", "Q3"),
    ("descartes cogito skepticism", "Q4"),
    ("spinoza substance monism", "Q5"),
    ("locke personal identity", "Q6"),
    ("hume causation induction", "Q7"),
    ("kant schematism", "Q8"),
    ("kant autonomy freedom", "Q9"),
    ("hegel recognition phenomenology of spirit", "Q10"),
    ("nietzsche genealogy of morals", "Q11"),
    ("wittgenstein rule following", "Q12"),
    ("heidegger dasein being and time", "Q13"),
    ("mencius human nature", "Q14"),
    # 2 negative（对照, 不入 relevance 均值分母）
    ("qqzzxv nonexistent philosopher theory blorptar", "N1"),
    ("kant unpublished manuscript 1789 never existed fragment xyzq", "N2"),
]
_key = None
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("ZHIPU_API_KEY="):
        _key = line.split("=", 1)[1].strip().strip('"').strip("'")

JUDGE_SYS = ("You are a bibliographic relevance assessor. Given a research query "
             "and a scholarly record (title, abstract if available, publication "
             "metadata), score TOPICAL_RELEVANCE 0-4: 0=unrelated, 1=vaguely "
             "connected, 2=same broad area, 3=directly on the topic, 4=centrally "
             "on the exact question. Output JSON only: "
             '{"TOPICAL_RELEVANCE": <int 0-4>, "reason": "<=40 words"}')


def call_judge(prompt):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 300,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": JUDGE_SYS},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""


def _load():
    if os.path.exists(OUT):
        try:
            return json.load(open(OUT, encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"phases": {}}


def _save(g):
    json.dump(g, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _run_mode(mode):
    """mode=L: provider 强制失败（网络禁用）; mode=C: 正常 live。"""
    orig_cr, orig_oa = SS.search_crossref, SS.search_openalex
    if mode == "L":
        def boom(*a, **k):
            raise SS.ProviderError("PROVIDER_UNAVAILABLE", "network disabled (gate)")
        SS.search_crossref = boom
        SS.search_openalex = boom
    SS._cache = {"searches": {}, "records": {}}
    results = []
    per_query = {}
    try:
        for q, qid in QUERIES:
            out = SS.search_scholarship(q, limit=5)
            scores = []
            for r in out["results"]:
                ab = (r.get("abstract") or {}).get("text") or ""
                prompt = (f"QUERY: {q}\nTITLE: {r.get('title')}\n"
                          f"YEAR: {r.get('publication_year')} | VENUE: {r.get('container_title')} "
                          f"| TYPE: {r.get('publication_type')}\nABSTRACT: {ab[:700]}")
                sc = None
                for attempt in range(3):
                    try:
                        sc = int(json.loads(call_judge(prompt)).get("TOPICAL_RELEVANCE", 0))
                        break
                    except Exception:
                        time.sleep(2 * (attempt + 1))
                scores.append(sc)
            per_query[qid] = scores
            results.append({"qid": qid, "query": q,
                            "titles": [r.get("title") for r in out["results"]],
                            "sids": [r["source_record_id"] for r in out["results"]],
                            "scores": scores})
            print(f"  {mode} {qid}: {len(out['results'])} recs", flush=True)
    finally:
        SS.search_crossref, SS.search_openalex = orig_cr, orig_oa
    # 固定宇宙分母（零结果不入样本消失）
    subst = {qid: per_query.get(qid, []) for q, qid in QUERIES if not qid.startswith("N")}
    neg = {qid: per_query.get(qid, []) for q, qid in QUERIES if qid.startswith("N")}
    valid = [s for ss in subst.values() for s in ss if s is not None]
    relevant = sum(1 for ss in subst.values()
                   if ss and max(s for s in ss if s is not None) >= 3)
    neg_fp = sum(1 for ss in neg.values()
                 if ss and max(s for s in ss if s is not None) >= 3)
    dup_top5 = 0
    for x in results:
        if len(set(x["sids"])) != len(x["sids"]):
            dup_top5 += 1
    return {"mode": mode, "judge": "glm-4.6",
            "query_universe": len(QUERIES),
            "SUBSTANTIVE_QUERY_COUNT": len(subst),
            "QUERIES_WITH_RELEVANT_RECORD": relevant,
            "QUERY_RELEVANCE_RATE": round(relevant / max(len(subst), 1), 3),
            "TOP5_RELEVANCE_MEAN": round(sum(valid) / max(len(valid), 1), 3),
            "NEGATIVE_QUERY_COUNT": len(neg),
            "NEGATIVE_QUERIES_WITH_FALSE_POSITIVE": neg_fp,
            "NEGATIVE_CONTROL_PASS": neg_fp == 0,
            "DUPLICATE_RECORDS_IN_TOP5": dup_top5,
            "detail": results}


def phase_l(g):
    g["phases"]["L"] = _run_mode("L")
    _save(g)


def phase_c(g):
    g["phases"]["C"] = _run_mode("C")
    _save(g)


def phase_r(g):
    reg = SR.load_registry()
    ids = list(reg)
    dois = [r["identifiers"]["doi"] for r in reg.values()
            if r["identifiers"].get("doi")]
    from collections import Counter
    c = Counter(r["cluster_ids_accepted"] and "accepted" or "discovery_only"
                for r in reg.values())
    g["phases"]["R"] = {
        "records": len(ids),
        "DUPLICATE_SOURCE_RECORD_ID": len(ids) - len(set(ids)),
        "DUPLICATE_VERIFIED_DOI": len(dois) - len(set(dois)),
        "SILENT_BIBLIOGRAPHIC_CONFLICT": sum(
            1 for r in reg.values()
            if any(c0.get("resolution_status") == "RESOLVED" and not c0.get("resolution_basis")
                   for c0 in r.get("conflicts", []))),
        "accepted": c.get("accepted", 0), "discovery_only": c.get("discovery_only", 0),
    }
    _save(g)


def phase_d(g):
    reg = SR.load_registry()
    dois = sorted({r["identifiers"]["doi"] for r in reg.values()
                   if r["identifiers"].get("doi")})
    set_hash = hashlib.sha256("\n".join(dois).encode()).hexdigest()
    prev = g["phases"].get("D")
    if prev and prev.get("doi_set_hash") == set_hash and prev.get("INVALID_VERIFIED_DOI") == []:
        g["phases"]["D"] = dict(prev, doi_set_unchanged=True)   # 确定性复用
        _save(g)
        return
    invalid = []
    for i, d in enumerate(dois):
        try:
            req = urllib.request.Request(f"https://doi.org/api/handles/{d}")
            with urllib.request.urlopen(req, timeout=15) as r:
                if json.loads(r.read()).get("responseCode") != 1:
                    invalid.append(d)
        except Exception:
            invalid.append(d)
        if (i + 1) % 60 == 0:
            print(f"  doi {i+1}/{len(dois)}", flush=True)
    g["phases"]["D"] = {"doi_checked": len(dois), "doi_set_hash": set_hash,
                        "INVALID_VERIFIED_DOI": invalid}
    _save(g)


def phase_b(g):
    reg = SR.load_registry()
    rng = random.Random(SEED)
    sample = sorted(rng.sample(sorted(reg), min(50, len(reg))))
    def _norm_authors(a):
        return sorted(((" ".join(str(x.get("name", "")).lower().split()),
                        str(x.get("orcid") or "").lower())
                       for x in (a or [])))

    wrong = []
    checked = 0
    for sid in sample:
        r = reg[sid]
        for field in ("title", "authors", "publication_year", "container_title", "doi"):
            cv = r.get(field) if field != "doi" else r["identifiers"].get("doi")
            if field == "authors":
                checked += 1
                pvs = [_norm_authors(p.get("authors")) for p in r["provider_records"]
                       if p.get("authors")]
                if cv and pvs and _norm_authors(cv) not in pvs:
                    wrong.append(f"{sid}.{field}")
                continue
            pvs = [p.get(field) for p in r["provider_records"]
                   if p.get(field) not in (None, "", [])]
            checked += 1
            if cv is None:
                continue
            if field == "doi":
                pvs = [SS.normalize_doi(v) for v in pvs]
            if cv not in pvs:
                wrong.append(f"{sid}.{field}")
    g["phases"]["B"] = {"sample": len(sample), "fields_checked": checked,
                        "fields_per_record": 5,
                        "BIBLIOGRAPHIC_WRONG_FIELDS": wrong}
    _save(g)


def phase_e(g):
    ev = SR._load_jsonl(os.path.join(SR.REG_DIR, "evidence.jsonl"))
    reg = SR.load_registry()
    orphan = fake_loc = 0
    for e in ev:
        if e["source_record_id"] not in reg:
            orphan += 1
        if e["evidence_type"] == "FULLTEXT_PASSAGE":
            if not e.get("content_hash") or e.get("access_level_at_ingest") != "FULL_TEXT_READ":
                orphan += 1
            if e.get("page") is not None or e.get("locator") is not None:
                fake_loc += 1
    g["phases"]["E"] = {"evidence_items": len(ev),
                        "ORPHAN_EVIDENCE": orphan,
                        "FAKE_PASSAGE_LOCATORS": fake_loc,
                        "abstract_evidence": sum(1 for e in ev if e["evidence_type"] == "ABSTRACT"),
                        "passage_evidence": sum(1 for e in ev if e["evidence_type"] == "FULLTEXT_PASSAGE")}
    _save(g)


PHASES = {"L": phase_l, "C": phase_c, "R": phase_r, "D": phase_d,
          "B": phase_b, "E": phase_e}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    g = _load()
    for name, fn in PHASES.items():
        if which in (name, "ALL"):
            print(f"== Phase {name}", flush=True)
            fn(g)
    for k in ("R", "D", "B", "E"):
        if k in g["phases"]:
            print(k, json.dumps(g["phases"][k], ensure_ascii=False)[:300])
