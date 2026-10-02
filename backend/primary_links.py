"""Public reading links from actual catalogue coordinates, never guessed chapters."""
import re
from urllib.parse import quote

from routes import agent_core as core

SITE = "https://deepphilosophy.top"


def _normal(value):
    return re.sub(r"\s+", "", str(value or "").replace('\\u3000', ' ')).replace("《", "").replace("》", "").replace("—", "-").replace("–", "-").replace('“', '"').replace('”', '"')


def _edition_base(value):
    return re.sub(r"[（(][^（）()]*[）)]$", "", _normal(value))


def primary_link(book, chapter=""):
    """Resolve navigation only; locating a chapter does not verify a claim or quote.

    Ambiguous editions/titles and missing chapters stay unlinked. In particular,
    there is no vector-search fallback to an unrelated hit or chapter zero.
    """
    from evidence_contract import _split_book_chapter, chapter_locator_match

    book, chapter = _split_book_chapter(book, chapter)
    books = [b for b in core.get_books() if _normal(b.get("title")) == _normal(book)]
    if not books:
        books = [b for b in core.get_books() if _edition_base(b.get("title")) == _normal(book)]
    if not book or len(books) != 1:
        return None
    bid = books[0]["id"]
    if not chapter.strip():
        return f"{SITE}/book/{quote(bid, safe='')}"
    wanted = _normal(chapter)
    targets = set()
    short_targets = set()
    meta = core.chapter_meta(bid) or {}
    for pos, item in enumerate(meta.get("toc") or []):
        if not isinstance(item, dict):
            item = {"title": item, "index": pos}
        actual = _normal(item.get("title"))
        exact = actual == wanted
        short = bool(re.fullmatch(r"第[一二三四五六七八九十百千零〇两\d]+[卷编章篇讲节]", wanted) and actual.startswith(wanted))
        short = short or (item.get('type') != 'section' and chapter_locator_match(item.get('title'), chapter) is True)
        if item.get("type") == "part" or not (exact or short):
            continue
        idx = item.get("index")
        if isinstance(idx, int) and not isinstance(idx, bool) and 0 <= idx < int(meta.get('chapterCount') or 0) and (core.CHAPTERS_DIR / bid / f"{idx}.json").is_file():
            url = f"{SITE}/reader/{quote(bid, safe='')}?ch={idx}"
            # Reader's toc parameter locates a section within a merged chapter.
            if item.get("type") == "section":
                url += f"&toc={pos}"
            (targets if exact else short_targets).add(url)
    if not targets:
        for idx, title in core.block_titles(bid).items():
            if _normal(title) == wanted and 0 <= idx < int(meta.get('chapterCount') or 0):
                targets.add(f"{SITE}/reader/{quote(bid, safe='')}?ch={idx}")
    if not targets:
        targets = short_targets
    return next(iter(targets)) if len(targets) == 1 else None
