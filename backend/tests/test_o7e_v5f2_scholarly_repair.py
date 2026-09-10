# -*- coding: utf-8 -*-
"""O7-E V5-F2: scholarly pipeline repair 回归（§B 相关性重排 / §C 可读计数 /
§D 书目 grounding guard / §F preflight 结构）。

允许对受控输入做单元级测试（测的是机械派生逻辑, 不是 mock 生产检索通道——
端到端行为由 dev behavioral probes 以真实 production 路径验收）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scholarly_registry as SR          # noqa: E402
import scholarly_sources as SS           # noqa: E402
from routes import agent_tools_scholarly as ATS  # noqa: E402
import final_validator as FV             # noqa: E402

# ══ §B: search_local 多词覆盖率重排 ═══════════════════════════
def test_search_local_multiterm_requires_full_coverage():
    """2 词查询: 只含单词碰撞的记录不得进入结果（moral+luck 需同时出现）。"""
    res = SR.search_local("moral luck", limit=8)
    assert res, "moral luck 零命中（registry 覆盖回归）"
    for r in res:
        hay = SR._record_haystack(r)
        assert "luck" in hay, f"单词碰撞记录混入: {r.get('title')}"


def test_search_local_dev_topics_direct_in_topk():
    """六个 dev topic 查询: 相关记录（覆盖率满分）必须进入 top-k。"""
    expect = {
        "Searle Chinese room": "chinese room",
        "moral luck Williams Nagel": "moral luck",
        "Nishida Kitaro pure experience": "nishida",
        "Averroes Ibn Rushd philosophy religion": "averroes",
        "Anscombe modern moral philosophy virtue": "modern moral philosophy",
        "Mackie error theory queerness": "inventing right and wrong",
    }
    for q, marker in expect.items():
        res = SR.search_local(q, limit=8)
        assert res, f"{q!r} 零命中"
        top = " ".join(str(r.get("title") or "").lower() for r in res[:3])
        assert marker in top, f"{q!r} top3 无直接相关记录: {top!r}"


def test_search_local_fallback_never_empty():
    """长查询部分覆盖时不得静默空手（兜底退回 OR 排序）。"""
    res = SR.search_local("Nishida Kitaro pure experience Kyoto School Japan", limit=8)
    assert res, "兜底路径不应返回空"


# ══ §C: search 响应可读计数（受控输入单元测试）═════════════════
def test_search_response_readable_count(monkeypatch):
    fake = {"query": "q", "results": [
        {"source_record_id": "doi:10.1/a", "title": "A", "authors": [], "publication_year": 2001,
         "publication_type": "JOURNAL_ARTICLE", "container_title": "V",
         "identifiers": {"doi": "10.1/a"}, "access": {"level": "ABSTRACT_AVAILABLE"},
         "abstract": {"text": "abstract a", "source": None, "hash": None},
         "provenance": {"providers": ["crossref"], "field_sources": {}}},
        {"source_record_id": "doi:10.1/b", "title": "B", "authors": [], "publication_year": 2002,
         "publication_type": "JOURNAL_ARTICLE", "container_title": "V",
         "identifiers": {"doi": "10.1/b"}, "access": {"level": "METADATA_ONLY"},
         "abstract": {"text": None, "source": None, "hash": None},
         "provenance": {"providers": ["crossref"], "field_sources": {}}},
    ], "providers_queried": ["LOCAL_CURATED"], "errors": []}
    monkeypatch.setattr(SS, "search_scholarship", lambda *a, **k: fake)
    out = ATS._exec_search_scholarship({"query": "q"})
    assert out["READABLE_RESULT_COUNT"] == 1
    assert out["READABLE_SOURCE_IDS"] == ["doi:10.1/a"]
    assert "get_scholarly_source" in out["note"]


def test_search_response_all_metadata_note(monkeypatch):
    fake = {"query": "q", "results": [
        {"source_record_id": "doi:10.1/b", "title": "B", "authors": [], "publication_year": 2002,
         "publication_type": "JOURNAL_ARTICLE", "container_title": "V",
         "identifiers": {"doi": "10.1/b"}, "access": {"level": "METADATA_ONLY"},
         "abstract": {"text": None, "source": None, "hash": None},
         "provenance": {"providers": ["crossref"], "field_sources": {}}},
    ], "providers_queried": ["LOCAL_CURATED"], "errors": []}
    monkeypatch.setattr(SS, "search_scholarship", lambda *a, **k: fake)
    out = ATS._exec_search_scholarship({"query": "q"})
    assert out["READABLE_RESULT_COUNT"] == 0
    assert "METADATA_ONLY" in out["note"]


# ══ §D + F2-R1 P0: bibliography grounding guard（逐字段溯源语义）═══════
def _rec(title, year, authors, doi, verified):
    return {"source_record_id": doi, "title": title,
            "authors": [{"name": a} for a in authors], "year": year,
            "publication_type": "JOURNAL_ARTICLE", "venue": "V",
            "doi": doi, "source_category": "UNKNOWN",
            "access_level": "ABSTRACT_AVAILABLE", "provider": "crossref",
            "source_providers": ["crossref"], "retrieval_origin": "LOCAL_CURATED",
            "bibliographic_verified_fields": verified}


def _mackie_log():
    return [{"name": "search_scholarship", "result_full": {"results": [
        _rec("Ethics: Inventing Right and Wrong", 1977, ["J. L. Mackie"],
             "10.1111/mack.1977",
             ["authors", "title", "publication_year", "doi"])]}}]


def test_r1_no_trace_bibliography_blocked():
    """F2-R1 P0: 零 scholarly record 时精确书目必须 flag（不得自动 PASS）。"""
    for ans in ("Mackie, Ethics: Inventing Right and Wrong, 1977 主张错误论。",
                "见 Derek Parfit, On What Matters, Vol. 2 (OUP, 2011)。",
                "Enoch, Taking Morality Seriously (OUP, 2011) 反对错误论。"):
        issues = FV.check_bibliography_groundedness(ans, [])
        assert any(i.code == "UNGROUNDED_BIBLIOGRAPHIC_DETAIL" for i in issues), ans


def test_r1_v512_triple_all_flagged():
    """V5-12 三条书目 + 无 retrieved record → 逐条 flag。"""
    ans = ("J. L. Mackie, Ethics: Inventing Right and Wrong, 1977; "
           "Derek Parfit, On What Matters, Vol. 2 (OUP, 2011); "
           "Enoch, Taking Morality Seriously (OUP, 2011)。")
    issues = FV.check_bibliography_groundedness(ans, [])
    assert len([i for i in issues if i.code == "UNGROUNDED_BIBLIOGRAPHIC_DETAIL"]) >= 2, issues


def test_r1_field_level_publisher_unverified_fails():
    """retrieved record 无 verified publisher: (Clarendon Press, 1977) → 必须 FAIL
    （不得借作者+同年放行）。"""
    ans = "J. L. Mackie, Ethics: Inventing Right and Wrong (Clarendon Press, 1977)。"
    issues = FV.check_bibliography_groundedness(ans, _mackie_log())
    assert any(i.code == "UNGROUNDED_BIBLIOGRAPHIC_DETAIL" for i in issues), issues


def test_r1_field_level_grounded_entry_passes():
    """作者/书名/年份全部匹配同一 verified record → PASS。"""
    ans = "J. L. Mackie, Ethics: Inventing Right and Wrong, 1977 主张错误论。"
    issues = FV.check_bibliography_groundedness(ans, _mackie_log())
    assert not issues, issues


def test_r1_doi_grounded_passes():
    issues = FV.check_bibliography_groundedness("参见 doi:10.1111/mack.1977 的论证。",
                                                _mackie_log())
    assert not issues, issues


def test_r1_prose_years_not_flagged():
    """普通行文年份/非书目形态不触发（conservative 触发面）。"""
    ans = "康德在 1781 年出版第一部批判; 1977 年学界才开始系统讨论错误论。"
    issues = FV.check_bibliography_groundedness(ans, _mackie_log())
    assert not issues, issues


def test_validator_integrates_bibliography_guard():
    res = FV.validate_final_candidate(
        "见 Derek Parfit, On What Matters, Vol. 2 (OUP, 2011)。",
        raw_tool_log=_mackie_log())
    assert not res.ok
    assert any(i.code == "UNGROUNDED_BIBLIOGRAPHIC_DETAIL" for i in res.issues)
