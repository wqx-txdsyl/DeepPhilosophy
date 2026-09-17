"""Deep-only regression: actual passage semantics, honest empty results and speakers."""
import copy
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes import agent
import deep_agent_tools as deep


@pytest.fixture
def small_library(monkeypatch):
    books = [
        {"id": "primary", "title": "论语", "author": "孔子"},
        {"id": "secondary", "title": "哲学讲义", "author": "讲师"},
        {"id": "unrelated", "title": "形而上学", "author": "亚里士多德"},
    ]
    chapters = {
        "primary": [(2, "学而篇", "学而时习之，不亦说乎？人不知而不愠，不亦君子乎？")],
        "secondary": [(0, "自由意志", "背景。" * 1400 + "对于自由意志，论者有不同的解释。")],
        "unrelated": [(0, "存在论", "不存在是一个存在论问题。")],
    }
    monkeypatch.setattr(deep.core, "get_books", lambda: books)
    monkeypatch.setattr(deep.core, "_book_chapter_texts", lambda bid: chapters[bid])
    monkeypatch.setattr(deep.core, "chapter_meta", lambda bid: {"chapterCount": 3})
    monkeypatch.setattr(deep.core, "book_by_id", lambda bid: next((b for b in books if b["id"] == bid), None))
    monkeypatch.setattr(deep.core, "read_chapter", lambda bid, idx: next(
        ({"title": title, "text": text} for i, title, text in chapters[bid] if i == idx), None))
    monkeypatch.setattr(agent, "_embed_query", lambda query: None)
    deep._lexical_search.cache_clear()
    yield books, chapters
    deep._lexical_search.cache_clear()


def test_quote_combines_fragments_and_returns_actual_passage(small_library):
    out = deep.search_books({"query": "人不知而不愠 不亦君子乎", "limit": 1})
    hit, = out["results"]
    assert hit["book_title"] == "论语"
    assert hit["chapter_title"] == "学而篇"
    assert "人不知而不愠，不亦君子乎" in hit["snippet"]
    assert hit["match_type"] == "exact_passage"
    assert hit["needs_read"] is True


def test_fulltext_recall_does_not_require_book_metadata_or_first_2000_chars(small_library):
    out = deep.search_books({"query": "自由意志", "limit": 1})
    assert out["results"][0]["book_title"] == "哲学讲义"
    assert "对于自由意志" in out["results"][0]["snippet"]
    assert len(out["results"]) == 1


def test_catalogue_hit_does_not_invent_supporting_chapter(small_library):
    out = deep.search_books({"query": "亚里士多德"})
    assert out["method"] == "catalogue"
    assert "chapter_idx" not in out["results"][0]
    assert out["results"][0]["snippet"] == ""
    assert out["results"][0]["evidence_scope"] == "catalogue"


def test_concept_trace_requires_literal_occurrence(small_library):
    out = deep.concept_trace({"concept": "不存在的哲学概念"})
    assert out["hits"] == 0
    assert out["timeline"] == []
    out = deep.concept_trace({"concept": "自由意志"})
    assert out["hits"] == 1
    assert "自由意志" in out["timeline"][0]["snippet"]
    # Two words appearing in different places are not an occurrence of a phrase.
    assert deep.concept_trace({"concept": "自由 意志"})["hits"] == 0


def test_chapters_after_300_are_searchable(small_library, monkeypatch):
    _, chapters = small_library
    monkeypatch.setattr(deep.core, "chapter_meta", lambda bid: {"chapterCount": 302} if bid == "primary" else {})
    original = deep.core.read_chapter
    monkeypatch.setattr(deep.core, "read_chapter", lambda bid, idx:
                        {"title": "附编", "text": "罕见命中片段"} if (bid, idx) == ("primary", 301)
                        else original(bid, idx))
    out = deep.search_books({"query": "罕见命中片段"})
    assert out["results"][0]["chapter_idx"] == 301


def test_search_read_args_reach_passages_after_the_old_6000_cutoff(small_library):
    _, chapters = small_library
    text = "前置讨论。" * 1600 + "关键证据在这里。" + "后续论证。" * 800
    chapters["secondary"] = [(0, "关于依据", text)]
    located = deep.search_books({"query": "关键证据在这里", "limit": 1})["results"][0]
    assert located["read_args"]["focus"] == "关键证据在这里"
    read = deep.get_chapter(located["read_args"])
    assert "关键证据在这里" in read["text"]
    assert read["excerpt_start"] > 6000
    assert read["text"] == text[read["excerpt_start"]:read["excerpt_end"]]
    assert len(read["text"]) <= 2800 and read["evidence_scope"] == "chapter_excerpt"
    next_read = deep.get_chapter({**located["read_args"], "offset": read["next_offset"]})
    assert next_read["excerpt_start"] == read["excerpt_end"]


def test_directory_returns_real_indexes_and_filtered_pages(small_library, monkeypatch):
    monkeypatch.setattr(deep.core, "chapter_meta", lambda _bid: {
        "chapterCount": 3, "chapterTitles": ["卷首", "目录", "学而篇"]})
    detail = deep.get_book_detail({"book_id": "primary", "focus": "学而"})
    assert detail["chapters"] == [{"index": 2, "title": "学而篇"}]
    assert detail["has_more"] is False
    first = deep.get_book_detail({"book_id": "primary", "limit": 1})
    assert first["next_offset"] == 1
    second = deep.get_book_detail({"book_id": "primary", "limit": 1, "offset": first["next_offset"]})
    assert second["chapters"][0]["index"] == 1


