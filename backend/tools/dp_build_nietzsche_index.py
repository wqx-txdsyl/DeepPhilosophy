# -*- coding: utf-8 -*-
"""构建 Nietzsche 语料运行时检索索引（Phase R, 2026-08-30）

把 all_chunks.json（453MB, text+embedding 混合 JSON）拆为三个紧凑运行时 artifact,
运行时检索（backend/philo_retrieval.py）按需加载, 不再整载 453MB:

  data/ai_author/vector/nietzsche_vectors.npy   float32 [N,1024] 已 L2 归一（余弦=点积）
  data/ai_author/vector/nietzsche_chunks.jsonl  每行一个 chunk 的 {"text": ...}（按行 seek 随机访问）
  data/ai_author/vector/nietzsche_meta.json     行元数据 [book, chapter, tier, format, source,
                                                period, year, chars, off, len] + 词料统计

源文件 all_chunks.json 只读不动（增量 artifact, 不删不迁数据）。
book 级 period/year 从 corpus/book_metadata.json 取（权威源）, 缺失时从 chunk 文本前缀
"[尼采·早期·1873-1876·...]" 兜底解析。

用法: .venv/Scripts/python.exe backend/tools/dp_build_nietzsche_index.py [--force]
"""
import json
import os
import re
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # backend/
AI_DIR = BASE.parent / "data" / "ai_author"
SRC = AI_DIR / "corpus" / "chunks" / "all_chunks.json"
BOOK_META = AI_DIR / "corpus" / "book_metadata.json"
OUT_DIR = AI_DIR / "vector"
VEC_OUT = OUT_DIR / "nietzsche_vectors.npy"
JSONL_OUT = OUT_DIR / "nietzsche_chunks.jsonl"
META_OUT = OUT_DIR / "nietzsche_meta.json"

_PERIOD_RE = re.compile(r"[［\[]尼采·(早期|中期|晚期)·(\d{4})")


def _stream_chunks(path):
    """增量解析 JSON 数组（raw_decode 逐对象, 内存只保留当前 chunk）"""
    dec = json.JSONDecoder()
    buf = ""
    with open(path, encoding="utf-8") as f:
        f.read(1)  # '['
        while True:
            block = f.read(4 * 1024 * 1024)
            if not block:
                break
            buf += block
            while True:
                buf = buf.lstrip(" \n\r\t,")
                if not buf or buf[0] == "]":
                    buf = ""
                    break
                try:
                    obj, end = dec.raw_decode(buf)
                except Exception:
                    break
                yield obj
                buf = buf[end:]


def main():
    import numpy as np

    if VEC_OUT.exists() and JSONL_OUT.exists() and META_OUT.exists() and "--force" not in sys.argv:
        print("[skip] artifacts 已存在（--force 重建）")
        return 0
    t0 = time.time()
    book_meta = {}
    if BOOK_META.exists():
        try:
            book_meta = json.load(open(BOOK_META, encoding="utf-8"))
        except Exception:
            book_meta = {}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []          # [book, chapter, tier, format, source, period, year, chars, off, len]
    vecs = []
    n = 0
    with open(JSONL_OUT, "wb") as jf:
        off = 0
        for c in _stream_chunks(SRC):
            text = c.get("text") or ""
            line = json.dumps({"text": text}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            jf.write(line + b"\n")
            emb = c.get("embedding") or []
            book = c.get("book") or ""
            bm = book_meta.get(book) or {}
            period = bm.get("period") or ""
            year = bm.get("year") or ""
            if not period:
                m = _PERIOD_RE.search(text[:80])
                if m:
                    period, year = m.group(1), m.group(2)
            # chapter 截断: 上游个别 chunk（《查拉图斯特拉》末部）chapter 字段为整段正文,
            # 元数据只保留标题用途的前 120 字（源文件不动, 不删数据）
            rows.append([book, (c.get("chapter") or "")[:120], c.get("tier") or "", c.get("format") or "",
                         c.get("source") or "", period, year, c.get("chars") or len(text),
                         off, len(line)])
            if emb:
                vecs.append(emb)
            else:
                vecs.append([0.0] * 1024)   # 占位行（当前全量 6488 均有 embedding, 防御性）
            off += len(line) + 1
            n += 1
    mat = np.asarray(vecs, dtype="float32")
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    mat = mat / norms
    np.save(VEC_OUT, mat)

    tier_counts = {}
    for r in rows:
        tier_counts[r[2]] = tier_counts.get(r[2], 0) + 1
    meta = {
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "corpus/chunks/all_chunks.json",
        "count": n,
        "dim": int(mat.shape[1]),
        "normalized": True,
        "tier_counts": tier_counts,
        "rows": rows,   # [book, chapter, tier, format, source, period, year, chars, off, len]
    }
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    print(f"[done] chunks={n} dim={mat.shape[1]} "
          f"npy={VEC_OUT.stat().st_size/1e6:.1f}MB jsonl={JSONL_OUT.stat().st_size/1e6:.1f}MB "
          f"meta={META_OUT.stat().st_size/1e6:.1f}MB 耗时{time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
