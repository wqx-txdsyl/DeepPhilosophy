"""General-agent source cards projected from observed retrieval and answer use."""
import hashlib
import re
from urllib.parse import quote
import evidence_contract as EC


def enrich_citations(citations, evidence, tool_log, answer):
    used = {item.get("evidence_id"): item for item in (evidence or {}).get("used_evidence", [])}
    reads = set()
    scholarly = {}
    for call in tool_log:
        result = call.get("result_full") or {}
        if not isinstance(result, dict) or result.get("error"):
            continue
        if call.get("name") == "get_chapter":
            reads.add((str(result.get("book_id")), str(result.get("chapter_idx"))))
        if call.get("name") == "get_scholarly_source":
            scholarly[result.get("source_record_id")] = result
    out = []
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
        read = (str(citation.get("book_id")), str(citation.get("chapter_idx"))) in reads
        out.append({**citation, "excerpt": item.get("snippet") or "",
                    "access_level": "PASSAGE_READ" if read else "SEARCH_EXCERPT"})
    seen = set()
    normalized = answer.casefold()
    answer_urls = {url.rstrip(".,;，。；") for url in re.findall(r"https?://[^\s)\]<>]+", answer)}
    for call in tool_log:
        result = call.get("result_full") or {}
        if call.get("name") != "websearch" or not isinstance(result, dict) or result.get("error"):
            continue
        for record in result.get("results") or []:
            url = record.get("url") or ""
            if not url.startswith(("https://", "http://")) or url not in answer_urls or url in seen:
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
