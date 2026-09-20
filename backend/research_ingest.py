"""Lossless source indexing, audit and legacy scholarly import; never edits source files."""
import bisect
from collections import Counter
import json
from pathlib import Path
import re
import uuid

from research_store import ResearchStore, digest, dump, now


def inventory_signature(root):
    root=Path(root)
    files=[root/'app/public/books.json']
    files.extend((root/'app/public/book_detail').glob('*.json'))
    files.extend((root/'backend/data/book_chapters').glob('*/*.json'))
    rows=[]
    for path in sorted(files):
        stat=path.stat();rows.append((str(path.relative_to(root)),stat.st_size,stat.st_mtime_ns))
    return digest(dump(rows))


def chapter_text(document):
    if not isinstance(document, dict) or not isinstance(document.get('content'), list):
        raise ValueError('INVALID_CHAPTER_STRUCTURE')
    strings, blocks, starts, offset = [], [], [], 0
    for i, block in enumerate(document['content']):
        if not isinstance(block, dict):
            raise ValueError('INVALID_CONTENT_BLOCK')
        if block.get('type') != 'text':
            continue
        value = block.get('value')
        if not isinstance(value, str):
            raise ValueError('INVALID_TEXT_VALUE')
        if strings:
            offset += 1
        starts.append(offset);blocks.append(i);strings.append(value);offset += len(value)
    return '\n'.join(strings), starts, blocks


def windows(text, starts, blocks, size=1600, overlap=120):
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        yield start, end, blocks[max(0, bisect.bisect_right(starts, start)-1)], blocks[max(0, bisect.bisect_right(starts, end-1)-1)], text[start:end]
        if end == len(text):
            break
        start = end - overlap


def material_role(title):
    if re.search(r'编者|译者|译序|编后|导读|一书评述|出版说明|出版前言', title):
        return 'EDITORIAL_CANDIDATE', 'title_rule; not academically reviewed'
    if re.search(r'索引|参考文献|目录|版权|书目', title):
        return 'REFERENCE_APPARATUS_CANDIDATE', 'title_rule; not academically reviewed'
    return 'UNCLASSIFIED', 'no verified authorship classification'


