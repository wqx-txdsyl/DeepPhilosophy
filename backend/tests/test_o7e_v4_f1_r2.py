# -*- coding: utf-8 -*-
"""O7-E V4-F1-R1.3: 阿奎那 primary corpus 检索回归（production search_books → get_chapter 真实路径）。

Reviewer R1.3 任务书约束:
- 禁止 scholarly_sources._local_results / scholarly_registry.search_local 等内部 FTS 旁路
- 必须走 production primary tools: search_books → get_chapter, 命中 book_id=590ee1d9a55a
- 允许禁用外部 embedding（_embed_query→None）走 production lexical fallback;
  禁止 mock 检索结果/排序/book_id/章节内容
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes import agent as agent_mod   # noqa: E402

AQUINAS_BID = "590ee1d9a55a"

# R1.3 acceptance queries（EN/CN/Latin 三通道, 逐字取自任务书）
ACCEPTANCE_QUERIES = {
    "EN": ["Thomas Aquinas Summa Theologiae", "natural law Aquinas"],
    "CN": ["阿奎那 神学大全 自然法", "阿奎那 恶是善的缺乏"],
    "Latin": ["Summa Theologiae lex naturalis", "lex aeterna", "lex humana", "privatio boni"],
}

# 真实 READ 探针: chapter_idx → 原典 QUESTION 标记（q48/q49 + q93/q94/q95）
QUESTION_READS = {
    1: "QUESTION 48",
    2: "QUESTION 49",
    6: "QUESTION 93",
    7: "QUESTION 94",
    8: "QUESTION 95",
}


@pytest.fixture(autouse=True)
def _lexical_only(monkeypatch):
    """禁用外部 embedding → production lexical fallback（任务书明示允许）。"""
    monkeypatch.setattr(agent_mod, "_embed_query", lambda q: None)


def _search(query):
    out = agent_mod.TOOLS["search_books"]["execute"]({"query": query, "limit": 10})
    assert "error" not in out, f"search_books error: {out}"
    assert out.get("method") == "lexical", f"未走 production lexical 路径: {out.get('method')}"
    return out, {r.get("book_id") for r in out.get("results", [])}


@pytest.mark.parametrize("lang,queries", sorted(ACCEPTANCE_QUERIES.items()))
def test_acceptance_queries_hit_aquinas_primary(lang, queries):
    """EN/CN/Latin 自然查询经正常 production search_books 命中阿奎那选编书。"""
    for q in queries:
        out, ids = _search(q)
        assert AQUINAS_BID in ids, f"[{lang}] '{q}' 未命中 {AQUINAS_BID}（top book_ids: {sorted(ids)[:6]}）"


def test_search_hit_then_real_read_q48_q49_q93_q94_q95():
    """search_books 命中后 get_chapter 真实读取原典五章（q48/q49 + q93/q94/q95）。"""
    out, ids = _search("natural law Aquinas")
    assert AQUINAS_BID in ids
    for idx, marker in QUESTION_READS.items():
        ch = agent_mod.TOOLS["get_chapter"]["execute"]({"book_id": AQUINAS_BID, "chapter_idx": idx})
        assert ch.get("book_id") == AQUINAS_BID, f"chapter {idx}: book_id 不符"
        text = ch.get("text") or ""
        assert len(text) > 1000, f"chapter {idx} 正文过短: {len(text)} chars"
        assert marker in text, f"chapter {idx} 缺原典标记 {marker}"


def test_primary_body_metadata_contamination_false():
    """q48 原典正文纯净: 直接以 QUESTION 48 开头, 无 CN retrieval 简介段污染。"""
    ch = agent_mod.TOOLS["get_chapter"]["execute"]({"book_id": AQUINAS_BID, "chapter_idx": 1})
    text = (ch.get("text") or "").lstrip()
    assert text.startswith("QUESTION 48"), f"q48 正文头部被污染: {text[:80]!r}"
