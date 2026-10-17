"""A restored book must not rescan or silently damage the rest of the library."""
import importlib.util
import json
from pathlib import Path

import pytest


def fixture_library(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "single_book_sync", Path(__file__).parents[1] / "tools/dp_sync_books.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    public = tmp_path / "app/public"
    detail_dir = public / "book_detail"
    chapter_dir = tmp_path / "backend/data/book_chapters/restored"
    detail_dir.mkdir(parents=True)
    chapter_dir.mkdir(parents=True)

    def write(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    books = [
        {"id": "untouched", "title": "另一部书", "chapterCount": 8, "rank": 81, "custom": {"keep": True}},
        {"id": "restored", "title": "原书名", "chapterCount": 0, "rank": 40, "cover": "/covers/original.webp", "file_type": "txt"},
    ]
    write(public / "books.json", books)
    meta = {"bookId": "restored", "title": "原书名", "author": "作者", "chapterCount": 1, "chapterTitles": ["第一章"], "toc": [{"type": "chapter", "title": "第一章", "index": 0, "level": 1}]}
    write(chapter_dir / "meta.json", meta)
    write(chapter_dir / "0.json", {"index": 0, "title": "第一章", "content": [{"type": "text", "value": "实际正文"}]})
    write(detail_dir / "restored.json", {**meta, "file_type": "epub", "language": "zh-CN", "translator": "译者"})
    for name, value in {
        "BASE": str(tmp_path), "BOOKS_FILE": str(public / "books.json"),
        "PUBLIC_DETAIL_DIR": str(detail_dir), "DETAIL_DIR": str(tmp_path / "backend/data/book_detail"),
        "CATALOG_FILE": str(tmp_path / "backend/data/books_catalog.json"),
    }.items():
        monkeypatch.setattr(module, name, value)
    return module, public, chapter_dir, books


def test_restoring_one_book_preserves_other_entries_and_existing_identity(tmp_path, monkeypatch):
    sync, public, chapter_dir, before = fixture_library(tmp_path, monkeypatch)
    sync.sync_existing_book("restored")
    after = json.loads((public / "books.json").read_text())
    assert after[0] == before[0]
    assert [book["id"] for book in after] == [book["id"] for book in before]
    assert after[1]["rank"] == 40
    assert after[1]["cover"] == "/covers/original.webp"
    assert after[1]["chapterCount"] == 1
    assert after[1]["language"] == "zh-CN"
    for name in ("meta.json", "0.json"):
        assert (public / "backend/data/book_chapters/restored" / name).read_bytes() == (chapter_dir / name).read_bytes()


def test_incomplete_chapter_source_leaves_catalog_and_mirrors_unmodified(tmp_path, monkeypatch):
    sync, public, chapter_dir, _ = fixture_library(tmp_path, monkeypatch)
    before = (public / "books.json").read_bytes()
    (chapter_dir / "0.json").unlink()
    with pytest.raises(ValueError, match="cover precisely"):
        sync.sync_existing_book("restored")
    assert (public / "books.json").read_bytes() == before
    assert not (public / "backend/data/book_chapters/restored").exists()
