# -*- coding: utf-8 -*-
"""agent 工具安全用例（R1-2: bid 白名单校验 / 检索上限）

覆盖 2026-08-18 整改（审计 S6 后半）：
- _safe_bid: 非法 / 路径穿越 / 格式不符 / 未知 bid 一律拒绝；合法 bid 放行
- chapter_meta / read_chapter: 恶意 bid 不得触达任意文件路径
- search_books / query_database: limit 钳制 [1,10]，结果数有上限（防 LLM 传超大 limit 拖垮检索）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes import agent


def _real_bid():
    for b in agent.get_books():
        if b.get("id"):
            return b["id"]
    raise AssertionError("books.json 中无有效 bid")


# ── bid 白名单校验 ─────────────────────────────────────
def test_safe_bid_rejects_invalid():
    for bad in ["../../etc/passwd", "../users.db", "a/b", "abc", "zzzzzzzzzzzz",
                "12345", "0" * 20, "F15E7FD89491", "d5498164021!", "", None, 12345]:
        assert agent._safe_bid(bad) is None, f"应拒绝: {bad!r}"


def test_safe_bid_accepts_real_book():
    bid = _real_bid()
    assert agent._safe_bid(bid) == bid


def test_safe_bid_rejects_unknown_but_format_valid():
    # 12 位十六进制但不在 books.json 中 → 必须拒绝（防拼路径读任意 JSON）
    assert agent._safe_bid("deadbeef0000") is None
    assert agent._safe_bid("ffffffffffff") is None


def test_chapter_read_rejects_malicious_bid():
    # 恶意 bid 不能触达任意目录（chapter_meta / read_chapter 内部先过 _safe_bid）
    assert agent.chapter_meta("../../etc") is None
    assert agent.read_chapter("../../etc", 0) is None
    assert agent.read_chapter("deadbeef0000", 0) is None


# ── 检索上限 ───────────────────────────────────────────
def test_int_arg_clamps_limit():
    assert agent._int_arg({"limit": 999}, "limit", 5, 1, 10) == 10
    assert agent._int_arg({"limit": -5}, "limit", 5, 1, 10) == 1
    assert agent._int_arg({"limit": "abc"}, "limit", 5, 1, 10) == 5
    assert agent._int_arg({}, "limit", 5, 1, 10) == 5


def test_search_books_limit_capped(monkeypatch):
    # 固定走关键词兜底路径（不依赖外部 embedding 服务），验证 limit 钳制
    monkeypatch.setattr(agent, "_embed_query", lambda q: None)
    # limit=999 被钳制到 10，最终结果最多 10*3=30 条
    out = agent._exec_search_books({"query": "哲学 存在", "limit": 999})
    assert len(out.get("results", [])) <= 30


def test_query_db_limit_capped():
    out = agent._exec_query_db({"table": "philosophers", "key": "", "limit": 999})
    assert len(out.get("results", [])) <= 10
    assert out["total"] >= len(out["results"])
