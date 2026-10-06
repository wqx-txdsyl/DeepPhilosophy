"""Verify actual secondary-source access and record bounded, located evidence."""
import hashlib
import re
import shutil
import subprocess
import tempfile
import time
import urllib.parse

from bs4 import BeautifulSoup
from research_transport import fetch_bytes, ResearchHTTPError, redact_url

MAX_PDF_PAGES = 80
MAX_EVIDENCE_CHARS = 1200


def _norm(text):
    return re.sub(r'[^\w]', '', str(text or '').casefold())


def identity_match(record, text, declared_doi=None, declared_title=None):
    doi=(record.get('identifiers') or {}).get('doi') or ''
    title=record.get('title') or ''
    if declared_doi and doi:
        normalized=re.sub(r'^https?://(?:dx\.)?doi.org/', '', declared_doi, flags=re.I).strip().lower()
        if normalized != doi.lower():return False, 'DECLARED_DOI_MISMATCH'
    head=text[:10000]
    target=_norm(title)
    if len(target)>=8 and target in _norm(declared_title or head):return True, 'TITLE_MATCH'
    terms=[t for t in re.findall(r'\w+', title.casefold()) if len(t)>2 and t not in {'the','and','for','with','from','that','this','into'}]
    title_coverage=sum(t in (declared_title or head).casefold() for t in terms)/len(terms) if terms else 0
    if len(terms)>=4 and title_coverage>=.85:return True, 'TITLE_TOKEN_MATCH'
    if doi and doi.casefold() in re.sub(r'\s+', '', text[:5000]).casefold() and title_coverage>=.4:return True, 'DOI_AND_TITLE_MATCH'
    return False, 'IDENTITY_UNVERIFIED'


def parse_pdf(body):
    if not body.startswith(b'%PDF'):raise ValueError('NOT_PDF')
    binary=shutil.which('pdftotext')
    if not binary:raise ValueError('PDF_PARSER_UNAVAILABLE')
    with tempfile.TemporaryDirectory(prefix='phi-research-') as folder:
        from pathlib import Path
        source=Path(folder)/'source.pdf';source.write_bytes(body)
        result=subprocess.run([binary,'-layout','-enc','UTF-8','-f','1','-l',str(MAX_PDF_PAGES),str(source),'-'],capture_output=True,timeout=30)
    if result.returncode:raise ValueError('PDF_PARSE_FAILED')
    text=result.stdout.decode('utf-8','replace')
    if len(text.strip())<200:raise ValueError('PDF_NO_EXTRACTABLE_TEXT')
    if len(text)>4_000_000:raise ValueError('PDF_TEXT_LIMIT')
    return text.split('\f')[:MAX_PDF_PAGES]


def select_passages(pages, query='', kind='FULLTEXT_PASSAGE'):
    terms=[t.casefold() for t in re.findall(r'\w+',query) if len(t)>2]
    candidates=[]
    for page_index,text in enumerate(pages,1):
        for match in re.finditer(r'\S[\s\S]*?(?=\n\s*\n|\Z)',text):
            block=match.group()
            if len(block.strip())<100:continue
            score=sum(t in block.casefold() for t in terms)
            candidates.append((-score,page_index,match.start(),block))
    candidates.sort(key=lambda c:(c[0],c[1],c[2]))
    out=[];remaining=MAX_EVIDENCE_CHARS
    for _,page,start,block in candidates:
        piece=block[:min(600,remaining)]
        if not piece or any(piece==p['text'] for p in out):continue
        out.append({'kind':kind,'text':piece,'locator':{'pdf_page':page,'start_char':start,'end_char':start+len(piece),'page_number_basis':'PDF page order; not printed page label','parsed_page_limit':MAX_PDF_PAGES}})
        remaining-=len(piece)
        if len(out)>=3 or remaining<100:break
    return out


