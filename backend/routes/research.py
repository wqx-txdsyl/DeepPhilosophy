"""Read-only access to the derived research database. Ingestion remains a local CLI."""
from fastapi import APIRouter, HTTPException, Query
from research_store import ResearchStore

router=APIRouter(prefix='/api/research',tags=['research'])


def store():
    result=ResearchStore()
    if not result.path.is_file():raise HTTPException(503,'Research database has not been built')
    return result


@router.get('/status')
def status():
    import os
    return {**store().stats(),'runtime_integration_enabled':os.environ.get('PHI_RESEARCH_DB_ENABLED','').lower() in {'1','true','yes'}}


@router.get('/passages/{passage_id}')
def passage(passage_id:str):
    result=store().passage(passage_id)
    if result is None:raise HTTPException(404,'Passage not found')
    return result


@router.get('/books/search')
def search_books(q: str=Query(min_length=1,max_length=500),limit:int=Query(default=10,ge=1,le=30),book_id:str | None=None):
    return {'query':q,'results':store().search_books(q,limit,book_id),'scope':'derived local index; results are excerpts, not a claim of reading the complete book'}


@router.get('/sources/search')
def search_sources(q:str=Query(min_length=1,max_length=500),limit:int=Query(default=10,ge=1,le=30)):
    return {'query':q,'results':store().search_sources(q,limit)}


@router.get('/sources/{source_id:path}')
def source(source_id:str):
    result=store().source(source_id)
    if not result:raise HTTPException(404,'Source not found')
    out={k:result[k] for k in ['source_id','doi','title','authors','year','venue','publication_type','updated_at']}
    out['provenance']=result['record'].get('provenance',{})
    out['classification']=result['record'].get('philosophical_role','UNKNOWN')
    out['classification_note']='Publication type and access do not establish scholarly authority or peer review.'
    out['latest_access_check']=result['checks'][0] if result['checks'] else None
    out['evidence']=[{k:e[k] for k in ['id','kind','text','text_hash','source_url','locator','origin','obtained_at']} for e in result['evidence'][:5]]
    out['note']='Stored evidence is historical. The latest access check separately reports current reachability.'
    return out
