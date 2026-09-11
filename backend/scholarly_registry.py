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
                "source_record_id UNINDEXED, cluster_ids_accepted, title, authors, "
                "aliases, abstract, passages, book_ids, container, cluster_topics)")
    indexed = 0
    for sid, r in _registry.items():
        # RP1 §2: 默认索引只含 accepted records（curation 约束 runtime 暴露）
        if not r.get("cluster_ids_accepted"):
            continue
        ev = _evidence.get(sid, [])
        con.execute(
            "INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?)",
            (sid,
             " ".join(r.get("cluster_ids_accepted") or []),
             r.get("title") or "",
             " ".join(a.get("name", "") for a in (r.get("authors") or [])),
             " ".join(r.get("aliases") or []),   # PF-RP5/V3-RP3: 多语别名可检索
             next((e["text"] for e in ev if e["evidence_type"] == "ABSTRACT"), ""),
             " ".join(e["text"] for e in ev if e["evidence_type"] == "FULLTEXT_PASSAGE"),
             " ".join(r.get("related_primary_book_ids") or []),
             # V6-F2 §4: 书名/期刊名是标准书目检索面——章节记录的判别词
             # （如 Tillman 专著名 Utilitarian Confucianism）常只存在于 container
             r.get("container_title") or "",
             # V6-F2 §4: curated 簇 topic 是记录的主题判别词所在（通用语料元数据）
             " ".join(r.get("cluster_topics") or [])))
        indexed += 1
    con.commit()
    con.close()
    return indexed


def _record_haystack(rec):
    """V5-F2 §B: 参与覆盖率判定的记录文本（title + authors + abstract + container）。"""
    parts = [str(rec.get("title") or "")]
    parts += [str(a.get("name") or "") for a in (rec.get("authors") or [])
              if isinstance(a, dict)]
    ab = rec.get("abstract")
    if isinstance(ab, dict):
        parts.append(str(ab.get("text") or ""))
    # V6-F2 §4: 书名/期刊名纳入覆盖判定（章节记录的判别词常只在 container）
    parts.append(str(rec.get("container_title") or ""))
    parts.append(" ".join(rec.get("cluster_topics") or []))
    # V6-F2 §4: 撇号归一（"Ch'en Liang" vs "Chen Liang"——FTS/子串两侧统一）
    return " ".join(parts).lower().replace("'", "").replace("’", "")


def search_local(query, limit=8):
    """本地 FTS5 检索（BM25）→ canonical record 视图（复用 O7-C identity）。

    V5-F2 §B: FTS OR 只做召回, 结果按通用相关性重排——多词覆盖率优先
    （≤3 词要求全词命中, >3 词要求 ≥60%）, bm25 仅作 tie-break。
    纯 OR/BM25 的单词碰撞（如 "moral luck" 命中任何含 moral 的记录）会把
    离题记录顶进 top-k, 使 LOCATE 结果失去文献判断价值。覆盖率排序无任何
    主题/查词特判; 全零覆盖时兜底退回 OR 排序, 不因收紧而静默空手。"""
    load_registry()
    if not os.path.exists(INDEX):
        build_index()
    # OR 语义做召回池（放大池深, 重排在池内做）; 引号短语原样保留（簇 tag 精确命中）
    if '"' in query:
        match = query
    else:
        # V3-RP3: 连字符归一（FTS5 分词把 "Neo-Confucianism" 拆成 neo+confucianism,
        # 查询串里的 "-" 会造成静默零命中）
        q_norm = query.replace("-", " ")
        terms = [t for t in q_norm.split() if len(t) >= 2]
        match = " OR ".join(terms) or query
    con = sqlite3.connect(INDEX)
    rows = con.execute(
        "SELECT source_record_id, bm25(sources) FROM sources WHERE sources MATCH ? "
        "ORDER BY bm25(sources) LIMIT ?", (match, max(limit * 8, 40))).fetchall()
    con.close()
    # retrieval_origin 标注: 记录取自本地 curated registry（区别于书目来源 provider）
    cand = [dict(_registry[s], _bm25=round(b, 2), retrieval_origin="LOCAL_CURATED")
            for s, b in rows
            if s in _registry and _registry[s].get("cluster_ids_accepted")]
    tl = [t.lower().replace("'", "").replace("’", "")
          for t in (query.replace("-", " ").split()) if len(t) >= 2]
    if not tl or '"' in query:
        return cand[:limit]
    for c in cand:
        text = _record_haystack(c)
        c["_term_coverage"] = round(sum(1 for t in tl if t in text) / len(tl), 2)
    need = 1.0 if len(tl) <= 2 else 0.6
    strict = [c for c in cand if c["_term_coverage"] + 1e-9 >= need]
    (strict or cand).sort(key=lambda c: (-c["_term_coverage"], c["_bm25"]))
    return (strict or cand)[:limit]


def stats():
    reg = load_registry()
    from collections import Counter
    levels = Counter(r["access"]["level"] for r in reg.values())
    return {"records": len(reg),
            "by_access_level": dict(levels),
            "evidence_records": sum(1 for _ in _evidence),
            "evidence_items": sum(len(v) for v in _evidence.values())}