def verify_source(store, source_id, *, query='', fetch=fetch_bytes, pdf_parser=parse_pdf, max_attempts=3):
    source=store.source(source_id)
    if not source:raise ValueError('Unknown source ID')
    sid=source['source_id'];record={**source['record'],'title':source['record'].get('title') or source['title']};candidates=[]
    for c in record.get('full_text_candidates') or []:
        if isinstance(c,dict) and isinstance(c.get('url'),str):candidates.append(c['url'])
    candidates.extend(record.get('stable_urls') or [])
    candidates=list(dict.fromkeys(u for u in candidates if isinstance(u,str) and u.startswith(('http://','https://'))))
    attempts=[];seen=set();index=0
    while index<len(candidates) and len(attempts)<max_attempts:
        url=candidates[index];index+=1
        if url in seen:continue
        seen.add(url);t0=time.monotonic();response=None;passages=[];detail={}
        try:
            response=fetch(url,accept='application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.1')
            body=response['body'];detail['network_modes']=response.get('network_modes',[])
            if body.startswith(b'%PDF'):
                pages=pdf_parser(body);text='\n\n'.join(pages)
                matched,basis=identity_match(record,text);detail.update(identity_basis=basis,parsed_pages=len(pages),parsed_page_limit=MAX_PDF_PAGES)
                if not matched:outcome='IDENTITY_UNVERIFIED'
                else:
                    passages=select_passages(pages,query or record.get('title',''))
                    outcome='PDF_PASSAGES_VERIFIED' if passages else 'PDF_TEXT_WITHOUT_USABLE_PASSAGES'
            elif response.get('content_type') in {'text/html','application/xhtml+xml'}:
                soup=BeautifulSoup(body,'html.parser')
                if soup.select_one('#challenge-form, #challenge-running, form[action*="captcha"]'):
                    outcome='ACCESS_CHALLENGE'
                else:
                    meta=lambda name: next((m.get('content','') for m in soup.find_all('meta') if str(m.get('name') or m.get('property') or '').casefold()==name),None)
                    title=meta('citation_title') or (soup.title.get_text(' ',strip=True) if soup.title else '')
                    page_text=soup.get_text(' ',strip=True)
                    matched,basis=identity_match(record,page_text,meta('citation_doi'),title);detail['identity_basis']=basis
                    pdf_url=meta('citation_pdf_url')
                    if matched and pdf_url:
                        candidate=urllib.parse.urljoin(response['url'],pdf_url)
                        if candidate not in seen:candidates.insert(index,candidate)
                        detail['discovered_pdf_url']=redact_url(candidate)
                    article=soup.select_one('[itemprop="articleBody"], .article__body, #article-body')
                    abstract=soup.select_one('#abstract, .abstract, [class="abstract-content"]')
                    if matched and article and len(article.get_text(' ',strip=True))>=1200:
                        text=article.get_text('\n\n',strip=True);passages=select_passages([text],query or title)
                        for p in passages:p['locator']={'html_selector':'article-body','start_char':p['locator']['start_char'],'end_char':p['locator']['end_char']}
                        outcome='HTML_PASSAGES_VERIFIED' if passages else 'LANDING_PAGE_ONLY'
                    elif matched and abstract and len(abstract.get_text(' ',strip=True))>=100:
                        text=abstract.get_text(' ',strip=True)[:MAX_EVIDENCE_CHARS]
                        passages=[{'kind':'ABSTRACT','text':text,'locator':{'html_section':'abstract'}}];outcome='ABSTRACT_VERIFIED'
                    else:outcome='LANDING_PAGE_ONLY' if matched else 'IDENTITY_UNVERIFIED'
            else:outcome='UNSUPPORTED_CONTENT'
        except ResearchHTTPError as exc:
            outcome=exc.code;detail={'http_status':exc.status,'retry_after':exc.retry_after,'final_url':exc.final_url}
        except (ValueError,subprocess.TimeoutExpired) as exc:
            outcome=str(exc) if isinstance(exc,ValueError) and str(exc).isupper() else 'PDF_PARSE_TIMEOUT'
        duration=round((time.monotonic()-t0)*1000)
        check_id=store.save_check(sid,outcome,url=redact_url(url),final_url=redact_url(response['url']) if response else detail.get('final_url'),http_status=response['status'] if response else detail.get('http_status'),content_type=response.get('content_type') if response else None,body_hash=hashlib.sha256(response['body']).hexdigest() if response else None,byte_count=len(response['body']) if response else None,duration_ms=duration,detail=detail,passages=passages)
        attempts.append({'check_id':check_id,'outcome':outcome,'url':redact_url(url),'duration_ms':duration,'evidence_items':len(passages)})
        if outcome in {'PDF_PASSAGES_VERIFIED','HTML_PASSAGES_VERIFIED'}:break
    if not attempts:
        outcome='PERSISTED_ABSTRACT_ONLY' if any(e['kind']=='ABSTRACT' for e in source['evidence']) else 'NO_RETRIEVABLE_URL'
        check_id=store.save_check(sid,outcome,detail={'network_requested':False,'note':'Local evidence is available historically; remote accessibility was not verified.'})
        attempts.append({'check_id':check_id,'outcome':outcome,'evidence_items':0})
    return {'source_id':sid,'title':source['title'],'attempts':attempts,'fulltext_verified':any(a['outcome'] in {'PDF_PASSAGES_VERIFIED','HTML_PASSAGES_VERIFIED'} for a in attempts),'abstract_available_locally':any(e['kind']=='ABSTRACT' for e in store.source(sid)['evidence'])}
