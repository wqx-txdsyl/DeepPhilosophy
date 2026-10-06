import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deep_web_search as web
import scholarly_sources as scholarship
import pytest
from research_relevance import assess
from research_transport import ResearchHTTPError
from deep_bare_agent import tool_status


@pytest.fixture(autouse=True)
def no_paid_search_in_tests(monkeypatch):
    monkeypatch.setattr(web, 'native_search', lambda query:None)


def test_native_search_uses_only_actual_tool_results_not_answer_prose():
    from deepseek_web_search import parse_response
    response = {'content':[
        {'type':'text','text':'Invented citation https://fake.example', 'citations':[{'url':'https://example.org/source','cited_text':'actual citation excerpt'}]},
        {'type':'web_search_tool_result','content':[{'type':'web_search_result','url':'https://example.org/source','title':'Evidence','encrypted_content':'opaque'}]},
        {'type':'web_search_tool_result','content':[{'type':'web_search_result','url':'https://example.org/source','title':'duplicate'}]},
    ]}
    result = parse_response(response, 'Evidence')
    assert len(result['results']) == 1
    assert result['results'][0]['snippet'] == 'actual citation excerpt'
    assert 'encrypted_content' not in result['results'][0]
    with pytest.raises(ResearchHTTPError,match='NATIVE_SEARCH_NOT_EXECUTED'):
        parse_response({'content':[{'type':'text','text':'I searched the web.'}]},'test')
    with pytest.raises(ResearchHTTPError,match='rate_limit_exceeded'):
        parse_response({'content':[{'type':'web_search_tool_result','content':{'error_code':'rate_limit_exceeded'}}]},'test')


def test_native_success_short_circuits_html_scraping(monkeypatch):
    monkeypatch.setattr(web,'native_search',lambda q:{'query':q,'status':'success','source':'deepseek','results':[{'title':'Evidence'}]})
    monkeypatch.setattr(web,'fetch_bytes',lambda *a,**k:pytest.fail('should not scrape after native search'))
    assert web.search('Evidence')['source'] == 'deepseek'


def test_native_adapter_never_reuses_another_providers_key(monkeypatch):
    import deepseek_web_search as native
    from routes import agent_llm
    monkeypatch.setattr(agent_llm,'API_URL','https://other-provider.example/v1')
    monkeypatch.setattr(native,'fetch_json',lambda *a,**k:pytest.fail('credential must not be sent'))
    assert native.search('test') is None


def test_native_failure_retained_when_fallback_succeeds(monkeypatch):
    def fail(query):raise ResearchHTTPError('RATE_LIMITED',429,'30')
    monkeypatch.setattr(web,'native_search',fail)
    monkeypatch.setattr(web,'fetch_bytes',lambda *a,**k:{'status':200,'body':b'<li class="b_algo"><h2><a href="https://example.org/kant">Kant</a></h2></li>'})
    result=web.search('Kant')
    assert result['status']=='partial' and result['source']=='bing'
    assert result['provider_errors'][0]['provider']=='deepseek'


def test_bing_extracts_result_heading_not_first_ad_or_tracking_link():
    url = 'https://example.org/paper'
    encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip('=')
    html = f'<li class="b_algo"><a href="https://wrong.example">logo</a><h2><a href="https://www.bing.com/ck/a?u=a1{encoded}">A paper</a></h2><p>Evidence</p></li>'
    assert web.parse_bing(html) == [{'title':'A paper','url':url,'snippet':'Evidence'}]


def test_homepage_is_not_zero_results_and_wikipedia_sends_user_agent(monkeypatch):
    requests = []
    def fetch(url, **kw):
        requests.append((url, kw))
        if 'bing.com' in url:
            body = b'<html><title>Bing</title></html>'
        else:
            body = b'{"query":{"search":[{"title":"Kant","snippet":"<span>philosopher</span>"}]}}'
        return {'body':body, 'status':200}
    monkeypatch.setattr(web, 'fetch_bytes', fetch)
    result = web.search('Kant')
    assert result['status'] == 'partial'
    assert result['scope'] == 'encyclopedia_only'
    assert len(result['provider_errors']) == 2
    assert result['results'][0]['snippet'] == 'philosopher'
    assert all(options['headers']['User-Agent'] for _, options in requests)


