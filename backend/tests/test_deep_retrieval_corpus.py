"""Offline replay against real books and saved embedding-2 query vectors.

No remote API calls. The fixture makes bad non-empty retrieval observable;
assertions check source identity, actual passages and honest negative results.
"""
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes import agent
import deep_agent_tools as deep

FIXTURE = json.loads((Path(__file__).parent / "fixtures/deep_retrieval_queries.json").read_text())
QUERIES = {row["query"]: row for row in FIXTURE["queries"]}


@pytest.fixture(autouse=True)
def replay_embeddings(monkeypatch):
    if not deep.core.get_books() or not (deep.core.CHAPTERS_DIR / "d9272a80942a").exists():
        pytest.skip("requires the local philosophy corpus")
    monkeypatch.setattr(agent, "_embed_query", lambda query: QUERIES.get(query, {}).get("embedding"))


@pytest.mark.parametrize("query", [
    "不存在的概念xyz", "asdfqwerzxcv", "不存在的哲学概念阿布拉卡达布拉",
    "自由意志量子烤鸭说", "今日上海天气", "2026年iPhone维修报价",
])
def test_unrelated_queries_return_no_claimed_evidence(query):
    out = deep.search_books({"query": query, "limit": 5})
    assert out["results"] == [], [(r["book_title"], r["snippet"]) for r in out["results"]]


@pytest.mark.parametrize("query, expected_fragment", [
    ("人工智能是否具有意识", "塞尔"),
    ("人为何愿意服从统治者", "政治学"),
    ("不受别人控制才算自由吗", "自由"),
])
def test_paraphrases_keep_useful_reading_candidates_without_certifying_them(query, expected_fragment):
    out = deep.search_books({"query": query, "limit": 3})
    assert out["results"]
    first = out["results"][0]
    assert expected_fragment in json.dumps(first, ensure_ascii=False)
    assert first["evidence_scope"] == "unverified_candidate"
    assert first["needs_read"] is True


def test_analects_quote_resolves_to_xue_er_not_zhong_yong():
    out = deep.search_books({"query": "人不知而不愠 不亦君子乎", "limit": 1})
    first, = out["results"]
    assert first["book_title"] == "论语"
    assert first["chapter_title"] == "学而篇"
    assert "人不知而不愠，不亦君子乎" in first["snippet"]
    chapter = deep.get_chapter(first["read_args"])
    assert "人不知而不愠，不亦君子乎" in chapter["text"]


def test_low_similarity_known_concept_is_rescued_by_actual_text():
    # Old vector ranking led this exact Kant phrase to natural law / Hobbes.
    out = deep.search_books({"query": "人为自然立法", "limit": 2})
    assert out["method"] == "exact_fulltext"
    assert "康德" in out["results"][0]["chapter_title"]
    assert all("人为自然立法" in result["snippet"] for result in out["results"])
    for result in out["results"]:
        assert "人为自然立法" in deep.get_chapter(result["read_args"])["text"]


def test_concept_trace_does_not_turn_neighbours_into_concept_history():
    out = deep.concept_trace({"concept": "不存在的哲学概念阿布拉卡达布拉"})
    assert out["hits"] == 0 and out["timeline"] == []
    out = deep.concept_trace({"concept": "自由意志"})
    assert out["hits"] > 0 and out["matched_books"] > 1
    assert all("自由意志" in row["snippet"] for row in out["timeline"])
