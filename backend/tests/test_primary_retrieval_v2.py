"""Primary text identity, source coordinates and honest relaxed retrieval."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
import deep_agent_tools as deep
from routes import agent_core as core


@pytest.fixture
def corpus(tmp_path,monkeypatch):
    bid='0123456789ab'
    root=tmp_path/bid;root.mkdir()
    books=[{'id':bid,'title':'原典','author':'作者甲'}]
    monkeypatch.setattr(core,'CHAPTERS_DIR',tmp_path)
    monkeypatch.setattr(core,'get_books',lambda:books)
    monkeypatch.setattr(core,'book_by_id',lambda b:books[0] if b==bid else None)
    monkeypatch.setenv('PHI_RESEARCH_DB_ENABLED','0')
    core._CHAPTER_INDEX.clear();core._CHAPTER_TEXTS.clear();deep._lexical_search.cache_clear()
    (root/'meta.json').write_text(json.dumps({'chapterCount':1,'chapterTitles':['错误的元数据标题']}))
    (root/'1.json').write_text(json.dumps({'index':7,'title':'真正第一章','content':[{'type':'text','value':'知性规定自然的立法条件。因果关系有必然性。'}]}))
    (root/'310.json').write_text(json.dumps({'title':'最后一章','content':[{'type':'text','value':'后部实际原文'}]}))
    yield bid,root
    core._CHAPTER_INDEX.clear();core._CHAPTER_TEXTS.clear();deep._lexical_search.cache_clear()


def test_real_files_override_stale_count_titles_and_embedded_index(corpus):
    bid,_=corpus
    detail=deep.get_book_detail({'book_id':bid})
    assert detail['declared_chapter_count']==1 and detail['chapterCount']==2
    assert [c['index'] for c in detail['chapters']]==[1,310]
    assert detail['chapters'][0]['title']=='真正第一章'
    assert deep.get_chapter({'book_id':bid,'chapter_idx':1})['title']=='真正第一章'
    assert deep.search_books({'query':'后部实际原文','book_id':bid})['results'][0]['chapter_idx']==310


def test_segmented_query_is_candidate_not_exact_quote(corpus):
    bid,_=corpus
    result=deep.search_books({'query':'知性为自然立法','book_id':bid})
    assert result['method']=='segmented_candidate'
    assert result['results'][0]['read_args']['book_id']==bid
    assert result['results'][0]['match_type']!='exact_passage'
    read=deep.get_chapter(result['results'][0]['read_args'])
    assert '知性规定自然的立法条件' in read['text']


def test_no_loose_match_for_invented_word(corpus):
    bid,_=corpus
    result=deep.search_books({'query':'阿布拉卡达不存在的哲学概念','book_id':bid})
    assert result['method']=='catalogue'
    assert all('chapter_idx' not in r for r in result['results'])


def test_bad_source_is_error_not_a_read(corpus):
    bid,root=corpus
    (root/'1.json').write_text('[]')
    assert deep.get_chapter({'book_id':bid,'chapter_idx':1})['error']=='INVALID_CHAPTER_DATA'
    (root/'1.json').write_text(json.dumps({'title':'空章','content':[]}))
    assert deep.get_chapter({'book_id':bid,'chapter_idx':1})['error']=='EMPTY_CHAPTER_TEXT'


def test_source_role_and_local_proximity():
    assert deep._material_role('康德《实践理性批判》句读','序言')=='COMMENTARY_CANDIDATE'
    assert deep._material_role('纯粹理性批判','译者序')=='EDITORIAL_CANDIDATE'
    assert deep._material_role('尼各马可伦理学[注释导读本]','第八卷')=='UNCLASSIFIED'
    near='知性把规则赋予自然，形成自然的立法。'
    scattered='知性'+('无关的文字'*150)+'自然'+('其他问题'*150)+'立法'
    assert deep._proximity_bonus(near,('知性','自然','立法'))>deep._proximity_bonus(scattered,('知性','自然','立法'))
    assert deep._proximity_bonus('知性。'*600+near,('知性','自然','立法'))>0


def test_book_identity_prefers_exact_and_does_not_guess_between_editions(monkeypatch):
    from routes import agent_tools_retrieval as retrieval
    books=[{'id':'annotated','title':'纯粹理性批判(注释本)','author':'康德'},
           {'id':'plain','title':'纯粹理性批判','author':'康德'}]
    monkeypatch.setattr(retrieval,'get_books',lambda:books)
    monkeypatch.setattr(core,'book_by_id',lambda _:None)
    assert deep._book_lookup('纯粹理性批判')[0]['id']=='plain'
    assert deep._book_lookup('康德')[1]['error']=='AMBIGUOUS_BOOK'
    books.append({'id':'commentary','title':'康德思想研究','author':'康德'})
    assert len(deep._book_lookup('康德')[1]['candidates'])==3


def test_focus_selects_context_with_all_terms_not_repeated_first_term(corpus):
    bid,root=corpus
    text='习惯的讨论。'*600+'知性与因果是本处的关键。'+'后文。'*500
    (root/'1.json').write_text(json.dumps({'title':'第一章','content':[{'type':'text','value':text}]}))
    result=deep.get_chapter({'book_id':bid,'chapter_idx':1,'focus':'习惯 知性 因果'})
    assert '知性与因果' in result['text']
    assert result['text']==text[result['excerpt_start']:result['excerpt_end']]
    assert result['has_previous'] and result['previous_offset'] < result['excerpt_start']


def test_json_fallback_invalidates_text_and_query_caches_on_source_edit(corpus):
    bid,root=corpus
    assert deep.search_books({'query':'后部实际原文','book_id':bid})['method']=='exact_fulltext'
    (root/'310.json').write_text(json.dumps({'title':'更新标题','content':[{'type':'text','value':'新修订内容，仅此一段。'}]}))
    assert deep.search_books({'query':'后部实际原文','book_id':bid})['method']=='catalogue'
    hit=deep.search_books({'query':'新修订内容','book_id':bid})['results'][0]
    assert hit['chapter_title']=='更新标题'


def test_book_catalogue_cache_tracks_canonical_file(tmp_path,monkeypatch):
    path=tmp_path/'books.json';path.write_text(json.dumps([{'id':'one','title':'初始书名'}]))
    monkeypatch.setattr(core,'BOOKS_FILE',path);monkeypatch.setattr(core,'_books_cache',None);monkeypatch.setattr(core,'_books_stamp',None)
    assert core.get_books()[0]['title']=='初始书名'
    path.write_text(json.dumps([{'id':'one','title':'更新后的真实书名'}]))
    assert core.get_books()[0]['title']=='更新后的真实书名'


def test_book_listing_can_reach_books_after_first_twenty(monkeypatch):
    from routes import agent_tools_retrieval as retrieval
    monkeypatch.setattr(retrieval,'get_books',lambda:[{'id':str(i),'title':f'书{i}','author':'甲'} for i in range(25)])
    first=retrieval._exec_list_books({'author':'甲'})
    second=retrieval._exec_list_books({'author':'甲','offset':first['next_offset']})
    assert len(first['books'])==20 and first['has_more']
    assert [b['id'] for b in second['books']]==['20','21','22','23','24'] and not second['has_more']


def test_specific_section_anchor_beats_later_generic_keyword_cluster(corpus):
    bid,root=corpus
    text='B.第二类比。这里是目标论证。'+('无关背景。'*700)+'稍后提到第二类比，原因与结果以及时间序列。'
    (root/'1.json').write_text(json.dumps({'title':'分析论','content':[{'type':'text','value':text}]}))
    result=deep.get_chapter({'book_id':bid,'chapter_idx':1,'focus':'第二类比 原因与结果 时间序列'})
    assert '这里是目标论证' in result['text']
    assert result['focus_locations'][0]['offset']==text.index('第二类比')