def test_all_providers_fail_is_error_not_success_or_empty(monkeypatch):
    def fail(*args, **kwargs):
        raise ResearchHTTPError('ACCESS_DENIED',403)
    monkeypatch.setattr(web, 'fetch_bytes', fail)
    result = web.search('Kant')
    assert result['status'] == tool_status(result) == 'error'
    assert len(result['provider_errors']) == 4


def test_rss_empty_is_distinct_from_html_challenge():
    assert web.parse_bing('<rss><channel /></rss>', rss=True) == []
    import pytest
    with pytest.raises(ValueError):
        web.parse_bing('<html>captcha</html>')


def test_long_query_keeps_candidates_but_free_will_stays_specific():
    query = 'gift giving reciprocity obligation in hierarchical relationships ethics'
    assert assess(query, {'title':'Obligation, choice, and gift-giving in close relationships'})['eligible']
    assert assess(query, {'title':'Gift and Counter-Gift: The Reciprocity Rule'})['eligible']
    assert not assess(query, {'title':'Quantum field theory'})['eligible']
    assert not assess('free will', {'title':'A free software tool','authors':[{'name':'Williams'}], 'abstract':{'text':'This tool will be free.'}})['eligible']
    assert not assess(query, {'title':'Contents'})['eligible']


def test_irrelevant_serp_is_not_search_success():
    assert web.query_candidates('Immanuel Kant', [{'title':'Japanese hotels','snippet':'Travel guide'}]) == []
    assert web.query_candidates('教育部 严禁教师 违规收受 礼品礼金', [{'title':'教育部首页','snippet':'中国教育考试网'}]) == []
    good = {'title':'严禁教师违规收受礼品礼金','snippet':'教育部发布通知'}
    assert web.query_candidates('教育部 严禁教师 违规收受 礼品礼金', [good]) == [good]


def test_rate_limited_provider_not_retried_on_query_reformulation(monkeypatch):
    calls = []
    def crossref(query, **kwargs):
        calls.append(('crossref',query)); return []
    def openalex(query, **kwargs):
        calls.append(('openalex',query)); raise scholarship.ProviderError('RATE_LIMITED','HTTP 429')
    monkeypatch.setattr(scholarship, 'search_crossref', crossref)
    monkeypatch.setattr(scholarship, 'search_openalex', openalex)
    monkeypatch.setattr(scholarship, '_local_results', lambda *a, **k: [])
    monkeypatch.setattr(scholarship, '_cache', {'searches':{},'records':{}})
    monkeypatch.setattr(scholarship, '_save_cache', lambda:None)
    import research_bridge
    monkeypatch.setattr(research_bridge, 'persist_records', lambda records:None)
    result = scholarship.search_scholarship('gift giving reciprocity obligation in hierarchical relationships ethics')
    assert sum(p == 'openalex' for p,q in calls) == 1
    assert len(result['errors']) == 1 and result['status'] == 'partial'
    assert any(a['status'] == 'skipped' for a in result['provider_attempts'])
    # Failed searches are not replayed as fresh successful retrievals.
    scholarship.search_scholarship('gift giving reciprocity obligation in hierarchical relationships ethics')
    assert sum(p == 'openalex' for p,q in calls) == 2


def test_status_preserves_partial_failure_and_empty_outcomes():
    assert tool_status({'results':[], 'provider_errors':[{'error':'RATE_LIMITED'}]}) == 'partial'
    assert tool_status({'results':[]}) == 'empty'
    assert tool_status({'results':[{'title':'paper'}]}) == 'success'
    assert tool_status({'error':'NETWORK_UNAVAILABLE'}) == 'error'
