import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from deep_quote_verify import verify_quote
from routes import agent_core as core


@pytest.fixture
def book(monkeypatch):
    import deep_quote_verify as verify
    meta={'id':'0123456789ab','title':'原典','author':'作者'}
    chapters=[(0,'首章','前文。人不知而不愠，不亦君子乎？后文。'),(1,'次章','相近意思的另一句话。')]
    monkeypatch.setattr(verify,'_book_lookup',lambda _: (meta,None))
    monkeypatch.setattr(verify,'_chapters',lambda _: iter(chapters))
    monkeypatch.setattr(core,'chapter_meta',lambda _: {'chapterCount':2})
    return chapters


def test_exact_and_negative_are_distinct_from_semantic_resemblance(book):
    found=verify_quote({'book_id':'原典','quote':'人不知而不愠，不亦君子乎'})
    assert found['found'] and found['matches'][0]['match_mode']=='exact'
    hit=found['matches'][0];text=book[0][2]
    assert hit['matched_text']==text[hit['match_start']:hit['match_end']]
    assert hit['text']==text[hit['excerpt_start']:hit['excerpt_end']]
    absent=verify_quote({'book_id':'原典','quote':'别人不了解我也不生气'})
    assert not absent['found'] and absent['coverage']['searched_chapters']==2
    from deep_sources import primary_research
    research=primary_research([],[{'name':'verify_quote','result_full':absent}],'未找到')
    assert research['status']=='no_quote_match' and research['quote_checks'][0]['found'] is False


def test_whitespace_is_explicit_and_no_unreadable_absence_claim(book):
    book[0]=(0,'首章','人不知而\n不愠，不亦君子乎？')
    result=verify_quote({'book_id':'原典','quote':'人不知而不愠，不亦君子乎'})
    assert result['matches'][0]['match_mode']=='whitespace_only'
    book[:]=[(0,'空章','')]
    assert verify_quote({'book_id':'原典','quote':'不存在'})['error']=='NO_LOCAL_TEXT'


def test_actual_read_enters_citation_validation_and_source_cards(book):
    from final_validator import validate_final_candidate
    from deep_sources import enrich_citations,primary_research
    import evidence_contract as evidence
    import quote_bound
    result=verify_quote({'book_id':'原典','quote':'人不知而不愠，不亦君子乎'})
    log=[{'name':'verify_quote','result_full':result}]
    text='“人不知而不愠，不亦君子乎”【《原典》·首章】'
    assert validate_final_candidate(text,raw_tool_log=log,strict_quote_spans=True).ok
    source=primary_research([],log,text)['sources'][0]
    assert source['access_level']=='PASSAGE_READ'
    assert len({s['evidence_id'] for s in quote_bound.evidence_spans(log)})==1


def test_quotation_in_body_precedes_same_words_in_contents(book):
    quotation='人不知而不愠，不亦君子乎'
    book[:]=[(0,'目录',quotation),(1,'学而',quotation)]
    result=verify_quote({'book_id':'原典','quote':quotation,'limit':1})
    assert result['match_count']==2 and result['matches'][0]['title']=='学而'
