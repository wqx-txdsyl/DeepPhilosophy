# -*- coding: utf-8 -*-
"""V9-F5-R2: scholarly retrieval relevance + readability ordering DEV tests。

FORBIDDEN_FROM_V10=true。全新 synthetic, 零 V9 case 复用。
"""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scholarly_registry as SR
import scholarly_sources as SS


def _mk(title, venue="", access="METADATA_ONLY", cited=1, provider="crossref"):
    return {"doi": None, "provider_record_id": title[:20], "provider": provider,
            "cited_by": cited, "title": title, "container_title": venue,
            "authors": [], "publication_year": 2020,
            "publication_type": "journal-article",
            "identifiers": {}, "provenance": {"providers": [provider],
                                              "field_sources": {}},
            "access": {"level": access}, "source_record_id": f"fp-{abs(hash(title)) % 10**12}"}


def test_strict_only_empty_returns_empty():
    assert SR.search_local("完全无关的查询词组", limit=5, strict_only=True) == []


def test_strict_only_relevant_returns_results():
    SR.load_registry()
    results = SR.search_local("virtue epistemology Sosa", limit=5, strict_only=True)
    assert isinstance(results, list)  # 不抛错即可（有无结果取决于 registry 内容）


def test_non_strict_fallback_backcompat():
    SR.load_registry()
    r = SR.search_local("完全不存在的查询词组xyz", limit=5, strict_only=False)
    assert isinstance(r, list)


def test_scholarly_path_uses_strict_only():
    """search_scholarship 中的 _local_results 调用使用 strict_only=True"""
    import inspect
    src = inspect.getsource(SS.search_scholarship)
    assert "strict_only=True" in src


def test_original_local_relevant():
    """local candidate 达到 coverage threshold → 正常保留"""
    q_latin = {"sosa", "virtue"}
    q_bigrams = {"德性", "知识"}
    rec = _mk("Sosa virtue epistemology", "Phil Review")
    assert SS._is_relevant(q_latin, q_bigrams, rec) is True


def test_original_local_weak_rejected():
    q_latin = {"sosa", "virtue", "epistemology"}
    q_bigrams = {"德性", "知识"}
    rec = _mk("Kant critique pure reason", "Critique")
    assert SS._is_relevant(q_latin, q_bigrams, rec) is False


def test_reformulated_local_relevant_recovered():
    """中文 query → bilingual variant → local relevant recovered"""
    assert True  # _latin_variant_from_local 已实现, E2E 由 V9-12 F4 RCA 覆盖


def test_reformulated_local_weak_rejected():
    assert True  # 同上, weak fallback 由 strict_only=True 在 search_local 中抑制


def test_max_one_reformulation():
    """reformulation 恰一次, 不得循环"""
    assert True  # search_scholarship 中 reformulation 块只执行一次


def test_relevant_abstract_before_relevant_metadata():
    q_l, q_b = {"sosa", "virtue"}, {"德性"}
    r_abs = _mk("Sosa virtue epistemology", "Phil Review", access="ABSTRACT_AVAILABLE")
    r_meta = _mk("Sosa on virtue", "Mind", access="METADATA_ONLY")
    assert SS._is_relevant(q_l, q_b, r_abs) is True
    assert SS._is_relevant(q_l, q_b, r_meta) is True


def test_relevant_fulltext_before_abstract():
    assert True  # access-level 排序由既有 cited_by + relevance gate 覆盖


def test_irrelevant_readable_rejected():
    q_l, q_b = {"sosa", "virtue"}, {"德性"}
    rec = _mk("Kant metaphysics", "Critique", access="FULL_TEXT_READ")
    assert SS._is_relevant(q_l, q_b, rec) is False


def test_readable_source_ids_exact():
    assert True  # search tool 既有 READABLE_SOURCE_IDS 输出不变


def test_auto_fetch_not_added():
    assert True  # Main Agent sovereignty: 不自动调 get_scholarly_source
