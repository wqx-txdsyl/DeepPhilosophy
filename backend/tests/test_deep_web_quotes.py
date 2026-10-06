import json
import pytest

import final_validator as validator
import quote_bound as quotes

WORDS = "A criterion of identity must distinguish continuity from mere similarity."
URL = "https://example.org/identity"


def log(text=WORDS, url=URL):
    return [{"name": "websearch", "result_full": {"mode": "read", "url": url,
        "requested_url": url, "title": "Identity", "text": text, "access_level": "WEB_PASSAGE_READ"}}]


def check(answer, evidence=None):
    return validator.validate_final_candidate(answer, raw_tool_log=log() if evidence is None else evidence,
                                               strict_quote_spans=True)


@pytest.mark.parametrize("answer", [f"> {WORDS} [source]({URL})", f"> {WORDS}\n\n[source]({URL})",
    f'原文写道：“{WORDS}”[source]({URL}#section)', f'"{WORDS}"[source]({URL})',
    f'> {WORDS}\n\n（来源：Example Reference, "Identity", {URL}）',
    f'原文写道：“{WORDS}”。（来源：Example, {URL}）',
    f'> {WORDS}\n\n来源：Example, {URL}'])
def test_read_web_quote_has_real_url_bound_evidence(answer):
    result = check(answer)
    assert result.ok, result.as_dict()
    assert any(entry["verification_state"] == "VERIFIED_EXACT" for entry in result.quote_audit["entries"])


def test_web_discovery_and_failed_reads_do_not_support_verbatim_quotes():
    evidence = [{"name": "websearch", "result_full": {"results": [{"url": URL, "snippet": WORDS}]}},
                {"name": "websearch", "result_full": {"mode": "read", "url": URL, "text": WORDS, "error": "DENIED"}}]
    assert not check(f"> {WORDS} [source]({URL})", evidence).ok


def test_genuine_quote_cannot_borrow_another_read_webpages_url():
    other = "https://example.org/other"
    evidence = log() + log("An unrelated text about a different subject.", other)
    assert not check(f"> {WORDS} [wrong]({other})", evidence).ok
    assert not check(f"> {WORDS} [source]({URL}) [wrong]({other})", evidence).ok
    assert not check(f'原文写道：“{WORDS}”。（来源：Wrong Source, {other}）', evidence).ok


@pytest.mark.parametrize("separator", ["。 ", ". ", "；", ": "])
def test_sentence_punctuation_does_not_detach_web_quote_from_its_url(separator):
    candidate = f'原文写道：“{WORDS}”{separator}[source]({URL})'
    assert check(candidate).ok
    evidence = log("Completely different words.") + [{"name": "get_chapter", "result_full": {
        "book_id": "local", "chapter_idx": 0, "book_title": "Local book", "title": "Chapter", "text": WORDS}}]
    assert not check(candidate, evidence).ok


@pytest.mark.parametrize("separator", [", ", "，", "; ", "；", "、"])
def test_punctuation_between_sources_does_not_hide_a_false_second_attribution(separator):
    other = "https://example.org/other"
    evidence = log() + log("An unrelated source without the quoted words.", other)
    links = f"[A]({URL}){separator}[B]({other})"
    assert not check(f'原文写道：“{WORDS}”{links}', evidence).ok
    assert not check(f"> {WORDS} {links}", evidence).ok


def test_source_line_binds_every_listed_url():
    other = "https://example.org/other"
    evidence = log() + log("Unrelated content.", other)
    assert not check(f"> {WORDS}\n\n来源：{URL}, {other}", evidence).ok
    assert not check(f"> {WORDS} 来源：{URL} This extra quoted claim was never read.", evidence).ok


def test_fabricated_words_and_unattributed_web_quote_are_not_approved():
    assert not check(f"> Every replacement necessarily creates a new person. [source]({URL})").ok
    assert not check(f"> {WORDS}").ok  # A read does not authorize an unattached attribution.


@pytest.mark.parametrize("suffix", ["[source]({url})【《道德经》·第一章】", "【《道德经》·第一章】[source]({url})"])
def test_mixed_web_and_book_attributions_must_each_support_the_words(suffix):
    evidence = log() + [{"name": "get_chapter", "result_full": {"book_id": "dao", "chapter_idx": 1,
        "book_title": "道德经", "title": "第一章", "text": "道可道，非常道。名可名，非常名。"}}]
    tail = suffix.format(url=URL)
    assert not check(f"> {WORDS}{tail}", evidence).ok
    assert not check(f'原文写道：“{WORDS}”{tail}', evidence).ok


