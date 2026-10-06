"""General-agent source cards projected from observed retrieval and answer use."""
import hashlib
import re
from urllib.parse import quote, urldefrag
import evidence_contract as EC


def _source_key(item):
    return (str(item.get("book_id")), str(item.get("chapter_idx"))) if item.get("book_id") else (item.get("book"), item.get("chapter"))


def _read_results(tool_log):
    for call in tool_log:
        result=call.get('result_full')
        if not isinstance(result,dict) or result.get('error'):continue
        if call.get('name')=='get_chapter' and result.get('text'):yield result
        if call.get('name')=='verify_quote':
            yield from (item for item in result.get('matches',[]) if isinstance(item,dict) and item.get('text'))


def _read_details(tool_log):
    return {_source_key(result):{k:result[k] for k in
            ('material_role','role_basis','chapter_text_length','reader_coordinate_valid') if k in result}
            for result in _read_results(tool_log)}


def _focused_excerpt(text, answer):
    """Choose an actual source window around a quoted passage, never rewrite it."""
    for quoted in re.findall(r'[“「『"]([^”」』"\n]{6,400})[”」』"]', answer or ""):
        offset = text.find(quoted)
        if offset >= 0:
            start = max(0, offset - 80)
            return text[start:start + 600]
    return text[:600]


def primary_research(citations, tool_log, answer):
    """Actual primary retrieval, kept distinct from the answer's used citations."""
    calls = [c for c in tool_log if c.get("name") in {"search_books", "get_chapter", "verify_quote"}]
    used = {_source_key(c) for c in citations if c.get("book_id") or c.get("book")}
    sources = {}
    details = _read_details(calls)
    quoted = re.findall(r'[“「『"]([^”」』"\n]{6,400})[”」』"]', answer or '')
    read_scores = {}
    for item in EC.build_evidence_pool(calls):
        if item["kind"] not in {"search", "chapter"} or not item.get("book"):
            continue
        key = _source_key(item)
        score = sum(len(q) for q in quoted if q in (item.get('text') or ''))
        if key in sources and sources[key]["access_level"] == "PASSAGE_READ":
            if item['kind'] != 'chapter' or score <= read_scores.get(key,0):
                continue
        sources[key] = {k: item[k] for k in ("book", "chapter", "book_id", "chapter_idx", "author")}
        sources[key].update(source_type="primary", used=key in used,
                            excerpt=_focused_excerpt(item.get("text") or "", answer),
                            access_level="PASSAGE_READ" if item["kind"] == "chapter" else
                            "SEARCH_EXCERPT" if (item.get('text') or '').strip() else "METADATA_ONLY")
        sources[key].update(details.get(key,{}))
        if item['kind']=='chapter':read_scores[key]=score
    failed = any(isinstance(c.get("result_full"), dict) and c["result_full"].get("error") for c in calls)
    checks = [{k:c['result_full'].get(k) for k in ('book_id','book_title','quote','found','match_count','coverage')}
              for c in calls if c.get('name')=='verify_quote' and isinstance(c.get('result_full'),dict) and not c['result_full'].get('error')]
    status = "complete" if sources else "failed" if failed else "empty" if calls else "not_requested"
    if not sources and checks and all(check['found'] is False for check in checks):status='no_quote_match'
    ordered = sorted(sources.values(), key=lambda s: (not s["used"], s["access_level"] != "PASSAGE_READ"))
    return {"status": status, "sources": ordered[:20], "total": len(ordered), 'quote_checks':checks}


