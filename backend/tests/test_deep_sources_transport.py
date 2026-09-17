import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_sources import enrich_citations
from routes.agent_sse import _heartbeat_stream


def test_primary_cards_distinguish_read_passage_from_search_excerpt():
    citations = [{"evidence_id": "a", "book_id": "one", "chapter_idx": 0, "book": "论语", "chapter": "学而篇"},
                 {"evidence_id": "b", "book_id": "two", "chapter_idx": 2, "book": "道德经", "chapter": "第三章"}]
    evidence = {"used_evidence": [{"evidence_id": "a", "snippet": "实际原句"}]}
    log = [{"name": "get_chapter", "result_full": {"book_id": "one", "chapter_idx": 0, "text": "实际原句"}}]
    result = enrich_citations(citations, evidence, log, "实际原句【《论语》·学而篇】【《道德经》·第三章】")
    assert result[0]["access_level"] == "PASSAGE_READ" and result[0]["excerpt"] == "实际原句"
    assert result[1]["access_level"] == "SEARCH_EXCERPT"
    assert "excerpt" not in citations[0]


def test_keyword_overlap_never_turns_unused_search_candidates_into_citations():
    citations = [{"evidence_id": str(i), "book": book, "chapter": chapter, "used": True}
                 for i, (book, chapter) in enumerate([
                     ("论语", "颜渊篇"), ("论语", "卫灵公篇"), ("大问题", "伦理"),
                     ("庄子说什么", "渔父"), ("康德《实践理性批判》句读", "实践")])]
    result = enrich_citations(citations, {}, [],
                              "己所不欲，勿施于人。【《论语》·颜渊篇】【《论语》·卫灵公篇】")
    assert [(item["book"], item["chapter"]) for item in result] == [
        ("论语", "颜渊篇"), ("论语", "卫灵公篇")]


def test_scholarly_cards_require_actual_read_and_explicit_answer_use():
    record = {"source_record_id": "s1", "title": "A careful argument", "doi": "10.1/test",
              "authors": [{"name": "Author"}]}
    search = {"name": "search_scholarship", "result_full": {"results": [record]}}
    read = {"name": "get_scholarly_source", "result_full": {"source_record_id": "s1",
            "abstract": {"text": "Abstract only."}, "returned_evidence_level": "ABSTRACT_AVAILABLE"}}
    assert enrich_citations([], {}, [search], record["title"]) == []
    assert enrich_citations([], {}, [search, read], "A different topic.") == []
    result = enrich_citations([], {}, [search, read], record["title"])
    assert len(result) == 1 and result[0]["access_level"] == "ABSTRACT_AVAILABLE"
    assert result[0]["excerpt"] == "Abstract only." and result[0]["url"] == "https://doi.org/10.1/test"


def test_web_sources_need_a_returned_url_actually_used_in_the_answer():
    log = [{"name": "websearch", "result_full": {"results": [
        {"title": "One source", "url": "https://example.org/source", "snippet": "A returned excerpt."},
        {"title": "Unused result", "url": "https://example.org/unused", "snippet": "Other text."}]}}]
    result = enrich_citations([], {}, log, "材料见[这一来源](https://example.org/source)。")
    assert len(result) == 1 and result[0]["url"] == "https://example.org/source"
    assert result[0]["access_level"] == "SEARCH_EXCERPT"
    assert enrich_citations([], {}, log, "https://example.org/source-fabricated") == []


def test_heartbeat_is_not_a_fabricated_thinking_event():
    async def run():
        async def events():
            await asyncio.sleep(0.012)
            yield {"type": "done", "content": "complete"}
        return [frame async for frame in _heartbeat_stream(events(), interval=0.003)]
    frames = asyncio.run(run())
    assert frames[0] == ": keep-alive\n\n"
    assert json.loads(frames[-1][6:])["type"] == "done"
    assert all(frame.startswith(":") for frame in frames[:-1])


def test_closing_heartbeat_cancels_pending_model_generation():
    closed = []
    async def run():
        async def events():
            try:
                await asyncio.sleep(30)
                yield {"type": "done"}
            finally:
                closed.append(True)
        stream = _heartbeat_stream(events(), interval=0.001)
        assert (await anext(stream)).startswith(":")
        await stream.aclose()
    asyncio.run(run())
    assert closed == [True]
