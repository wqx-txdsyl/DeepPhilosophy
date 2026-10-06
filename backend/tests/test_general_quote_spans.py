"""Deep philosophy opt-in quote boundaries, grounded in the live Analects failure."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import final_validator as FV
import quote_bound as QB


FIRST = "子曰：“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？”"
LAST = "子曰：“不患人之不己知，患不知人也。”"
LABEL = "【《论语》·学而篇】"


def read_log(text=FIRST + "\n" + LAST, *, title="学而篇", book="论语", bid="analects"):
    return [{"name": "get_chapter", "args": {"book_id": bid, "chapter_idx": 2},
             "result_full": {"book_id": bid, "book_title": book, "chapter_idx": 2,
                             "title": title, "text": text}}]


def validate(answer, log=None, **kwargs):
    return FV.validate_final_candidate(answer, raw_tool_log=read_log() if log is None else log,
                                       strict_quote_spans=True, **kwargs)


@pytest.mark.parametrize("quote,legacy_code", [
    (FIRST, FV.NEAR_QUOTE_NOT_MARKED),
    (LAST, FV.UNSUPPORTED_EXACT_QUOTE),
])
def test_live_analects_false_rejection_fixed_only_when_enabled(quote, legacy_code):
    candidate = f"> {quote}{LABEL}"
    old = FV.validate_final_candidate(candidate, raw_tool_log=read_log())
    assert legacy_code in {issue.code for issue in old.issues}
    enabled = validate(candidate)
    assert enabled.ok, enabled.as_dict()
    assert enabled.verified_citations == 1
    assert enabled.quote_audit["entries"][0]["verification_state"] == "VERIFIED_EXACT"


@pytest.mark.parametrize("tail", [
    LABEL, " " + LABEL, "\n> " + LABEL, "\n>\n> " + LABEL,
    "【《论语·学而篇》】", "【孔子·《论语》】", LABEL + " 【《论语》】",
])
def test_source_marker_formatting_does_not_become_quoted_words(tail):
    candidate = f"> {FIRST}{tail}"
    result = validate(candidate)
    assert result.ok, result.as_dict()
    block = QB.extract_quotes(candidate, strict_quote_spans=True)[0]
    assert block["text"] == FIRST
    # Repair tooling can still locate the full original block, including labels.
    assert candidate[block["char_start"]:block["char_end"]] == candidate


def test_unknown_source_label_is_not_erased_from_validation():
    result = validate(f"> {FIRST}【《不存在的书》·第一章】")
    assert not result.ok
    assert FV.UNVERIFIED_CITATION in {issue.code for issue in result.issues}


def test_true_quote_cannot_borrow_another_read_books_label():
    log = read_log() + read_log("道可道，非常道。名可名，非常名。", title="第一章", book="道德经", bid="dao")
    result = validate(f"> {FIRST}【《道德经》·第一章】", log)
    assert not result.ok
    assert result.verified_citations == 1
    assert FV.UNSUPPORTED_EXACT_QUOTE in {issue.code for issue in result.issues}


def test_every_attached_label_must_support_the_quote():
    log = read_log() + read_log("道可道，非常道。名可名，非常名。", title="第一章", book="道德经", bid="dao")
    result = validate(f"> {FIRST}{LABEL}【《道德经》·第一章】", log)
    assert not result.ok
    assert result.verified_citations == 2


@pytest.mark.parametrize("quote", [
    "孔子教导我们每天学习就会获得财富与荣耀。",
    "学习应该温故知新，远方朋友到来值得高兴，被人误解也不生气。",
])
def test_fabrication_and_paraphrase_disguised_as_verbatim_still_fail(quote):
    result = validate(f"> {quote}{LABEL}")
    assert not result.ok
    assert FV.UNSUPPORTED_EXACT_QUOTE in {issue.code for issue in result.issues}


def test_approximate_wording_still_requires_disclosure():
    near = FIRST.replace("时习之", "时常复习之")
    result = validate(f"> {near}{LABEL}")
    assert not result.ok
    assert FV.NEAR_QUOTE_NOT_MARKED in {issue.code for issue in result.issues}


def test_stitched_passages_remain_rejected_with_a_real_source_label():
    first = "闵子侍侧，訚訚如也；子路，行行如也；冉有、子贡，侃侃如也。"
    last = "鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”子曰：“夫人不言，言必有中。”"
    result = validate(
        "> 闵子侍侧，訚訚如也。夫人不言，言必有中。【《论语》·先进篇】",
        read_log(first + "\n" + last, title="先进篇"))
    assert not result.ok
    assert FV.STITCHED_QUOTE in {issue.code for issue in result.issues}


def test_interior_citation_is_not_removed_to_join_fragments():
    candidate = "> 学而时习之【《论语》·学而篇】，不亦说乎？有朋自远方来，不亦乐乎？"
    quote = QB.extract_quotes(candidate, strict_quote_spans=True)[0]
    assert LABEL in quote["text"]
    assert not validate(candidate).ok


def test_text_after_citation_does_not_escape_verification():
    candidate = f"> {FIRST}{LABEL}所以成功者应当永远统治失败者。"
    assert not validate(candidate).ok


def test_no_read_evidence_still_rejects_genuine_but_unverified_words():
    assert not validate(f"> {FIRST}{LABEL}", []).ok


def test_default_audit_and_opt_out_are_identical_for_philosopher_compatibility():
    candidate = f"> {FIRST}{LABEL}\n\n解释如下。"
    log = read_log()
    assert QB.extract_quotes(candidate) == QB.extract_quotes(candidate, strict_quote_spans=False)
    assert QB.audit_quotes(candidate, log) == QB.audit_quotes(candidate, log, strict_quote_spans=False)
    assert FV.validate_final_candidate(candidate, raw_tool_log=log) == FV.validate_final_candidate(
        candidate, raw_tool_log=log, strict_quote_spans=False)


@pytest.mark.parametrize("quote_marks", [("“", "”"), ('"', '"')])
def test_inline_verbatim_quote_cannot_borrow_another_read_books_label(quote_marks):
    left, right = quote_marks
    quoted = "学而时习之，不亦说乎？有朋自远方来，不亦乐乎？"
    candidate = f"原文写道：{left}{quoted}{right}【《道德经》·第一章】"
    log = read_log() + read_log("道可道，非常道。名可名，非常名。", title="第一章", book="道德经", bid="dao")
    assert FV.validate_final_candidate(candidate, raw_tool_log=log).ok  # Persona contract is unchanged.
    result = validate(candidate, log)
    assert not result.ok and result.verified_citations == 1
    assert FV.UNSUPPORTED_EXACT_QUOTE in {issue.code for issue in result.issues}


@pytest.mark.parametrize("tail", [LABEL, " " + LABEL, LABEL + "【孔子·《论语》】"])
def test_inline_verbatim_quote_accepts_only_its_supporting_labels(tail):
    candidate = f"孔子曰：\"学而时习之，不亦说乎？有朋自远方来，不亦乐乎？\"{tail}"
    assert validate(candidate).ok
    quote = QB.extract_quotes(candidate, strict_quote_spans=True)[0]
    assert quote["citation_labels"]
    assert candidate[quote["char_start"]:quote["char_end"]].startswith('"')


def test_inline_quote_checks_every_adjacent_label_but_not_a_later_prose_citation():
    quote = "孔子曰：\"学而时习之，不亦说乎？有朋自远方来，不亦乐乎？\""
    other = "【《道德经》·第一章】"
    log = read_log() + read_log("道可道，非常道。名可名，非常名。", title="第一章", book="道德经", bid="dao")
    assert not validate(quote + LABEL + other, log).ok
    assert validate(quote + LABEL + "这里再讨论另一部书：" + other, log).ok


@pytest.mark.parametrize("candidate", [
    "生病的伴侣确实该被照顾，他说“我今天撑不住，你留下好吗”不是勒索。",
    '假设一个人问道：“你能把这本书借我几天吗？”这只是一个请求。',
    'For example, a friend says: "Could you stay with me for a while?" This is a request.',
])
def test_general_example_dialogue_does_not_claim_a_literary_source(candidate):
    # Ordinary generic-role dialogue makes no claim to quote a retrieved work.
    assert validate(candidate, []).ok


@pytest.mark.parametrize("candidate", [
    "例如孔子曰：“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？”",
    "生病的伴侣复述原文，他说“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？”",
    "一个人说：“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？”" + LABEL,
    "朋友读着《论语》，他说“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？”",
    "他说“学而时习之，不亦说乎？有朋自远方来，不亦乐乎？”",
])
def test_example_context_never_exempts_explicit_or_unresolved_source_attribution(candidate):
    assert not validate(candidate, []).ok


def test_example_speech_exemption_does_not_change_persona_parser():
    candidate = "生病的伴侣确实该被照顾，他说“我今天撑不住，你留下好吗”不是勒索。"
    assert not FV.validate_final_candidate(candidate, raw_tool_log=[]).ok
    assert validate(candidate, []).ok