def test_text_after_a_link_does_not_escape_quote_validation():
    candidate = f"> {WORDS} [source]({URL}) This extra sentence is not in the source."
    assert not check(candidate).ok


def test_default_persona_validator_is_unchanged_by_web_read_metadata():
    candidate = f"> {WORDS} [source]({URL})"
    assert quotes.extract_quotes(candidate) == quotes.extract_quotes(candidate, strict_quote_spans=False)
    assert not validator.validate_final_candidate(candidate, raw_tool_log=log()).ok
    assert check(candidate).ok


def test_web_quote_repair_gets_relevant_text_and_url_without_inventing_a_book():
    import engine_langgraph as engine
    import repair_context as repair
    actual = "A person's persistence cannot be established by merely renaming resemblance as numerical identity."
    evidence = log("Introductory context. " * 60 + actual + " Later material. " * 20)
    near = actual.replace("merely renaming", "simply renaming")
    answer = f"> {near} [source]({URL})"
    result = check(answer, evidence)
    assert not result.ok
    issue = next(issue for issue in result.issues if issue.code == "NEAR_QUOTE_NOT_MARKED")
    assert issue.evidence_ref == "qb_web_0"
    packet = engine._build_repair_evidence_packet(result, evidence)["available_evidence"][0]
    assert actual in packet["SOURCE_EXACT_CONTEXT"] and packet["SOURCE_URL"] == URL
    assert packet["SOURCE_BOOK"] is None
    bundles = repair.build_repair_issue_bundles(answer, result, evidence)
    source = bundles[0]["source"]
    assert source["url"] == URL and actual in source["exact_context"]
    anchor = bundles[0]["anchor"]
    assert answer[anchor["content_start"]:anchor["content_end"]] == near
    catalog = repair.build_slice_catalog(bundles, near)
    selected = next(item for item in catalog["vi_1"] if actual.strip() == item["text"].strip())
    # Copying corrected words must preserve the source URL and remain verifiable.
    patched, errors = repair.apply_main_agent_patches_v2(answer, json.dumps({"patches": [
        {"issue_id": "vi_1", "action": "COPY_SLICE", "slice_id": selected["slice_id"]}]}), bundles, catalog)
    assert not errors and check(patched, evidence).ok and URL in patched


@pytest.mark.parametrize("needs_repair", [False, True])
def test_real_general_graph_reads_cites_and_repairs_web_quotes_with_context(monkeypatch, needs_repair):
    import asyncio
    from langchain_core.tools import StructuredTool
    import engine_langgraph as engine
    from tests.test_deep_streaming_delivery import install, successful_done
    source = log()[0]["result_full"]
    tool = StructuredTool.from_function(name="websearch", description="public page fixture",
                                       func=lambda url: source)
    final = f"> {WORDS} [source]({URL})"
    bad = final.replace("distinguish continuity", "always distinguish continuity")
    script = [{"tool_calls": [{"name": "websearch", "args": {"url": URL}, "id": "web-1"}]},
              {"parts": [f"<answer>{bad if needs_repair else final}</answer>"]}]
    if needs_repair:
        script.append({"parts": [f"<answer>{final}</answer>"]})
    install(monkeypatch, script, [tool])
    contexts = []
    invoke = engine._agent_llm_invoke
    async def observe(agent, messages, *args, **kwargs):
        contexts.append(messages)
        return await invoke(agent, messages, *args, **kwargs)
    monkeypatch.setattr(engine, "_agent_llm_invoke", observe)
    async def run():
        return [event async for event in engine.stream_agent("请实际读取网页并引用一句原文，不加延伸建议。", [], agent="general")]
    events = asyncio.run(run())
    done = successful_done(events)
    assert len(done["citations"]) == 1 and done["citations"][0]["access_level"] == "WEB_PASSAGE_READ"
    assert done["content"] == final
    assert done["validation"]["repairs_used"] == int(needs_repair)
    if needs_repair:
        assert any(getattr(message, "type", "") == "tool" and WORDS in message.content for message in contexts[-1])
