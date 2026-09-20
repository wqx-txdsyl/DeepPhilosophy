"""Opt-in runtime access to the durable research DB; legacy paths remain available."""
import os


def enabled_store():
    if os.environ.get('PHI_RESEARCH_DB_ENABLED','').lower() not in {'1','true','yes'}:
        return None
    from research_store import ResearchStore
    store=ResearchStore()
    return store if store.path.is_file() else None


def current_library_store(root):
    """A stale or interrupted index never replaces the canonical source path."""
    store=enabled_store()
    if not store:return None
    import json
    from research_ingest import inventory_signature
    with store.connect(readonly=True) as con:
        row=con.execute('SELECT status,report_json FROM builds ORDER BY started_at DESC LIMIT 1').fetchone()
    if not row or row['status'] not in {'COMPLETE','COMPLETE_WITH_ISSUES'}:return None
    report=json.loads(row['report_json'])
    if report.get('inventory_stable') and report.get('inventory_signature')==inventory_signature(root):return store
    return None


def local_records(query, limit=8):
    store=enabled_store()
    if not store:return []
    out=[]
    for hit in store.search_sources(query,limit=limit):
        source=store.source(hit['source_id']);rec=source['record']
        if rec.get('ingest') and not rec.get('cluster_ids_accepted'):
            continue  # Imported discovery-only records are not promoted to curated material.
        rec={**rec,'retrieval_origin':'LOCAL_RESEARCH_DB'}
        if not rec.get('title'):rec['title']=source['title']
        if any(e['kind']=='FULLTEXT_PASSAGE' and e['origin']=='VERIFIED_FETCH' for e in source['evidence']):
            rec['access']={**rec.get('access',{}),'level':'FULL_TEXT_READ','evidence':'persisted verified excerpts; current reachability is tracked separately'}
        out.append(rec)
    return out


def record(source_id):
    store=enabled_store()
    if not store:return None
    source=store.source(source_id)
    return {**source['record'],'title':source['record'].get('title') or source['title'],'retrieval_origin':'LOCAL_RESEARCH_DB'} if source else None


def live_json(url):
    """Use the verified DNS-pinned transport for live runtime bibliography."""
    from research_transport import fetch_json, ResearchHTTPError
    from scholarly_sources import ProviderError
    from urllib.parse import urlsplit, quote
    if urlsplit(url).hostname=='api.openalex.org':
        from research_providers import _env_key
        key=_env_key('OPENALEX_API_KEY')
        if key:url+='&api_key='+quote(key,safe='')
    try:return fetch_json(url)
    except ResearchHTTPError as exc:raise ProviderError(exc.code) from None


def persist_records(records):
    store=enabled_store()
    if store:
        for rec in records:store.put_source(rec,'RUNTIME_DISCOVERY')


def evidence_result(source_id, requested_access):
    store=enabled_store()
    if not store:return None
    source=store.source(source_id)
    if not source:return None
    rec={**source['record'],'title':source['record'].get('title') or source['title']};items=source['evidence'];latest=source['checks'][0] if source['checks'] else None
    requested_full=requested_access=='FULL_TEXT_IF_LEGALLY_AVAILABLE'
    chosen=[e for e in items if e['kind']==('FULLTEXT_PASSAGE' if requested_full else 'ABSTRACT') and (not requested_full or e['origin']=='VERIFIED_FETCH')]
    if not chosen:return None  # Preserve existing live-reader fallback.
    from scholarly_sources import model_view
    level='FULL_TEXT_READ' if requested_full else 'ABSTRACT_AVAILABLE'
    out={'source_record_id':source['source_id'],'bibliographic_record':model_view(rec),
         'access_level_before':rec.get('access',{}).get('level','METADATA_ONLY'),
         'access_level_after':rec.get('access',{}).get('level','METADATA_ONLY'),
         'returned_evidence_level':level,'historical_evidence_level':level,
         'full_text_status':'PERSISTED_VERIFIED_READ' if requested_full else 'PERSISTED_ABSTRACT',
         'source_url':chosen[0].get('source_url'),'content_hash':chosen[0]['text_hash'],
         'content_hash_basis':'persisted excerpt text; not the complete PDF binary',
         'access_notes':'返回数据库中已取得的历史证据；本次工具调用未重新获取网页，不能据此声称当前URL可达。',
         'latest_access_check':{k:latest.get(k) for k in ('checked_at','outcome','http_status','body_hash')} if latest else None,
         'evidence_origin':'PERSISTED_VERIFIED_READ' if requested_full else 'ABSTRACT_METADATA'}
    if requested_full:
        out['evidence_passages']=[{'passage_id':e['id'],'text':e['text'],'locator':e['locator'],'evidence_origin':'PERSISTED_VERIFIED_READ'} for e in chosen[:5]]
        out['passage_locators']=[e['locator'] for e in out['evidence_passages']]
    else:out['abstract']={'text':chosen[0]['text'],'source':chosen[0]['origin'],'hash':chosen[0]['text_hash']}
    return out
