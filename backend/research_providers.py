"""Explicit provider adapters feeding canonical bibliography and a query ledger."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import time
import urllib.parse

import scholarly_sources as scholarly
from research_store import now
from research_transport import ResearchHTTPError, fetch_json
from research_relevance import assess, VERSION as RELEVANCE_VERSION


PROVIDERS=('crossref','openalex','semantic_scholar','metaso')


def _env_key(name):
    # Existing project convention: credentials come from the root .env; values
    # are never returned, logged, or put into the database.
    from routes.agent_llm import _load_env
    _load_env()
    return os.environ.get(name,'').strip()


def provider_status():
    return {'crossref':{'authentication':'not_required'},
            'openalex':{'authentication':'configured' if _env_key('OPENALEX_API_KEY') else 'public_quota_only'},
            'semantic_scholar':{'authentication':'configured' if _env_key('SEMANTIC_SCHOLAR_API_KEY') else 'public_quota_only'},
            'metaso':{'authentication':'configured' if _env_key('METASO_API_KEY') else 'required'}}


def search_provider(provider, query, limit=5, open_access_only=False):
    limit=min(10,max(1,int(limit)))
    if provider=='crossref':
        return scholarly.search_crossref(query,limit,json_fetch=fetch_json)
    if provider=='openalex':
        key=_env_key('OPENALEX_API_KEY')
        def get(url):
            if key:url+='&api_key='+urllib.parse.quote(key,safe='')
            return fetch_json(url)
        return scholarly.search_openalex(query,limit,json_fetch=get,open_access_only=open_access_only)
    if provider=='semantic_scholar':
        key=_env_key('SEMANTIC_SCHOLAR_API_KEY')
        url='https://api.semanticscholar.org/graph/v1/paper/search?'+urllib.parse.urlencode({'query':query,'limit':limit,'fields':'title,authors,year,venue,externalIds,abstract,openAccessPdf,url,publicationTypes'})
        data=fetch_json(url,headers={'x-api-key':key} if key else {})
        if not isinstance(data.get('data'),list):raise ResearchHTTPError('UNRECOGNIZED_PROVIDER_RESPONSE')
        out=[]
        for item in data.get('data',[])[:limit]:
            pdf=item.get('openAccessPdf') or {};doi=scholarly.normalize_doi((item.get('externalIds') or {}).get('DOI'))
            out.append({'provider':'semantic_scholar','provider_record_id':item.get('paperId'),'title':item.get('title'),'authors':[{'name':a.get('name','')} for a in item.get('authors',[])],'publication_year':item.get('year'),'container_title':item.get('venue'),'publication_type':'JOURNAL_ARTICLE' if 'JournalArticle' in (item.get('publicationTypes') or []) else 'OTHER','doi':doi,'abstract_text':item.get('abstract'),'stable_urls':[u for u in [item.get('url'),'https://doi.org/'+doi if doi else None] if u],'oa_pdf_url':pdf.get('url'),'oa_candidate_kind':'DIRECT_PDF' if pdf.get('url') else None})
        return out
    if provider=='metaso':
        key=_env_key('METASO_API_KEY')
        if not key:raise ResearchHTTPError('AUTHENTICATION_REQUIRED')
        # Search only. Generated answers are not imported as scholarly evidence.
        data=fetch_json('https://metaso.cn/api/v1/search',headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},data=json.dumps({'q':query,'scope':'paper','size':limit,'includeSummary':False,'includeRawContent':False}).encode())
        if 'papers' in data:rows=data['papers']
        elif 'results' in data:rows=data['results']
        else:raise ResearchHTTPError('UNRECOGNIZED_PROVIDER_RESPONSE')
        if not isinstance(rows,list):raise ResearchHTTPError('UNRECOGNIZED_PROVIDER_RESPONSE')
        out=[]
        for item in rows[:limit]:
            url=item.get('link') or item.get('url')
            if not isinstance(url,str) or not url.startswith(('https://','http://')):continue
            from research_store import digest
            out.append({'provider':'metaso','provider_record_id':digest(url),'title':item.get('title'),'authors':None,'publication_year':None,'container_title':None,'publication_type':'OTHER','doi':None,'stable_urls':[url]})
        if rows and not out:raise ResearchHTTPError('UNRECOGNIZED_SOURCE_RECORDS')
        return out
    raise ValueError('Unknown research provider')


def discover(store, query, providers=PROVIDERS, limit=5, open_access_only=False):
    if not isinstance(query,str) or not query.strip() or len(query)>500:raise ValueError('Query must contain 1–500 characters')
    if any(p not in PROVIDERS for p in providers):raise ValueError('Unknown research provider')
    def run(provider):
        started=now();t0=time.monotonic();sids=[];error=None;rejected=[];raw_count=0
        try:
            rows=search_provider(provider,query,limit,open_access_only=open_access_only)
            raw_count=len(rows)
            for record in scholarly.merge_records(rows):
                sid=store.put_source(record,provider)
                assessment=assess(query,record)
                if assessment['eligible']:sids.append(sid)
                else:rejected.append({'source_id':sid,'title':record.get('title'),'assessment':assessment})
            outcome='SUCCESS' if sids else 'NO_RELEVANT_CANDIDATES' if rows else 'EMPTY'
        except ResearchHTTPError as exc:
            outcome=exc.code;error={'http_status':exc.status,'retry_after':exc.retry_after}
        except scholarly.ProviderError as exc:
            outcome=exc.kind;error={}
        except (TypeError,KeyError,AttributeError,IndexError) as exc:
            outcome='INVALID_PROVIDER_RESPONSE';error={'exception_type':type(exc).__name__}
        elapsed=round((time.monotonic()-t0)*1000)
        detail={'error':error,'raw_result_count':raw_count,'rejected':rejected,'relevance_version':RELEVANCE_VERSION}
        run_id=store.save_query(provider,query,started,outcome,elapsed,sids,detail)
        return {'provider':provider,'outcome':outcome,'source_ids':sids,'query_run_id':run_id,'duration_ms':elapsed,'error':error,'raw_result_count':raw_count,'rejected':rejected}
    with ThreadPoolExecutor(max_workers=min(len(providers) or 1,3)) as pool:results=list(pool.map(run,providers))
    return {'query':query,'providers':results,'source_ids':list(dict.fromkeys(s for r in results for s in r['source_ids']))}
