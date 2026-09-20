"""Durable research corpus, provenance, reachable evidence and runtime integration."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_store import ResearchStore, digest
from research_ingest import build_library
from research_access import verify_source, identity_match
from research_transport import ResearchHTTPError, fetch_bytes, redact_url, _NoCredentialRedirect
import scholarly_sources as scholarly


@pytest.fixture
def store(tmp_path):
    result=ResearchStore(tmp_path/'research.sqlite3');result.initialize();return result


def record(provider='crossref',doi='10.1234/example',title='Moral Responsibility and Free Will'):
    return scholarly.merge_records([{'provider':provider,'provider_record_id':provider+'-1','doi':doi,'title':title,'authors':[{'name':'A. Scholar'}],'publication_year':2020,'container_title':'Philosophy Journal','publication_type':'JOURNAL_ARTICLE','stable_urls':['https://publisher.example/paper.pdf'],'oa_pdf_url':'https://publisher.example/paper.pdf','oa_candidate_kind':'DIRECT_PDF'}])[0]


def library(root):
    bid='0123456789ab';public=root/'app/public';(public/'book_detail').mkdir(parents=True)
    folder=root/'backend/data/book_chapters'/bid;folder.mkdir(parents=True)
    book={'id':bid,'title':'论语','author':'孔子','chapterCount':2}
    (public/'books.json').write_text(json.dumps([book],ensure_ascii=False))
    (public/'book_detail'/f'{bid}.json').write_text(json.dumps(book))
    (folder/'meta.json').write_text(json.dumps({'chapterCount':2,'chapterTitles':['学而','译者序']}))
    (folder/'0.json').write_text(json.dumps({'title':'学而','content':[{'type':'text','value':'前文。'*500},{'type':'text','value':'学而时习之，不亦说乎？自由思想，认真辨析。'},{'type':'text','value':'后文。'*500}]}))
    (folder/'1.json').write_text(json.dumps({'index':7,'title':'译者序','content':[{'type':'text','value':'这是一段译者说明。'}]}))
    return folder


def test_library_normalizes_only_derived_indexes_and_preserves_source_bytes(store,tmp_path):
    folder=library(tmp_path);before={p:p.read_bytes() for p in tmp_path.rglob('*.json')}
    first=build_library(store,tmp_path)
    assert first['error_count']==0
    assert first['issues_by_code']['MISSING_INDEX_DERIVED_FROM_FILENAME']==1
    assert first['issues_by_code']['EMBEDDED_INDEX_DIFFERS_FROM_FILENAME']==1
    assert all(p.read_bytes()==raw for p,raw in before.items())
    hit=store.search_books('自由')[0]
    assert hit['chapter_idx']==0 and hit['book_title']=='论语'
    assert store.search_books('学而时习')[0]['source_hash']==digest((folder/'0.json').read_bytes())
    with store.connect(readonly=True) as con:
        for p in con.execute('SELECT p.*,c.text AS chapter_text FROM passages p JOIN chapters c ON c.id=p.chapter_id'):
            assert p['text']==p['chapter_text'][p['start_char']:p['end_char']]
        assert con.execute('SELECT material_role FROM chapters WHERE chapter_index=1').fetchone()[0]=='EDITORIAL_CANDIDATE'
        first_id=con.execute('SELECT id FROM passages LIMIT 1').fetchone()[0]
    assert '&sec=' in store.passage(first_id)['reader_url']
    second=build_library(store,tmp_path)
    assert second['counts']['unchanged_chapters']==2
    assert store.stats()['chapters']==2
    assert store.check_integrity()=={'integrity':['ok'],'foreign_key_errors':[]}


def test_changed_or_invalid_source_cannot_leave_old_text_in_search(store,tmp_path):
    folder=library(tmp_path);build_library(store,tmp_path)
    (folder/'0.json').write_text(json.dumps({'index':0,'title':'学而','content':[{'type':'text','value':'更新后的原文。'}]}))
    build_library(store,tmp_path)
    assert store.search_books('自由')==[] and store.search_books('更新后的原文')
    (folder/'0.json').write_text('[]')
    result=build_library(store,tmp_path)
    assert result['error_count']==1 and store.search_books('更新后的原文')==[]
    assert store.stats()['books_by_status']['incomplete']==1


def test_primary_tool_uses_only_current_database_snapshot(store,tmp_path,monkeypatch):
    folder=library(tmp_path);build_library(store,tmp_path)
    monkeypatch.setenv('PHI_RESEARCH_DB_ENABLED','1');monkeypatch.setenv('PHI_RESEARCH_DB_PATH',str(store.path))
    import deep_agent_tools as deep
    from research_bridge import current_library_store
    monkeypatch.setattr(deep.core,'PUBLIC',tmp_path/'app/public')
    assert current_library_store(tmp_path) is not None
    result=deep._exact_results('自由')
    assert result['storage']=='SQLITE_RESEARCH_INDEX'
    assert result['passages'][0]['book_id']=='0123456789ab'
    (folder/'0.json').write_text('{}')
    assert current_library_store(tmp_path) is None


def test_concurrent_provider_merge_retains_every_snapshot_and_doi_identity(store):
    with ThreadPoolExecutor(max_workers=2) as pool:ids=list(pool.map(store.put_source,[record('crossref'),record('openalex')]))
    assert ids[0]==ids[1]
    source=store.source(ids[0])
    assert set(source['record']['provenance']['providers'])=={'crossref','openalex'}
    assert store.stats()['sources']==1 and store.stats()['provider_records']==2
    assert store.search_sources('moral responsibility')[0]['source_id']==ids[0]


def test_backup_is_consistent_and_refuses_overwrite(store,tmp_path):
    sid=store.put_source(record());target=tmp_path/'snapshot.sqlite3';store.backup(target)
    assert ResearchStore(target).source(sid)['title']==record()['title']
    with pytest.raises(FileExistsError):store.backup(target)


def test_verified_passages_keep_page_offsets_and_failure_does_not_erase_history(store):
    sid=store.put_source(record())
    text='Moral Responsibility and Free Will\n\n'+'Responsibility requires a careful account of agency and reasons. '*35
    def response(url,**kwargs):return {'body':b'%PDF-fixture','status':200,'url':url,'content_type':'application/pdf'}
    result=verify_source(store,sid,fetch=response,pdf_parser=lambda _: [text])
    assert result['fulltext_verified'] is True
    source=store.source(sid);e=source['evidence'][0]
    assert e['text']==text[e['locator']['start_char']:e['locator']['end_char']]
    assert e['locator']['pdf_page']==1 and e['check_id']==result['attempts'][0]['check_id']
    def denied(url,**kwargs):raise ResearchHTTPError('ACCESS_DENIED',403)
    again=verify_source(store,sid,fetch=denied)
    assert again['fulltext_verified'] is False
    assert store.source(sid)['checks'][0]['outcome']=='ACCESS_DENIED'
    assert store.source(sid)['evidence']


def test_wrong_pdf_and_plain_landing_page_are_not_fulltext(store):
    sid=store.put_source(record())
    response=lambda url,**kwargs:{'body':b'%PDF-fixture','status':200,'url':url,'content_type':'application/pdf'}
    result=verify_source(store,sid,fetch=response,pdf_parser=lambda _:['An unrelated paper about chemistry. '*100])
    assert not result['fulltext_verified'] and store.source(sid)['evidence']==[]
    html=b'<html><head><title>Moral Responsibility and Free Will</title></head><body>Buy this article to read its contents.</body></html>'
    result=verify_source(store,sid,fetch=lambda url,**kw:{'body':html,'status':200,'url':url,'content_type':'text/html'})
    assert not result['fulltext_verified'] and result['attempts'][0]['outcome']=='LANDING_PAGE_ONLY'


def test_html_pdf_link_is_followed_only_after_document_identity_match(store):
    sid=store.put_source(record());calls=[]
    html=b'<html><head><meta name="citation_title" content="Moral Responsibility and Free Will"><meta name="citation_pdf_url" content="/actual.pdf"></head></html>'
    def fetch(url,**kw):
        calls.append(url)
        return {'body':b'%PDF-fixture' if url.endswith('actual.pdf') else html,'status':200,'url':url,'content_type':'application/pdf' if url.endswith('actual.pdf') else 'text/html'}
    text='Moral Responsibility and Free Will\n\n'+'An actual paragraph about this paper. '*40
    result=verify_source(store,sid,fetch=fetch,pdf_parser=lambda _: [text])
    assert result['fulltext_verified'] and calls[-1]=='https://publisher.example/actual.pdf'


def test_identity_conflict_and_credentials_fail_closed_without_network():
    assert identity_match(record(),'Moral Responsibility and Free Will',declared_doi='10.1234/wrong')[0] is False
    with pytest.raises(ResearchHTTPError,match='CREDENTIAL_DESTINATION_REFUSED'):
        fetch_bytes('https://attacker.example',headers={'Authorization':'Bearer test'})
    with pytest.raises(ResearchHTTPError,match='UNSUPPORTED_RESEARCH_HEADER'):
        fetch_bytes('https://example.org',headers={'Cookie':'secret'})
    with pytest.raises(ResearchHTTPError,match='AUTHENTICATED_REDIRECT_REFUSED'):
        _NoCredentialRedirect().redirect_request(None,None,302,'',{},'https://other.example')
    assert 'secret' not in redact_url('https://api.openalex.org/works?api_key=secret&search=ethics')


def test_runtime_bridge_preserves_historical_access_scope(store,monkeypatch):
    monkeypatch.setenv('PHI_RESEARCH_DB_ENABLED','1');monkeypatch.setenv('PHI_RESEARCH_DB_PATH',str(store.path))
    sid=store.put_source(record())
    store.save_check(sid,'PDF_PASSAGES_VERIFIED',url='https://publisher.example/paper.pdf',passages=[{'text':'A verified body passage. '*20,'locator':{'pdf_page':2}}])
    store.save_check(sid,'PDF_PASSAGES_VERIFIED',url='https://mirror.example/paper.pdf',passages=[{'text':'A verified body passage. '*20,'locator':{'pdf_page':2}}])
    store.save_check(sid,'ACCESS_DENIED',http_status=403)
    from research_bridge import local_records,evidence_result
    assert local_records('moral responsibility')[0]['retrieval_origin']=='LOCAL_RESEARCH_DB'
    result=evidence_result(sid,'FULL_TEXT_IF_LEGALLY_AVAILABLE')
    assert result['full_text_status']=='PERSISTED_VERIFIED_READ'
    assert result['latest_access_check']['outcome']=='ACCESS_DENIED'
    assert result['evidence_passages'][0]['locator']['pdf_page']==2
    assert len(result['evidence_passages'])==1, 'mirror URLs do not duplicate the same evidence passage'
    from deep_tool_context import tool_context
    serialized,delivery=tool_context('get_scholarly_source',result,'general')
    assert json.loads(serialized)==result and delivery['status']=='complete'


def test_public_read_api_and_disabled_bridge(store,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes.research import router
    sid=store.put_source(record());monkeypatch.setenv('PHI_RESEARCH_DB_PATH',str(store.path));monkeypatch.delenv('PHI_RESEARCH_DB_ENABLED',raising=False)
    from research_bridge import local_records
    assert local_records('moral responsibility')==[]
    app=FastAPI();app.include_router(router);client=TestClient(app)
    assert client.get('/api/research/status').json()['sources']==1
    result=client.get('/api/research/sources/'+sid)
    assert result.status_code==200 and result.json()['doi']=='10.1234/example'
    assert 'record_json' not in result.json()
    assert client.get('/api/research/sources/search',params={'q':'moral responsibility'}).json()['results']


def test_metaso_missing_key_is_recorded_as_blocked_not_empty(store,monkeypatch):
    import research_providers as providers
    monkeypatch.setattr(providers,'_env_key',lambda _: '')
    result=providers.discover(store,'伦理学',['metaso'])
    assert result['providers'][0]['outcome']=='AUTHENTICATION_REQUIRED'
    assert store.stats()['query_runs']==1 and store.stats()['sources']==0
    monkeypatch.setattr(providers,'_env_key',lambda _: 'fixture-key')
    monkeypatch.setattr(providers,'fetch_json',lambda *args,**kwargs:{'unexpected':'shape'})
    result=providers.discover(store,'伦理学',['metaso'])
    assert result['providers'][0]['outcome']=='UNRECOGNIZED_PROVIDER_RESPONSE'


def test_free_will_query_does_not_promote_free_software_or_physics_results(store,monkeypatch):
    import research_providers as providers
    from research_relevance import assess
    wrong=record(title='SwissADME: a free web tool to evaluate pharmacokinetics')
    wrong['abstract']={'text':'This free tool will help researchers.'}
    assert assess('free will',wrong)['eligible'] is False
    surname=record(title='Use of a free radical method to evaluate antioxidant activity')
    surname['authors']=[{'name':'Brand-Williams'}]
    assert assess('free will',surname)['eligible'] is False, 'will must not match the surname Williams'
    assert assess('free will',record())['eligible'] is True
    monkeypatch.setattr(providers,'search_provider',lambda *args,**kwargs:wrong['provider_records'])
    result=providers.discover(store,'free will',['openalex'])
    assert result['source_ids']==[] and result['providers'][0]['outcome']=='NO_RELEVANT_CANDIDATES'
    assert store.stats()['sources']==1, 'rejected raw discovery remains auditable'
    assert store.search_sources('free will')==[]


def test_openalex_repository_versions_and_pdf_candidates_remain_distinct():
    response={'results':[{'id':'https://openalex.org/W1','title':'An Example','doi':'https://doi.org/10.1234/example','primary_location':{},'open_access':{},'locations':[{'is_oa':True,'landing_page_url':'https://repository.example/record/1','pdf_url':None},{'is_oa':True,'landing_page_url':'https://repository.example/record/1','pdf_url':'https://repository.example/paper.pdf'}]}]}
    normalized=scholarly.search_openalex('example',json_fetch=lambda _:response)
    canonical=scholarly.merge_records(normalized)[0]
    assert [c['candidate_kind'] for c in canonical['full_text_candidates']]==['OA_LOCATION','DIRECT_PDF']
    assert canonical['access']['level']=='METADATA_ONLY', 'OA URL is not proof of readable content'


def test_runtime_discovery_persists_records_and_marks_cached_reads(store,monkeypatch):
    monkeypatch.setenv('PHI_RESEARCH_DB_ENABLED','1');monkeypatch.setenv('PHI_RESEARCH_DB_PATH',str(store.path))
    monkeypatch.setattr(scholarly,'_cache',{'searches':{},'records':{}})
    monkeypatch.setattr(scholarly,'_save_cache',lambda:None)
    monkeypatch.setattr(scholarly,'_local_results',lambda *a,**k:[])
    calls=[]
    monkeypatch.setattr(scholarly,'search_crossref',lambda *a,**k:calls.append(1) or record()['provider_records'])
    monkeypatch.setattr(scholarly,'search_openalex',lambda *a,**k:[])
    result=scholarly.search_scholarship('moral responsibility')
    assert store.source(result['results'][0]['source_record_id'])
    cached=scholarly.search_scholarship('moral responsibility')
    assert len(calls)==1 and cached['cached'] and cached['providers_queried']==[]
    assert cached['results'][0]['retrieval_origin'].endswith('+CACHE')
