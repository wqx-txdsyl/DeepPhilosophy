# -*- coding: utf-8 -*-
"""O7-D §3-7/§17-19/§28/§36: Registry builder——从 frozen discovery snapshot +
curation decisions 确定性构建 registry/evidence（DISCOVERY RUN 与 REGISTRY BUILD 分离）。

输出:
  backend/data/scholarly/registry.jsonl    canonical source records（O7-C identity 复用）
  backend/data/scholarly/evidence.jsonl    ABSTRACT / FULLTEXT_PASSAGE 证据
  backend/data/scholarly/corpus_manifest.json
重复构建 byte-identical（时间戳取 snapshot.ran_at, 排序固定）。

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/dp_o7d_registry.py [--fetch-passages]
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

MANIFEST = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_COVERAGE_MANIFEST.json")
SNAP = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_DISCOVERY_SNAPSHOT.json")
CUR = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_CURATION_DECISIONS.json")
REG_DIR = os.path.join(ROOT, "backend", "data", "scholarly")

FULLTEXT_ATTEMPT_N = 12      # 全文证据抓取尝试数（accepted DIRECT_PDF 优先）
PASSAGE_MAX_CHARS = 1200
PASSAGE_MAX_N = 5


def build(fetch_passages=False):
    m = json.load(open(MANIFEST, encoding="utf-8"))
    snap = json.load(open(SNAP, encoding="utf-8"))
    cur = json.load(open(CUR, encoding="utf-8"))["decisions"]
    ran_at = snap["ran_at"]

    rel = {}
    for d in cur:
        if d["TOPICAL_RELEVANCE"] is not None:
            rel[(d["cluster_id"], d["source_record_id"])] = d["TOPICAL_RELEVANCE"]

    # cluster membership
    cluster_of = {}          # sid -> {cid: relevance}
    for cid, cl in snap["clusters"].items():
        for r in cl["candidates"]:
            cluster_of.setdefault(r["source_record_id"], {})[cid] = \
                rel.get((cid, r["source_record_id"]))
    book_ids_of = {}
    for c in m["clusters"]:
        if c.get("related_primary_book_ids"):
            for sid in cluster_of:
                if c["cluster_id"] in cluster_of[sid]:
                    book_ids_of.setdefault(sid, []).extend(c["related_primary_book_ids"])

    records = {}
    for cid, cl in snap["clusters"].items():
        for r in cl["candidates"]:
            sid = r["source_record_id"]
            if sid in records:
                continue
            r = json.loads(json.dumps(r))     # deep copy
            acc = sorted(c for c, v in cluster_of[sid].items() if (v or 0) >= 3)
            disc = sorted(c for c, v in cluster_of[sid].items()
                          if v is not None and (v or 0) < 3)
            level = r["access"]["level"]
            r.update({
                "cluster_ids_accepted": acc,
                "cluster_ids_discovery_only": disc,
                "related_primary_book_ids": sorted(set(book_ids_of.get(sid, []))),
                "association_status": "CURATED",
                "ingest": {"discovery_snapshot_hash": snap["discovery_snapshot_hash"],
                           "access_level_at_ingest": level,
                           "checked_at": ran_at},
                "reuse_status": ("METADATA_ONLY" if level == "METADATA_ONLY"
                                 else "UNKNOWN"),
                "license": None, "license_source": None, "license_verified": False,
            })
            records[sid] = r

    evidence = []
    for sid, r in sorted(records.items()):
        ab = r.get("abstract") or {}
        if ab.get("text"):
            evidence.append({
                "source_record_id": sid,
                "evidence_id": "ev-" + hashlib.sha256(
                    (sid + "|ABSTRACT").encode()).hexdigest()[:16],
                "evidence_type": "ABSTRACT",
                "text": ab["text"][:PASSAGE_MAX_CHARS * 3],
                "abstract_source": ab.get("source"),
                "abstract_hash": ab.get("hash"),
                "access_level_at_ingest": "ABSTRACT_AVAILABLE",
                "extracted_at": ran_at,
                "evidence_origin": "ABSTRACT_METADATA",
            })

    fetched = []
    if fetch_passages:
        import scholarly_sources as SS
        n = 0
        for sid, r in sorted(records.items()):
            if n >= FULLTEXT_ATTEMPT_N:
                break
            if not r["cluster_ids_accepted"]:
                continue
            kinds = [c.get("candidate_kind") for c in (r.get("full_text_candidates") or [])]
            if "DIRECT_PDF" not in kinds:
                continue
            n += 1
            rec, info = SS.get_evidence(json.loads(json.dumps(r)),
                                        "FULL_TEXT_IF_LEGALLY_AVAILABLE")
            if info.get("access_level_after") != "FULL_TEXT_READ":
                continue
            fetched.append(sid)
            for p in (info.get("evidence_passages") or [])[:PASSAGE_MAX_N]:
                evidence.append({
                    "source_record_id": sid,
                    "evidence_id": "ev-" + hashlib.sha256(
                        (sid + "|PASSAGE|" + p["passage_id"]).encode()).hexdigest()[:16],
                    "evidence_type": "FULLTEXT_PASSAGE",
                    "text": p["text"][:PASSAGE_MAX_CHARS],
                    "locator": None, "page": None,
                    "source_url": rec["access"].get("full_text_url"),
                    "content_hash": rec["access"].get("content_hash"),
                    "access_level_at_ingest": "FULL_TEXT_READ",
                    "verified_document_kind": "PDF",
                    "parser": "pdftotext",
                    "extracted_at": ran_at,
                    "evidence_origin": "PERSISTED_VERIFIED_READ",
                })
            # registry 的历史 access 记录
            records[sid]["ingest"]["access_level_at_ingest"] = "FULL_TEXT_READ"
            records[sid]["ingest"]["fulltext_read"] = {
                "content_hash": rec["access"].get("content_hash"),
                "checked_at": ran_at, "reuse_status": "ACCESSIBLE_BUT_REUSE_UNVERIFIED"}
            # 不持久正文 body——只留 passages/hash（§6/§18）

    os.makedirs(REG_DIR, exist_ok=True)
    with open(os.path.join(REG_DIR, "registry.jsonl"), "w", encoding="utf-8") as f:
        for sid in sorted(records):
            f.write(json.dumps(records[sid], ensure_ascii=False, sort_keys=True) + "\n")
    with open(os.path.join(REG_DIR, "evidence.jsonl"), "w", encoding="utf-8") as f:
        for e in evidence:
            f.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")

    acc_total = sum(1 for r in records.values() if r["cluster_ids_accepted"])
    cm = {
        "version": "o7d-1",
        "discovery_snapshot_hash": snap["discovery_snapshot_hash"],
        "manifest_version": m["version"],
        "records": len(records),
        "records_with_accepted_cluster": acc_total,
        "records_discovery_only": len(records) - acc_total,
        "evidence_abstract": sum(1 for e in evidence if e["evidence_type"] == "ABSTRACT"),
        "evidence_passages": sum(1 for e in evidence if e["evidence_type"] == "FULLTEXT_PASSAGE"),
        "fulltext_read_records": len(fetched),
        "registry_sha256": hashlib.sha256(
            open(os.path.join(REG_DIR, "registry.jsonl"), "rb").read()).hexdigest(),
        "evidence_sha256": hashlib.sha256(
            open(os.path.join(REG_DIR, "evidence.jsonl"), "rb").read()).hexdigest(),
    }
    json.dump(cm, open(os.path.join(REG_DIR, "corpus_manifest.json"), "w",
                       encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(cm, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    build(fetch_passages="--fetch-passages" in sys.argv)
