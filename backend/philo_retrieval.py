# -*- coding: utf-8 -*-
"""Nietzsche 语料混合检索（Phase R2/R3, 2026-08-30）

目标: philosopher_corpus 不再以"全量 term-count 扫描 453MB 语料"为主路径, 让 AIAuthor
既有 vector 数据真正参与检索。检索失败绝不拖垮 Agent（分层降级）。

数据源（backend/tools/dp_build_nietzsche_index.py 一次性拆出的运行时 artifact,
源文件 corpus/chunks/all_chunks.json 只读不动, 不删不迁数据）:
  nietzsche_vectors.npy   float32 [N,1024] 已 L2 归一（余弦 = 点积）
  nietzsche_meta.json     行元数据 [book, chapter, tier, format, source, period, year, chars, off, len]
  nietzsche_chunks.jsonl  行文本（字节偏移 seek, 支持按 chunk 行号随机取原文）

检索管线（本模块职责边界: 不改 LangGraph 拓扑/工具注册表/Persona/Memory 语义）:
  query → embedding（复用 routes.agent_core._embed_query——Phase S 的 429 熔断/缓存/降级语义原样）
        → dense top-N（全语料余弦召回, 精确 chunk 行号）
        + lexical BM25（dense 候选上重排; 降级时全语料 BM25 兜底）
        → RRF 候选合并 → 轻量 rerank（短语命中 + tier 权威加权, primary-source-first）
        → top-k echoes（book/chapter/tier/period/source_type 元数据完整, 供 Evidence Contract）

R3 语料访问策略:
  - 健康路径: 只 seek 读取 dense 候选（~32 条）的原文做词法重排——不为单个问题整载语料
  - 降级路径（embedding 429/不可用）: 全语料 BM25 → 一次性加载 13.9MB 紧凑文本域并常驻复用
    （等价旧词法基线的召回面, 但内存 453MB → ~14MB）
  - chunk_text(row)/fetch_chunks(rows) 提供按 chunk 行号的精确随机访问

降级链:
  ① embedding 429/不可用 → 纯 lexical（Phase S 降级语义, _embed_query 熔断器复用）
  ② 索引 artifact 缺失/损坏 → retrieve 返回 None, agents.philosopher_corpus 走旧 bundle 全量路径兜底
  ③ 本模块任何异常 → 返回 {"echoes": [], "mode": "error"}, 不抛出
"""
import json
import math
import re
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent                  # backend/
AI_DIR = BASE.parent / "data" / "ai_author"
VEC_FILE = AI_DIR / "vector" / "nietzsche_vectors.npy"
META_FILE = AI_DIR / "vector" / "nietzsche_meta.json"
JSONL_FILE = AI_DIR / "vector" / "nietzsche_chunks.jsonl"
TIERS_FILE = AI_DIR / "corpus" / "corpus_tiers.json"    # 权威 tier 定义（S/A/B/C authority）

# dense 召回候选数与相似度下限（chunk 级 embedding 相似度波动大, 下限放低由 rerank 兜底）
_DENSE_CANDIDATES = 32
_DENSE_MIN_SIM = 0.30
# lexical BM25 参数（标准值）
_BM25_K1 = 1.5
_BM25_B = 0.75
_RRF_K = 60                    # Reciprocal Rank Fusion 常数
_PHRASE_BONUS = 0.08           # 完整查询串命中正文的 rerank 加成
_TIER_BONUS = {"S": 0.05, "A": 0.03, "B": 0.015, "C": 0.0}   # primary-source-first 权重
# 词法查询词上限（长 query 防御）
_MAX_TERMS = 8

# ── 运行时状态（进程级, 懒加载一次后常驻复用; 均为语料尺寸的有界缓存, 非无界）──
_STATE = {
    "meta": None,          # meta.json 内容
    "vectors": None,       # np.ndarray [N, dim]
    "texts": None,         # row -> text（13.9MB, 仅降级全语料词法需要时加载, 加载后常驻）
    "doc_len": None,       # row -> 字符数（BM25 长度归一）
    "tiers": None,         # tier -> authority（corpus_tiers.json, 缺失用兜底表）
}
_STATE_LOCK = threading.RLock()
_JSONL_LOCK = threading.Lock()   # jsonl seek+read 串行化（共享句柄定位安全）