def enrich_citations(citations, evidence, tool_log, answer):
    used = {item.get("evidence_id"): item for item in (evidence or {}).get("used_evidence", [])}
    reads = {}
    for result in _read_results(tool_log):
        reads.setdefault(_source_key(result), []).append(result['text'])
    quoted = list(dict.fromkeys(re.findall(r'[“「『"]([^”」』"\n]{6,400})[”」』"]', answer or "")))
    scholarly = {}
    for call in tool_log:
        result = call.get("result_full") or {}
        if not isinstance(result, dict) or result.get("error"):
            continue
        if call.get("name") == "get_scholarly_source":
            scholarly[result.get("source_record_id")] = result
    out = []
    details = _read_details(tool_log)
    markers = EC._cite_markers(answer)
    for citation in citations:
        item = used.get(citation.get("evidence_id"), {})
        book = citation.get("book") or ""
        chapter = citation.get("chapter") or ""
        explicitly_cited = any(EC._book_match(book, source_book)
                               and EC._chapter_match(chapter, source_chapter)
                               for source_book, source_chapter in markers)
        explicitly_named = bool(book and f"《{book}》" in answer
                                and (not chapter or chapter in answer))
        if not explicitly_cited and not explicitly_named:
            continue  # Lexical overlap with a retrieved snippet is not answer attribution.
        key = _source_key(citation)
        read = key in reads
        fragments = reads.get(key) or [item.get("snippet") or ""]
        excerpt = max(fragments, key=lambda text: sum(len(q) for q in quoted if q in text))
        out.append({**citation, "excerpt": _focused_excerpt(excerpt, answer),
                    "quoted_passages": [q for q in quoted if read and any(q in text for text in fragments)],
                    "access_level": "PASSAGE_READ" if read else "SEARCH_EXCERPT" if excerpt.strip() else "METADATA_ONLY",
                    **details.get(key,{})})
    # A literal quotation attributed to a named book is actual source use even
    # without the optional 【book·chapter】 marker. Require a unique read source,
    # exact passage matching and an explicit book name; topic overlap is insufficient.
    named_books = re.findall(r'《([^》]+)》', answer or "")
    eligible = {}
    for source in EC.build_evidence_pool(tool_log):
        if source['kind'] == 'chapter' and source.get('book_id') and any(EC._book_match(source['book'], name) for name in named_books):
            eligible.setdefault(_source_key(source), source)
    unmarked = set()
    for q in quoted:
        if len(q) < 12:
            continue
        matches = [key for key in eligible if any(q in text for text in reads.get(key, []))]
        if len(matches) == 1:
            unmarked.add(matches[0])
    present = {_source_key(c) for c in out}
    for key, source in eligible.items():
        if key not in unmarked or key in present:
            continue
        fragments = reads[key]
        excerpt = max(fragments, key=lambda text: sum(len(q) for q in quoted if q in text))
        out.append({k: source[k] for k in ('book', 'chapter', 'book_id', 'chapter_idx', 'author')})
        out[-1].update(evidence_id='read_' + hashlib.sha256(repr(key).encode()).hexdigest()[:12],
                       used=True, source_type='primary', access_level='PASSAGE_READ',
                       excerpt=_focused_excerpt(excerpt, answer),
                       quoted_passages=[q for q in quoted if any(q in text for text in fragments)])
        out[-1].update(details.get(key,{}))
    seen = set()
    normalized = answer.casefold()
    answer_url_order = list(dict.fromkeys(urldefrag(url.rstrip(".,;，。；\"'"))[0]
                                         for url in re.findall(r"https?://[^\s()\[\]<>（）【】\"']+", answer)))
    answer_urls = set(answer_url_order)
    # A successful URL read is stronger evidence than a search snippet. Keep
    # source identity tied to the real final URL, including redirected aliases.
    web_reads = {}
    for call in tool_log:
        result = call.get("result_full") or {}
        if (call.get("name") == "websearch" and isinstance(result, dict) and not result.get("error")
                and result.get("mode") == "read" and isinstance(result.get("text"), str) and result["text"].strip()):
            for url in (result.get("url"), result.get("requested_url")):
                if isinstance(url, str) and url.startswith(("https://", "http://")):
                    web_reads.setdefault(urldefrag(url)[0], result)

    def append_web_read(read):
        url = read.get("url") or ""
        if not url.startswith(("https://", "http://")) or url in seen:
            return
        out.append({"evidence_id": "web_" + hashlib.sha256(url.encode()).hexdigest()[:12],
                    "source_type": "web", "used": True, "title": read.get("title") or url,
                    "url": url, "excerpt": read["text"][:600], "access_level": "WEB_PASSAGE_READ",
                    "content_hash": read.get("content_hash"), "document_truncated": read.get("document_truncated", False)})
        seen.add(url)

    for url in answer_url_order:
        if url in web_reads:
            append_web_read(web_reads[url])
    for call in tool_log:
        result = call.get("result_full") or {}
        if call.get("name") != "websearch" or not isinstance(result, dict) or result.get("error"):
            continue
        for record in result.get("results") or []:
            url = record.get("url") or ""
            if not url.startswith(("https://", "http://")) or url not in answer_urls or url in seen:
                continue
            if urldefrag(url)[0] in web_reads:
                append_web_read(web_reads[urldefrag(url)[0]])
                continue
            snippet = record.get("snippet") or ""
            out.append({"evidence_id": "web_" + hashlib.sha256(url.encode()).hexdigest()[:12],
                        "source_type": "web", "used": True, "title": record.get("title") or url,
                        "url": url, "excerpt": snippet[:600],
                        "access_level": "SEARCH_EXCERPT" if snippet else "WEB_DISCOVERY_ONLY"})
            seen.add(url)
    for call in tool_log:
        result = call.get("result_full") or {}
        if call.get("name") != "search_scholarship" or not isinstance(result, dict):
            continue
        for record in result.get("results") or []:
            sid = record.get("source_record_id")
            title, doi = record.get("title") or "", record.get("doi") or ""
            read = scholarly.get(sid)
            # Search candidates stay hidden. A card requires a real read AND an
            # explicit title/DOI in the final answer, not merely a similar topic.
            if sid in seen or not read or not ((len(title) >= 8 and title.casefold() in normalized)
                                              or (doi and doi.casefold() in normalized)):
                continue
            abstract = (read.get("abstract") or {}).get("text") or ""
            passages = read.get("evidence_passages") or []
            excerpt = next((p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in passages if p), "") or abstract
            if not excerpt:
                continue
            authors = record.get("authors") or []
            author_names = [a.get("name", "") if isinstance(a, dict) else str(a) for a in authors]
            out.append({"evidence_id": "sch_" + hashlib.sha256(str(sid).encode()).hexdigest()[:12],
                        "source_record_id": sid, "source_type": "scholarly", "used": True,
                        "title": title, "book": title, "author": ", ".join(author_names),
                        "year": record.get("year"), "doi": doi,
                        "url": "https://doi.org/" + quote(doi, safe="/") if doi else record.get("url"),
                        "access_level": read.get("returned_evidence_level") or read.get("access_level_after"),
                        "excerpt": excerpt[:600]})
            seen.add(sid)
    return out
