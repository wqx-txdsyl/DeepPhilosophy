# -*- coding: utf-8 -*-
"""O7-D — Scholarly Source Registry 运行时（scholarly_registry.py）。

Curated/Versioned/Reproducible 的二手文献语料层（≠ runtime cache §4）:
  backend/data/scholarly/registry.jsonl   canonical source records（O7-C identity 复用）
  backend/data/scholarly/evidence.jsonl   持久证据（ABSTRACT / FULLTEXT_PASSAGE）
  backend/data/scholarly/index.sqlite     FTS5 本地索引（title/authors/abstract/passages）

原则:
  - LOCAL_CURATED 是 provider, 不是 authority——每条结果保留原始
    Crossref/OpenAlex provenance（§24）
  - 无自动刷新（§49）; 历史 access 状态与当前分离（§36）
  - evidence passages ≤1200 字 / 每篇 ≤5 段（§19）; 不持久整篇正文（§6）
"""
import hashlib
import json
import os
import sqlite3
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG_DIR = os.path.join(ROOT, "backend", "data", "scholarly")
REGISTRY = os.path.join(REG_DIR, "registry.jsonl")
EVIDENCE = os.path.join(REG_DIR, "evidence.jsonl")
INDEX = os.path.join(REG_DIR, "index.sqlite")

_lock = threading.Lock()
_registry = None      # {source_record_id: record}
_evidence = None      # {source_record_id: [evidence...]}


def _load_jsonl(path):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_registry():
    global _registry, _evidence
    with _lock:
        if _registry is None:
            _registry = {r["source_record_id"]: r for r in _load_jsonl(REGISTRY)}
            _evidence = {}
            for e in _load_jsonl(EVIDENCE):
                _evidence.setdefault(e["source_record_id"], []).append(e)
    return _registry


def record(sid):
    return load_registry().get(sid)


def evidence_for(sid):
    load_registry()
    return _evidence.get(sid, [])


# ── FTS5 索引（简单透明, 不造 embedding stack §21）────────────────
def build_index():
    load_registry()
    os.makedirs(REG_DIR, exist_ok=True)
    if os.path.exists(INDEX):
        os.unlink(INDEX)
    con = sqlite3.connect(INDEX)
    con.execute("CREATE VIRTUAL TABLE sources USING fts5("
                "source_record_id UNINDEXED, cluster_ids, title, authors, "
                "abstract, passages, book_ids)")
    for sid, r in _registry.items():
        ev = _evidence.get(sid, [])
        con.execute(
            "INSERT INTO sources VALUES (?,?,?,?,?,?,?)",
            (sid,
             " ".join(r.get("cluster_ids") or []),
             r.get("title") or "",
             " ".join(a.get("name", "") for a in (r.get("authors") or [])),
             next((e["text"] for e in ev if e["evidence_type"] == "ABSTRACT"), ""),
             " ".join(e["text"] for e in ev if e["evidence_type"] == "FULLTEXT_PASSAGE"),
             " ".join(r.get("related_primary_book_ids") or [])))
    con.commit()
    con.close()


def search_local(query, limit=8):
    """本地 FTS5 检索（BM25）→ canonical record 视图（复用 O7-C identity）。"""
    load_registry()
    if not os.path.exists(INDEX):
        build_index()
    con = sqlite3.connect(INDEX)
    rows = con.execute(
        "SELECT source_record_id, bm25(sources) FROM sources WHERE sources MATCH ? "
        "ORDER BY bm25(sources) LIMIT ?", (query, limit)).fetchall()
    con.close()
    return [dict(_registry[sid], _bm25=round(b, 2)) for s, b in rows
            if s in _registry]


def stats():
    reg = load_registry()
    from collections import Counter
    levels = Counter(r["access"]["level"] for r in reg.values())
    return {"records": len(reg),
            "by_access_level": dict(levels),
            "evidence_records": sum(1 for _ in _evidence),
            "evidence_items": sum(len(v) for v in _evidence.values())}