_ECHO_TEXT_LEN = 220             # echoes 正文截断（与旧 philosopher_corpus 输出一致）


def artifacts_available():
    """索引 artifact 是否就绪（缺失 → 调用方走旧 bundle 兜底）"""
    return VEC_FILE.exists() and META_FILE.exists() and JSONL_FILE.exists()


def _ensure_index():
    """懒加载 meta + vectors（~29MB, 双检锁; 进程内一次）"""
    if _STATE["meta"] is not None:
        return
    with _STATE_LOCK:
        if _STATE["meta"] is not None:
            return
        meta = json.load(open(META_FILE, encoding="utf-8"))
        import numpy as np
        vecs = np.load(VEC_FILE)
        if vecs.shape[0] != meta.get("count"):
            raise RuntimeError(f"vector/meta 行数不一致: {vecs.shape[0]} != {meta.get('count')}")
        _STATE["meta"] = meta
        _STATE["vectors"] = vecs


def _ensure_tiers():
    """tier 权威表（corpus_tiers.json 缺失/损坏 → 内置兜底, 数值与 corpus_tiers.json 一致）"""
    if _STATE["tiers"] is not None:
        return _STATE["tiers"]
    tiers = {"S": 1.0, "A": 0.8, "B": 0.6, "C": 0.45}
    try:
        raw = json.load(open(TIERS_FILE, encoding="utf-8"))
        for t, d in (raw.get("tiers") or {}).items():
            if isinstance(d, dict) and isinstance(d.get("authority"), (int, float)):
                tiers[t] = float(d["authority"])
    except Exception:
        pass
    _STATE["tiers"] = tiers
    return tiers


def _ensure_texts():
    """懒加载全语料文本 + 文档长度（13.9MB, 双检锁; 仅全语料词法路径需要, 加载后常驻复用）"""
    if _STATE["texts"] is not None:
        return
    with _STATE_LOCK:
        if _STATE["texts"] is not None:
            return
        texts, doc_len = {}, {}
        with open(JSONL_FILE, encoding="utf-8") as f:
            for row, line in enumerate(f):
                line = line.strip()
                if not line:
                    texts[row] = ""
                    doc_len[row] = 0
                    continue
                try:
                    texts[row] = json.loads(line).get("text") or ""
                except Exception:
                    texts[row] = ""
                doc_len[row] = len(texts[row])
        _STATE["texts"] = texts
        _STATE["doc_len"] = doc_len


def chunk_text(row):
    """按行号 seek 读取单个 chunk 原文（R3: 精确取文, 不整载语料）"""
    with _STATE_LOCK:
        meta = _STATE["meta"]
        if meta is None:
            _ensure_index()
            meta = _STATE["meta"]
    rows = meta.get("rows") or []
    if not isinstance(row, int) or row < 0 or row >= len(rows):
        return ""
    off, length = rows[row][8], rows[row][9]
    with _JSONL_LOCK:
        with open(JSONL_FILE, "rb") as f:
            f.seek(off)
            raw = f.read(length)
    try:
        return json.loads(raw.decode("utf-8")).get("text") or ""
    except Exception:
        return ""


def fetch_chunks(rows):
    """按 chunk 行号批量取原文（R3 对外 API; 顺序保持）"""
    return [chunk_text(r) for r in rows]


def _tokenize(query):
    """词法查询词: 标点/空白切分, 保留 ≥2 字词（短词与旧 philosopher_corpus 分词语义一致）。
    长 term（≥6 字, 常为整句）追加 2 字滑窗 bigram——原文精确子串命中率随句长骤降,
    bigram + BM25 idf 自动降权常用字组, 恢复整句/意译查询的词法召回。"""
    raw = [t for t in re.split(r"[\s,，。；;：:、！!？?·（）()\[\]【】\"'“”]+", query or "")
           if len(t) >= 2]
    seen, out = set(), []

    def _add(t):
        if t and t not in seen:
            seen.add(t)
            out.append(t)

    for t in raw[:_MAX_TERMS]:
        _add(t)
        if len(t) >= 6:
            for i in range(len(t) - 1):
                _add(t[i:i + 2])
    return out[:24]


