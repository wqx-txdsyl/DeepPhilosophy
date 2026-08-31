# -*- coding: utf-8 -*-
"""Thinking UI 安全事件回归（2026-08-31）
- interpret_thinking: 工具结果解读为确定性片段, 不引用 raw CoT/system prompt
- 绝不输出内部字段（book_id/chapter_idx）与结果正文
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine_langgraph import interpret_thinking, _count_result, RationaleParser, _RAT_OPEN, _RAT_CLOSE


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


def test_rationale_single_chunk():
    p = RationaleParser()
    emit, rats = p.push(f"前置文本{_RAT_OPEN}问题重点是体系位置而非内容简介{_RAT_CLOSE}后置文本")
    assert rats == ["问题重点是体系位置而非内容简介"]
    assert emit == "前置文本后置文本"


def test_rationale_split_across_chunks():
    p = RationaleParser()
    emit, rats = p.push(f"前{_RAT_OPEN[:6]}")
    assert emit == "前" and not rats
    emit2, rats2 = p.push(f"{_RAT_OPEN[6:]}需要确认中介关系{_RAT_CLOSE[:8]}")
    assert emit2 == "" and not rats2
    emit3, rats3 = p.push(f"{_RAT_CLOSE[8:]}正文继续")
    assert rats3 == ["需要确认中介关系"]
    assert emit3 == "正文继续"


def test_rationale_unclosed_released_at_finish():
    p = RationaleParser()
    p.push(f"{_RAT_OPEN}未闭合内容")
    tail = p.finish()
    assert tail == f"{_RAT_OPEN}未闭合内容"   # 宁可展示原文, 不丢内容


def test_rationale_label_prefix_hold_release():
    p = RationaleParser()
    # chunk 尾部切碎 open 前缀 → hold, 不误吞正文
    emit, rats = p.push("正文文本<ra")
    assert emit == "正文文本" and not rats
    emit2, rats2 = p.push("tionale>摘要</rationale>余")
    assert rats2 == ["摘要"]
    assert emit2 == "余"


def test_rationale_no_label_passthrough():
    p = RationaleParser()
    emit, rats = p.push("普通思考文字")
    assert emit == "普通思考文字" and not rats


def test_rationale_multiple_pairs():
    p = RationaleParser()
    emit, rats = p.push(f"{_RAT_OPEN}A{_RAT_CLOSE}中{_RAT_OPEN}B{_RAT_CLOSE}尾")
    assert rats == ["A", "B"]
    assert emit == "中尾"
