# -*- coding: utf-8 -*-
"""O7-E V5-F2-R1.1: scholarly 原调用即时快照 provenance 回归。

§2 原调用即时快照（engine_langgraph._scholarly_call_snapshot）:
immutable/bounded/无 CoT; §4 突变免疫; §5 重复调用身份。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine_langgraph import _scholarly_call_snapshot  # noqa: E402


def _search_result():
    return {"query": "moral luck", "results": [
        {"source_record_id": "doi:10.1/x", "title": "Moral Luck",
         "authors": [{"name": "B. Williams"}], "publication_year": 1981,
         "access_level": "METADATA_ONLY", "retrieval_origin": "LOCAL_CURATED"},
    ], "errors": [{"provider": "openalex", "error": "PROVIDER_RATE_LIMIT"}],
        "offline_mode": False}


def test_search_snapshot_fields():
    snap = _scholarly_call_snapshot("search_scholarship", _search_result())
    assert snap["returned_source_record_ids"] == ["doi:10.1/x"]
    assert snap["access_levels"] == {"doi:10.1/x": "METADATA_ONLY"}
    assert snap["retrieval_origins"] == ["LOCAL_CURATED"]
    assert snap["provider_errors"][0]["provider"] == "openalex"
    assert snap["offline_mode"] is False
    assert "results" not in snap and "abstract" not in str(snap)  # bounded, 无正文


def test_mutation_immunity_search_snapshot():
    """§4: READ 晋升/cache 变更后, 既有 SEARCH snapshot 不得反向改变。"""
    result = _search_result()
    snap = _scholarly_call_snapshot("search_scholarship", result)
    # 事后: 原始 result 对象被就地晋升（模拟 _promote_access）+ cache 变更
    result["results"][0]["access_level"] = "FULL_TEXT_READ"
    assert snap["access_levels"]["doi:10.1/x"] == "METADATA_ONLY", \
        "search 快照被事后状态污染（MUTATION_IMMUNITY 破坏）"


def test_read_snapshot_shows_transition():
    """§4: READ snapshot 正确显示 before→after transition。"""
    result = {"source_record_id": "doi:10.1/x",
              "access_level_before": "METADATA_ONLY",
              "access_level_after": "FULL_TEXT_READ",
              "returned_evidence_level": "FULL_TEXT_READ",
              "content_hash": "abc123"}
    snap = _scholarly_call_snapshot("get_scholarly_source", result)
    assert snap["access_before"] == "METADATA_ONLY"
    assert snap["access_after"] == "FULL_TEXT_READ"
    assert snap["returned_evidence_level"] == "FULL_TEXT_READ"
    assert snap["content_hash"] == "abc123"


def test_repeated_call_snapshots_independent():
    """§5: 同 query 两次调用 → 两个独立快照对象, 互不影响（身份由 tool_call_id
    在事件层绑定, 快照本身不按 SID/query 合并）。"""
    s1 = _scholarly_call_snapshot("search_scholarship", _search_result())
    s2 = _scholarly_call_snapshot("search_scholarship", _search_result())
    assert s1 is not s2 and s1["access_levels"] is not s2["access_levels"]
    s1["access_levels"]["doi:10.1/x"] = "FULL_TEXT_READ"
    assert s2["access_levels"]["doi:10.1/x"] == "METADATA_ONLY"


def test_non_scholarly_tool_no_snapshot():
    assert _scholarly_call_snapshot("search_books", {"results": []}) is None
    assert _scholarly_call_snapshot("get_chapter", {"text": "x"}) is None
    assert _scholarly_call_snapshot("search_scholarship", "not-a-dict") is None