def _dense_recall(query_vec, n):
    """全语料余弦召回 → [(row, sim)] 降序"""
    import numpy as np
    vecs = _STATE["vectors"]
    v = np.asarray(query_vec, dtype="float32")
    norm = float(np.linalg.norm(v))
    if norm <= 0:
        return []
    v = v / norm
    sims = vecs @ v
    n = min(n, sims.shape[0])
    top = np.argsort(-sims)[:n]
    return [(int(i), float(sims[i])) for i in top if sims[i] >= _DENSE_MIN_SIM]


def _bm25(tf, doc_len, df, n_total, avgdl):
    """BM25 得分: {row: score}（tf: row -> {term: count}, df: term -> 全库文档频率）"""
    out = {}
    for r, tfs in tf.items():
        if not tfs:
            continue
        dl = doc_len.get(r) or 1
        score = 0.0
        for term, c in tfs.items():
            idf = math.log(1.0 + (n_total - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (c * (_BM25_K1 + 1)) / (c + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl))
        out[r] = score
    return out


def _lexical_over_texts(terms, texts, doc_len=None):
    """在给定 {row: text} 候选子集上算 BM25（df 为候选集内文档频率——idf 只影响
    候选间相对排序, 排序可用性优先; 全库 df 见 _lexical_scores_full）"""
    if not texts or not terms:
        return {}
    rows = [r for r in texts if texts.get(r)]
    tf = {}
    for r in rows:
        t = texts[r]
        d = {}
        for term in terms:
            c = t.count(term)
            if c > 0:
                d[term] = c
        if d:
            tf[r] = d
    if not tf:
        return {}
    n_cand = len(rows)
    avgdl = sum((doc_len.get(r) if doc_len else len(texts[r])) or 1 for r in rows) / n_cand
    df = {term: 0 for term in terms}
    for d in tf.values():
        for term in d:
            df[term] += 1
    dl_map = {r: ((doc_len.get(r) if doc_len else len(texts[r])) or 1) for r in rows}
    return _bm25(tf, dl_map, df, n_cand, avgdl)


def _lexical_scores_full(terms):
    """全语料 BM25（df 全库统计; 一次扫描内同时算 tf 与 df, 无需倒排索引）"""
    _ensure_texts()
    texts, doc_len = _STATE["texts"], _STATE["doc_len"]
    if not texts or not terms:
        return {}
    tf = {}
    for r, t in texts.items():
        if not t:
            continue
        d = {}
        for term in terms:
            c = t.count(term)
            if c > 0:
                d[term] = c
        if d:
            tf[r] = d
    if not tf:
        return {}
    n_total = len(texts)
    avgdl = (sum(doc_len.values()) / n_total) if n_total else 1.0
    df = {term: 0 for term in terms}
    for d in tf.values():
        for term in d:
            df[term] += 1
    return _bm25(tf, doc_len, df, n_total, avgdl)


def _rrf_merge(rank_lists):
    """Reciprocal Rank Fusion: 多路召回排名合并 → {row: rrf_score}"""
    fused = {}
    for ranking in rank_lists:
        for rank, row in enumerate(ranking):
            fused[row] = fused.get(row, 0.0) + 1.0 / (_RRF_K + rank + 1)
    return fused


def state_info():
    """运行时状态（测试/诊断/性能记录用）"""
    meta = _STATE["meta"]
    return {
        "artifacts_available": artifacts_available(),
        "index_loaded": meta is not None,
        "texts_loaded": _STATE["texts"] is not None,
        "chunks": (meta or {}).get("count") or 0,
        "vectors_mb": round(VEC_FILE.stat().st_size / 1e6, 1) if VEC_FILE.exists() else 0,
        "texts_mb": round(JSONL_FILE.stat().st_size / 1e6, 1) if JSONL_FILE.exists() else 0,
        "meta_mb": round(META_FILE.stat().st_size / 1e6, 1) if META_FILE.exists() else 0,
    }


def reset_state():
    """清空进程内索引/文本缓存（测试用; 运行时主流程不调用）"""
    with _STATE_LOCK:
        _STATE["meta"] = None
        _STATE["vectors"] = None
        _STATE["texts"] = None
        _STATE["doc_len"] = None
        _STATE["tiers"] = None


def retrieve(query, k=3):
    """混合检索入口。返回 {"echoes": [...], "mode": str, "lex_scope": str, "candidates": int,
    "degraded_reason": str, "latency_ms": float} 或 None（artifact 缺失 → 调用方走旧路径兜底）。
    任何内部异常都折返回空结果, 不抛出（检索失败不拖垮 Agent）。"""
    if not artifacts_available():
        return None
    try:
        return _retrieve_inner(query, k)
    except Exception as e:
        return {"echoes": [], "mode": "error", "lex_scope": "-", "candidates": 0,
                "degraded_reason": f"{type(e).__name__}: {e}", "latency_ms": 0}


def _retrieve_inner(query, k):
    q = (query or "").strip()
    if not q:
        return {"echoes": [], "mode": "empty", "lex_scope": "-", "candidates": 0,
                "degraded_reason": "empty_query", "latency_ms": 0}
    t0 = time.time()
    _ensure_index()
    terms = _tokenize(q)

    # ① dense 召回（复用 Phase S _embed_query: 429 熔断/缓存/降级语义不变）
    dense, dense_err = [], ""
    if terms:
        try:
            from routes.agent_core import _embed_query, _embed_status
            qv = _embed_query(q[:500])
            if qv is not None:
                dense = _dense_recall(qv, _DENSE_CANDIDATES)
            else:
                dense_err = _embed_status.get("degraded_reason") or "embedding_unavailable"
        except Exception as e:
            dense_err = f"embedding_error: {e}"

    # ② 词法路（R3: 健康路径只在 dense 候选上重排, 逐条 seek 取文, 不整载语料;
    #    降级路径全语料 BM25——文本域加载一次后常驻复用, 等价旧词法基线召回面）
    lex_scores, lex_scope = {}, "-"
    if not dense:
        lex_scores = _lexical_scores_full(terms)
        lex_scope = "corpus"
        mode = "lexical" if dense_err else "lexical_only"
    elif _STATE["texts"] is not None:
        lex_scores = _lexical_scores_full(terms)     # 文本已常驻 → 全语料词法召回（复用, 不重复读盘）
        lex_scope = "corpus"
        mode = "hybrid_fulllex"
    else:
        cand_texts = {r: chunk_text(r) for r, _ in dense}
        lex_scores = _lexical_over_texts(terms, cand_texts, None)
        lex_scope = "candidates"
        mode = "hybrid"

    dense_rank = [r for r, _ in dense]
    lex_rank = [r for r, _ in sorted(lex_scores.items(), key=lambda x: -x[1])]
    fused = _rrf_merge([dense_rank, lex_rank])
    if not fused:
        return {"echoes": [], "mode": mode, "lex_scope": lex_scope, "candidates": 0,
                "degraded_reason": dense_err or "no_hit", "latency_ms": round((time.time() - t0) * 1000, 1)}

    # ③ rerank: RRF 主序 + 完整查询串命中加成 + tier 权威加成（primary-source-first）
    tiers = _ensure_tiers()
    meta_rows = _STATE["meta"].get("rows") or []
    reranked = []
    for row, rrf in fused.items():
        if row >= len(meta_rows):
            continue
        if _STATE["texts"] is not None:
            text = _STATE["texts"].get(row) or ""
        else:
            text = chunk_text(row)
        phrase = _PHRASE_BONUS if (q and q in text) else 0.0
        tier = meta_rows[row][2] or "C"
        bonus = _TIER_BONUS.get(tier, 0.0)
        reranked.append((rrf + phrase + bonus, rrf, phrase, row, text))
    reranked.sort(key=lambda x: (-x[0], x[3]))

    # ④ top-k evidence（元数据完整: book=著作 / chapter=章节 / tier / period / source_type / source）
    echoes = []
    for final, rrf, phrase, row, text in reranked[:max(1, k)]:
        r = meta_rows[row]
        echoes.append({
            "book": r[0], "chapter": r[1], "tier": r[2],
            "source_type": r[3], "source": r[4],
            "period": r[5], "year": r[6],
            "text": (text or "")[:_ECHO_TEXT_LEN],
            "score": round(min(final, 1.0), 4),
            "scores": {"rrf": round(rrf, 4), "phrase_bonus": phrase,
                       "dense": round(next((s for rr, s in dense if rr == row), 0.0), 3),
                       "lex": round(lex_scores.get(row, 0.0), 3)},
            "chunk_row": row,
        })
    return {"echoes": echoes, "mode": mode, "lex_scope": lex_scope,
            "candidates": len(fused), "degraded_reason": dense_err,
            "latency_ms": round((time.time() - t0) * 1000, 1)}
