# -*- coding: utf-8 -*-
"""O8-R2 §7: Retrieval / Corpus Census（evaluation-only, 只读）。

LOCAL_CURATED: record_count/unique_sources/authors/years/languages/
DOI coverage/URL coverage/abstract coverage/duplicates。
Primary Text: catalog_count/works_with_real_text/works_without_verifiable_text/
chapter coverage（以 clean reviewed checkout 为唯一真源）。
72-case 命中类指标由报告组装阶段从 o8r2_bench.json 回填。
产出 backend/tools/_tmp/o8r2_census.json。
"""
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

SCH = os.path.join(ROOT, "backend/data/scholarly")
BOOKS = os.path.join(ROOT, "app/public/books.json")
CHAPTERS = os.path.join(ROOT, "backend/data/book_chapters")


def census_local_curated():
    recs = [json.loads(l) for l in open(os.path.join(SCH, "registry.jsonl"),
                                        encoding="utf-8") if l.strip()]
    ev = [json.loads(l) for l in open(os.path.join(SCH, "evidence.jsonl"),
                                      encoding="utf-8") if l.strip()]
    n = len(recs)
    dois = [r.get("_doi") for r in recs if r.get("_doi")]
    dois_clean = [d for d in dois if isinstance(d, str) and d.strip()]
    dup_dois = {d: c for d, c in Counter(dois_clean).items() if c > 1}
    titles, authors, years, langs, urls = [], [], [], [], []
    accepted_cluster = 0
    for r in recs:
        titles.append(r.get("title") or "")
        for a in (r.get("authors") or []):
            authors.append(a.get("family") or a.get("name") if isinstance(a, dict) else str(a))
        y = r.get("publication_year")
        if y:
            years.append(str(y)[:4])
        lang = r.get("language")
        if lang:
            langs.append(str(lang)[:8])
        for u in (r.get("stable_urls") or []):
            if isinstance(u, str) and u:
                urls.append(u)
            elif isinstance(u, dict) and (u.get("url") or u.get("stable_url")):
                urls.append(u.get("url") or u.get("stable_url"))
        if r.get("cluster_ids_accepted"):
            accepted_cluster += 1
    has_abstract = sum(1 for r in recs if (r.get("abstract") or {}).get("text"))
    readable = sum(1 for r in recs
                   if len(((((r.get("abstract") or {}).get("text")) or ""))) >= 400)
    return {
        "record_count": n,
        "records_with_accepted_cluster": accepted_cluster,
        "unique_titles": len(set(t.strip().lower() for t in titles if t)),
        "unique_authors": len(set(a for a in authors if a)),
        "author_sample": sorted(set(a for a in authors if a))[:25],
        "year_range": [min(years), max(years)] if years else None,
        "year_distribution_bucket": dict(Counter(
            (y[:3] + "0s") for y in years if y.isdigit())),
        "languages": dict(Counter(langs)),
        "doi_coverage": {"with_doi": len(dois_clean), "rate": round(len(dois_clean) / max(n, 1), 3)},
        "url_coverage": {"with_url": len(set(urls)), "rate": round(len(set(urls)) / max(n, 1), 3)},
        "abstract_coverage": {"with_abstract_field": has_abstract,
                              "with_long_abstract(>=400ch)": readable,
                              "rate": round(readable / max(n, 1), 3)},
        "evidence_records": len(ev),
        "duplicates": {"duplicate_doi_count": len(dup_dois),
                       "dup_examples": dict(list(dup_dois.items())[:10])},
        "registry_sha256_note": "corpus_manifest.json 冻结哈希为准",
    }


def census_primary_text():
    books = json.load(open(BOOKS, encoding="utf-8"))
    catalog = {}
    for b in books:
        catalog[b["id"]] = {"title": b.get("title"), "author": b.get("author"),
                            "chapterCount": b.get("chapterCount"),
                            "file_type": b.get("file_type")}
    # 章节真源: backend/data/book_chapters/{bid}/{idx}.json（git 跟踪 12768 文件）
    real_chapters, mismatched, content_ok = {}, {}, 0
    for bid in sorted(os.listdir(CHAPTERS)) if os.path.isdir(CHAPTERS) else []:
        d = os.path.join(CHAPTERS, bid)
        if not os.path.isdir(d):
            continue
        chs = [f for f in os.listdir(d) if f.endswith(".json")]
        real_chapters[bid] = len(chs)
        # 内容可验证抽样: 首章非空即算 readable content（全量逐字验证太重, 结构验证全量）
        try:
            sample = json.load(open(os.path.join(d, sorted(chs)[0]), encoding="utf-8"))
            if isinstance(sample, dict) and (sample.get("content") or sample.get("text")):
                content_ok += 1
        except Exception:
            pass
    with_text, without = [], []
    for bid, meta in catalog.items():
        cnt = real_chapters.get(bid, 0)
        if cnt > 0:
            with_text.append(bid)
            if meta["chapterCount"] and abs(cnt - meta["chapterCount"]) > 0:
                mismatched[bid] = {"title": meta["title"],
                                   "catalog": meta["chapterCount"], "files": cnt}
        else:
            without.append({"id": bid, "title": meta["title"],
                            "catalog_chapterCount": meta["chapterCount"],
                            "files_found": 0})
    total_catalog_chapters = sum((m["chapterCount"] or 0) for m in catalog.values())
    total_real_chapters = sum(real_chapters.values())
    return {
        "catalog_count": len(catalog),
        "book_universe_manifest_claim": "docs/evidence/PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json 记录 409（tracked 版本）; 主工作树未提交 diff 记录 410",
        "CANONICAL_COUNT": len(catalog),
        "MISMATCH": "catalog(books.json)=410 vs tracked O7B manifest=409 → MISMATCH=1（只报告不修数据）",
        "SOURCE_OF_TRUTH": "app/public/books.json @ clean reviewed checkout（章节真源 backend/data/book_chapters/ git 跟踪目录树 {bid}/{idx}.json）",
        "works_with_real_text": len(with_text),
        "works_without_verifiable_text": len(without),
        "works_with_readable_content_sampled": content_ok,
        "without_examples": without[:15],
        "without_file_types": dict(Counter(m["file_type"] or "?" for bid, m in catalog.items()
                                           if bid in {w["id"] for w in without})),
        "chapter_files_dirs": len(real_chapters),
        "total_catalog_chapters": total_catalog_chapters,
        "total_real_chapters": total_real_chapters,
        "chapter_coverage_rate": round(total_real_chapters / max(total_catalog_chapters, 1), 3),
        "catalog_vs_files_mismatched_books": len(mismatched),
        "mismatch_examples": dict(list(mismatched.items())[:10]),
    }


if __name__ == "__main__":
    out = {"LOCAL_CURATED": census_local_curated(),
           "PRIMARY_TEXT": census_primary_text(),
           "O8R2_CASE_HITS": "PENDING（报告组装阶段从 o8r2_bench.json 回填）"}
    dst = os.path.join(ROOT, "backend/tools/_tmp/o8r2_census.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:3000])
