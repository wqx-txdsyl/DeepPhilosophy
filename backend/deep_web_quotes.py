"""Explicit URL attribution for quotes from actually read general web passages."""
import re
from urllib.parse import urldefrag

import evidence_contract as EC

WEB_LINK = re.compile(r"\[[^\]\n]*\]\((https?://[^\s)<]+)\)")
BARE_URL = r"https?://[^\s<>()[\]（）【】\"']+"
CAPTION = rf"[（(](?:来源|出处|Source|source|Reference|reference)\s*[:：][^\n()（）]{{0,600}}[)）]"
SOURCE_LINE = (rf"(?:来源|出处|Source|source|Reference|reference)\s*[:：]"
               rf"(?:(?!https?://)[^\n]){{0,300}}{BARE_URL}(?:[\s,，;；、]+{BARE_URL})*")
TOKEN = rf"(?:{EC._CITE_RE.pattern}|{EC._CITE_AUTHOR_WORK_RE.pattern}|{WEB_LINK.pattern}|{CAPTION}|{SOURCE_LINE})"
SEPARATOR = r"[\s.。,，;；:：、]*"


def _urls(text):
    return list(dict.fromkeys(urldefrag(url.rstrip(".,;，。；"))[0] for url in re.findall(BARE_URL, text)))


def inline_urls(tail):
    match = re.match(rf"{SEPARATOR}{TOKEN}(?:{SEPARATOR}{TOKEN})*", tail)
    return _urls(match.group(0)) if match else []


def inline_labels(tail):
    match = re.match(rf"{SEPARATOR}{TOKEN}(?:{SEPARATOR}{TOKEN})*", tail)
    return ([{"book": book, "chapter": chapter} for book, chapter in EC._cite_markers(match.group(0))]
            if match else [])


def split_suffix(body):
    match = re.search(rf"\s*{TOKEN}(?:{SEPARATOR}{TOKEN})*{SEPARATOR}$", body)
    if not match or not _urls(match.group(0)):
        return body, [], []
    markers = [{"book": book, "chapter": chapter} for book, chapter in EC._cite_markers(match.group(0))]
    return body[:match.start()].rstrip(), markers, _urls(match.group(0))


def read_spans(log):
    spans = []
    for index, call in enumerate(log or []):
        result = call.get("result_full") or {}
        if (call.get("name") != "websearch" or not isinstance(result, dict)
                or result.get("mode") != "read" or result.get("error")
                or not isinstance(result.get("text"), str) or not result["text"].strip()):
            continue
        urls = [urldefrag(value)[0] for value in (result.get("url"), result.get("requested_url"))
                if isinstance(value, str) and value.startswith(("https://", "http://"))]
        if not urls:
            continue
        spans.append({"evidence_id": f"qb_web_{index}", "book": None, "title": result.get("title") or urls[0],
                      "chapter": "", "book_id": "", "chapter_idx": -1,
                      "source_type": "web_read", "urls": urls, "units": [result["text"]]})
    return spans


def repair_span(ref, log):
    for span in read_spans(log):
        if span["evidence_id"] != ref:
            continue
        text = span["units"][0]
        starts = list(range(0, max(1, len(text) - 399), 160))
        starts.append(max(0, len(text) - 400))
        return {**span, "units": [text[start:start + 400] for start in dict.fromkeys(starts)]}
    return None