def test_known_book_without_chapter_meta_reports_unreadable_catalogue(small_library, monkeypatch):
    monkeypatch.setattr(deep.core, "chapter_meta", lambda _bid: None)
    monkeypatch.setattr(deep.core, "_book_chapter_texts", lambda _bid: [])
    detail = deep.get_book_detail({"book_id": "primary"})
    assert detail["title"] == "论语"
    assert detail["chapterCount"] == 0
    assert detail["chapters"] == []


def test_high_cosine_without_distribution_separation_is_rejected(small_library, monkeypatch):
    scores = np.linspace(0.50, 0.61, 100, dtype="float32")
    vectors = np.column_stack([scores, np.sqrt(1 - scores ** 2)])
    monkeypatch.setattr(agent, "_embed_query", lambda query: [1, 0])
    monkeypatch.setattr(deep.core, "_load_vectors", lambda: (vectors, [{"bid": "unrelated", "idx": 0}] * 100))
    out = deep.search_books({"query": "不存在的哲学概念阿布拉卡达布拉"})
    assert out["results"] == []
    assert out["method"] == "no_match"


@pytest.mark.parametrize("value", [None, [], {}, 123, "", " 。 "])
def test_invalid_retrieval_input_does_not_embed(value, monkeypatch):
    monkeypatch.setattr(agent, "_embed_query", lambda _: pytest.fail("invalid input must not call a provider"))
    assert "error" in deep.search_books({"query": value})


@pytest.mark.parametrize("speakers", ["康德,尼采", "康德，尼采", "康德、尼采", "康德和尼采", ["康德", "尼采"]])
def test_debate_really_gives_each_speaker_a_turn(speakers, monkeypatch):
    slot = {"debate": None}
    calls = []
    monkeypatch.setattr(deep.memory, "_mem_slot", lambda: slot)
    monkeypatch.setattr(deep.memory, "_debate_round", lambda names, topic, ctx, round_no:
                        calls.extend(names) or [name + ": 论证" for name in names])
    monkeypatch.setattr(deep.memory, "_auto_visualize", lambda _: None)
    monkeypatch.setattr(deep.memory, "_debate_map_text", lambda _: None)
    result = deep.philosopher_debate({"topic": "自由", "speakers": speakers, "rounds": 1})
    assert calls == ["康德", "尼采"]
    assert result["debate"] == ["康德: 论证", "尼采: 论证"]


@pytest.mark.parametrize("speakers", ["康德", "康德,康德", "康德,尼采,黑格尔,柏拉图", [], ["康德", 7], 7, {}, ["康德,尼采", "柏拉图"]])
def test_invalid_speaker_sets_do_not_silently_default_or_spend(speakers, monkeypatch):
    monkeypatch.setattr(deep.memory, "llm_chat", lambda *_a, **_kw: pytest.fail("invalid speakers must not generate"))
    assert "error" in deep.philosopher_debate({"topic": "自由", "speakers": speakers})


def test_name_containing_connector_is_preserved_across_rounds(monkeypatch):
    slot = {"debate": None}
    calls = []
    monkeypatch.setattr(deep.memory, "_mem_slot", lambda: slot)
    monkeypatch.setattr(deep.memory, "_save_agent_memory", lambda: None)
    monkeypatch.setattr(deep.memory, "_debate_round", lambda names, *_a, **_kw:
                        calls.append(list(names)) or [name + ": 论证" for name in names])
    first = deep.philosopher_debate({"topic": "关系伦理", "speakers": ["和辻哲郎", "康德"], "mode": "step"})
    assert first["debate"][0].startswith("和辻哲郎:")
    deep.philosopher_debate({"topic": "继续", "action": "continue"})
    assert calls == [["和辻哲郎", "康德"], ["和辻哲郎", "康德"]]


def test_continue_without_session_does_not_create_fake_default_debate(monkeypatch):
    monkeypatch.setattr(deep.memory, "_mem_slot", lambda: {"debate": None})
    monkeypatch.setattr(deep.memory, "llm_chat", lambda *_a, **_kw: pytest.fail("no session must not generate"))
    assert "error" in deep.philosopher_debate({"topic": "继续", "action": "continue"})


def test_registry_and_legacy_debate_remain_unchanged():
    before = {name: copy.deepcopy(meta["parameters"]) for name, meta in agent.TOOLS.items()}
    old_execute = {name: meta["execute"] for name, meta in agent.TOOLS.items()}
    specs = deep.install_deep_tool_overrides(agent.TOOLS)
    assert specs["search_books"]["execute"] is deep.search_books
    assert specs["concept_trace"]["execute"] is deep.concept_trace
    assert specs["philosopher_debate"]["execute"] is deep.philosopher_debate
    specs["philosopher_debate"]["parameters"]["properties"]["speakers"]["description"] = "changed copy"
    for name, meta in agent.TOOLS.items():
        assert meta["execute"] is old_execute[name]
        assert meta["parameters"] == before[name]
