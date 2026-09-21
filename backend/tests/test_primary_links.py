"""Real coordinate resolution and streaming/export parity for reading paths."""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import primary_links as links
from routes import openai_compat as compat


@pytest.fixture
def catalogue(monkeypatch, tmp_path):
    books = [{"id": "0123456789ab", "title": "测试原典"}]
    (tmp_path / books[0]["id"]).mkdir()
    (tmp_path / books[0]["id"] / "3.json").write_text('{}')
    monkeypatch.setattr(links.core, "get_books", lambda: books)
    monkeypatch.setattr(links.core, "CHAPTERS_DIR", tmp_path)
    monkeypatch.setattr(links.core, "chapter_meta", lambda _: {"toc": [
        {"type": "part", "title": "第一部"},
        {"type": "chapter", "title": "真实章节", "index": 3},
        {"type": "section", "title": "节内标题", "index": 3},
        {"type": "chapter", "title": "缺失正文", "index": 4},
    ]})
    monkeypatch.setattr(links.core, "block_titles", lambda _: {3: "合并块标题"})
    return books


def test_real_chapter_section_and_book_links(catalogue):
    assert links.primary_link("测试原典", "真实章节") == "https://deepphilosophy.top/reader/0123456789ab?ch=3"
    assert links.primary_link("测试原典", "节内标题").endswith("?ch=3&toc=2")
    assert links.primary_link("测试原典", "合并块标题").endswith("?ch=3")
    assert links.primary_link("测试原典") == "https://deepphilosophy.top/book/0123456789ab"


@pytest.mark.parametrize("book,chapter", [("测试原典", "不存在"), ("测试", "真实章节"), ("测试原典", "缺失正文"), ("测试原典", "第一部")])
def test_never_guess_chapter_or_another_book(catalogue, book, chapter):
    assert links.primary_link(book, chapter) is None


def test_ambiguous_editions_stay_unlinked(catalogue):
    catalogue.append({"id": "abcdef123456", "title": "测试原典"})
    assert links.primary_link("测试原典", "真实章节") is None


def test_unique_edition_suffix_is_resolved_but_never_arbitrarily_selected(catalogue):
    catalogue[0]['title']='测试原典（全4册）'
    assert links.primary_link('测试原典', '真实章节').endswith('?ch=3')
    catalogue.append({'id':'abcdef123456','title':'测试原典(注释本)'})
    assert links.primary_link('测试原典', '真实章节') is None


@pytest.mark.parametrize("text", [
    "先读【《测试原典》·真实章节】，再读【《测试原典》】。",
    "原典路径：[【《测试原典》·真实章节】](http://127.0.0.1:8011/cite/旧地址)。",
    "| 来源 |\n| --- |\n| 【《测试原典》·节内标题】 |",
    "未知【《测试原典》·不存在】，普通【强调】和[网站](https://example.org)。",
])
def test_all_stream_chunk_boundaries_match_aggregate(catalogue, text):
    expected = compat.convert_cites(text)
    assert "127.0.0.1" not in expected
    for split in range(len(text) + 1):
        out1, buf = compat._convert_buffered(text[:split])
        out2, buf = compat._convert_buffered(buf + text[split:])
        assert out1 + out2 + buf == expected
    out, buf = "", ""
    for char in text:
        part, buf = compat._convert_buffered(buf + char)
        out += part
    assert out + buf == expected
    assert "[[【" not in expected


def test_legacy_redirect_and_api(catalogue):
    redirect = asyncio.run(compat.cite_redirect("测试原典", "真实章节"))
    assert redirect.headers["location"] == "https://deepphilosophy.top/reader/0123456789ab?ch=3"
    missing = asyncio.run(compat.cite_redirect("测试原典", "不存在"))
    assert "error" in missing
    assert asyncio.run(compat.resolve_primary_link("测试原典", "真实章节"))["matched"]
    assert not asyncio.run(compat.resolve_primary_link("测试原典", "不存在"))["matched"]


def test_nested_book_title_and_adjacent_references(catalogue):
    catalogue[0]['title']='康德《实践理性批判》句读'
    text='观点。【《康德《实践理性批判》句读》·真实章节】和【《康德《实践理性批判》句读》】'
    converted=compat.convert_cites(text)
    assert converted.count('https://deepphilosophy.top/') == 2
    assert '/reader/0123456789ab?ch=3' in converted
    assert '/book/0123456789ab' in converted