def build_library(store: ResearchStore, root, progress=None):
    root=Path(root); public=root/'app/public'; chapter_root=root/'backend/data/book_chapters'
    catalog_raw=(public/'books.json').read_bytes();books=json.loads(catalog_raw)
    if not isinstance(books,list) or any(not isinstance(b,dict) or not re.fullmatch(r'[0-9a-f]{10,16}',str(b.get('id',''))) for b in books):
        raise ValueError('INVALID_BOOK_CATALOGUE')
    if len({b['id'] for b in books}) != len(books):
        raise ValueError('DUPLICATE_BOOK_ID')
    run=uuid.uuid4().hex;started=now();counts=Counter();issues=[]
    initial_inventory=inventory_signature(root)
    def issue(bid,path,code,severity='error',detail=None):
        row={'book_id':bid,'source_path':str(path.relative_to(root)) if path else None,'code':code,'severity':severity,'detail':detail or {}}
        issues.append(row)
    with store.connect() as con:
        con.execute('INSERT INTO builds(id,started_at,status) VALUES(?,?,?)',(run,started,'RUNNING'))
    try:
        for b in books:
            bid=b['id'];folder=chapter_root/bid;detail_path=public/'book_detail'/f'{bid}.json'
            detail={};meta={};detail_raw=b''
            start_issues=len(issues)
            try:detail_raw=detail_path.read_bytes();detail=json.loads(detail_raw)
            except (OSError,ValueError):issue(bid,detail_path,'DETAIL_UNREADABLE')
            if not isinstance(detail,dict):issue(bid,detail_path,'DETAIL_INVALID');detail={}
            meta_path=folder/'meta.json'
            if meta_path.exists():
                try:meta=json.loads(meta_path.read_bytes())
                except (OSError,ValueError):issue(bid,meta_path,'CHAPTER_META_UNREADABLE')
                if not isinstance(meta,dict):meta={};issue(bid,meta_path,'CHAPTER_META_INVALID')
            files=sorted((p for p in folder.glob('*.json') if p.stem.isdecimal()),key=lambda p:int(p.stem)) if folder.exists() else []
            indexes=[int(p.stem) for p in files]
            if indexes and indexes != list(range(len(files))):issue(bid,folder,'NONCONTIGUOUS_CHAPTER_INDEX',detail={'indexes':indexes})
            declared={'catalogue':b.get('chapterCount'),'detail':detail.get('chapterCount'),'meta':meta.get('chapterCount')}
            for source,n in declared.items():
                if n is not None and n != len(files):issue(bid,folder,'CHAPTER_COUNT_MISMATCH',detail={'source':source,'declared':n,'actual_files':len(files)})
            if not files:issue(bid,folder,'NO_LOCAL_CHAPTERS','warning',{'declared':declared})
            signature=digest(dump(b)+digest(detail_raw));valid=0;nonempty=0
            with store.connect() as con:
                con.execute('INSERT INTO books VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,author=excluded.author,region=excluded.region,expected_chapters=excluded.expected_chapters,status=excluded.status,metadata_json=excluded.metadata_json,source_hash=excluded.source_hash,indexed_at=excluded.indexed_at',
                            (bid,str(b.get('title') or ''),str(b.get('author') or ''),b.get('region'),b.get('chapterCount'),0,'indexing',dump({'catalogue':b,'detail':detail,'chapter_meta':meta}),signature,now()))
                prior={r['chapter_index']:r for r in con.execute('SELECT id,chapter_index,source_hash,text FROM chapters WHERE book_id=?',(bid,))}
                for index,old in prior.items():
                    if index not in indexes:con.execute('DELETE FROM chapters WHERE id=?',(old['id'],));counts['removed_derived_chapters']+=1
                book_hashes={}
                for path in files:
                    index=int(path.stem)
                    try:
                        if not path.resolve().is_relative_to(chapter_root.resolve()):raise ValueError('SOURCE_PATH_OUTSIDE_CHAPTER_ROOT')
                        raw=path.read_bytes();document=json.loads(raw);text,starts,blocks=chapter_text(document)
                        if document.get('index') is None:
                            issue(bid,path,'MISSING_INDEX_DERIVED_FROM_FILENAME','warning',{'derived_index':index})
                        elif document.get('index') != index:
                            issue(bid,path,'EMBEDDED_INDEX_DIFFERS_FROM_FILENAME','warning',{'embedded_index':document.get('index'),'derived_index':index,'basis':'reader resolves numeric filename'})
                        title=document.get('title')
                        if not isinstance(title,str):raise ValueError('INVALID_CHAPTER_TITLE')
                        source_hash=digest(raw)
                    except (OSError,ValueError,TypeError) as exc:
                        issue(bid,path,str(exc) if isinstance(exc,ValueError) and str(exc).isupper() else 'CHAPTER_UNREADABLE')
                        if index in prior:con.execute('DELETE FROM chapters WHERE id=?',(prior[index]['id'],))
                        counts['invalid_chapters']+=1
                        continue
                    valid+=1;nonempty+=bool(text.strip());counts['chapter_characters']+=len(text)
                    titles=meta.get('chapterTitles') or []
                    if index < len(titles) and titles[index] != title:issue(bid,path,'TITLE_MISMATCH','warning',{'meta_title':titles[index],'file_title':title})
                    if not text.strip():issue(bid,path,'EMPTY_CHAPTER','warning')
                    if text.strip() and digest(text) in book_hashes:issue(bid,path,'DUPLICATE_CHAPTER_TEXT','warning',{'same_as_index':book_hashes[digest(text)]})
                    book_hashes[digest(text)]=index
                    if index in prior and prior[index]['source_hash']==source_hash:
                        counts['unchanged_chapters']+=1
                        continue
                    if index in prior:con.execute('DELETE FROM chapters WHERE id=?',(prior[index]['id'],))
                    role,basis=material_role(title)
                    chapter_id=con.execute('INSERT INTO chapters(book_id,chapter_index,title,text,source_path,source_hash,text_hash,material_role,role_basis,indexed_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                                           (bid,index,title,text,str(path.relative_to(root)),source_hash,digest(text),role,basis,now())).lastrowid
                    con.executemany('INSERT INTO passages VALUES(?,?,?,?,?,?,?,?)',
                                    [(digest(f'{bid}:{index}:{source_hash}:{start}:{end}'),chapter_id,start,end,lo,hi,piece,digest(piece)) for start,end,lo,hi,piece in windows(text,starts,blocks)])
                    counts['indexed_chapters']+=1
                errors=any(i['severity']=='error' for i in issues[start_issues:])
                status='incomplete' if errors else 'readable' if nonempty else 'metadata_only'
                con.execute('UPDATE books SET actual_chapters=?,status=? WHERE id=?',(valid,status,bid))
                for item in issues[start_issues:]:
                    con.execute('INSERT OR IGNORE INTO audit_issues VALUES(?,?,?,?,?,?,?)',(digest(run+dump(item)),run,bid,item['source_path'],item['code'],item['severity'],dump(item['detail'])))
            counts['books_processed']+=1
            if progress and counts['books_processed']%25==0:progress(dict(counts))
        known={b['id'] for b in books}
        orphans=[p.name for p in chapter_root.iterdir() if p.is_dir() and p.name not in known]
        final_inventory=inventory_signature(root)
        if initial_inventory!=final_inventory:issue(None,None,'SOURCE_CHANGED_DURING_BUILD')
        report={'build_id':run,'started_at':started,'finished_at':now(),'catalogue_hash':digest(catalog_raw),'inventory_signature':final_inventory,'inventory_stable':initial_inventory==final_inventory,'catalogue_books':len(books),'counts':dict(counts),'issues_by_code':dict(Counter(i['code'] for i in issues)),'error_count':sum(i['severity']=='error' for i in issues),'warning_count':sum(i['severity']=='warning' for i in issues),'orphan_chapter_directories':orphans,'issues':issues}
        with store.connect() as con:
            for row in con.execute('SELECT id FROM books').fetchall():
                if row['id'] not in known:con.execute("UPDATE books SET status='not_in_catalogue' WHERE id=?",(row['id'],))
            con.execute('UPDATE builds SET status=?,finished_at=?,report_json=? WHERE id=?',('COMPLETE_WITH_ISSUES' if issues or orphans else 'COMPLETE',report['finished_at'],dump(report),run))
        return report
    except BaseException as exc:
        with store.connect() as con:
            con.execute('UPDATE builds SET status=?,finished_at=?,report_json=? WHERE id=?',('INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'FAILED',now(),dump({'exception':type(exc).__name__,'counts':dict(counts)}),run))
        raise


def import_scholarly(store, root):
    root=Path(root);base=root/'backend/data/scholarly';count=0;evidence_count=0;aliases={}
    registry=base/'registry.jsonl'
    for line in registry.open() if registry.exists() else []:
        if not line.strip():continue
        rec=json.loads(line);sid=store.put_source(rec,'LEGACY_REGISTRY');aliases[rec['source_record_id']]=sid;count+=1
    cache=root/'backend/data/scholarly_cache.json'
    if cache.exists():
        for rec in json.loads(cache.read_text()).get('records',{}).values():
            if isinstance(rec,dict) and rec.get('source_record_id'):
                sid=store.put_source(rec,'LEGACY_CACHE');aliases[rec['source_record_id']]=sid;count+=1
    path=base/'evidence.jsonl'
    for line in path.open() if path.exists() else []:
        if not line.strip():continue
        e=json.loads(line);sid=aliases.get(e.get('source_record_id'))
        if sid and isinstance(e.get('text'),str):
            store.add_evidence(sid,e.get('evidence_type','UNKNOWN'),e['text'],url=e.get('source_url'),locator=e.get('locator'),origin='HISTORICAL_IMPORT');evidence_count+=1
    return {'imported_records':count,'imported_evidence':evidence_count,'note':'Historical imports do not assert current network reachability.'}
