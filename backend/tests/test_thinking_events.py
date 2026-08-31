# -*- coding: utf-8 -*-
"""Thinking UI 安全事件回归（2026-08-31）
- interpret_thinking: 工具结果解读为确定性片段, 不引用 raw CoT/system prompt
- 绝不输出内部字段（book_id/chapter_idx）与结果正文
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine_langgraph import interpret_thinking, _count_result


def test_count_result_only_lengths():
    assert _count_result([1, 2, 3]) == 3
    assert _count_result({"results": [{"book_id": "x"}]}) == 1
    assert _count_result({"items": []}) == 0
    assert _count_result({"weird": {"a": 1}}) == 0
    assert _count_result("text") == 0


def test_search_books_hit():
    s = interpret_thinking("search_books", {"query": "合目的性"}, {"results": [{"book_id": "x"}] * 2}, "zh")
    assert "2 项" in s and "原典检索" in s
    assert "book_id" not in s


def test_get_chapter_with_book_entity():
    s = interpret_thinking("get_chapter", {"book": "判断力批判", "chapter": "序言"}, {"content": "..."}, "zh")
    assert "已调取" in s and "判断力批判" in s
    en = interpret_thinking("get_chapter", {}, {"content": "..."}, "en")
    assert "Chapter text" in en


def test_no_hit_message():
    s = interpret_thinking("search_books", {"query": "x"}, {"results": []}, "zh")
    assert "没有检索到" in s


def test_non_retrieval_tool_silent():
    assert interpret_thinking("write_essay", {"topic": "x"}, {}, "zh") is None
    assert interpret_thinking("confrontation", {"a": 1}, {"results": [1]}, "zh") is None


def test_websearch_auto_detect_text():
    s = interpret_thinking("websearch", {"query": "生命"}, [{"url": "u"}], "zh")
    assert "网上检索返回 1 项" in s
    assert "url" not in s
