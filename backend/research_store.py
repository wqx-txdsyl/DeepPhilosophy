"""Transactional, rebuildable research database. Source JSON remains authoritative."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / 'backend/data/research/library.sqlite3'
SCHEMA_VERSION = 1


def now():
    return datetime.now(timezone.utc).isoformat()


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


SCHEMA = '''
CREATE TABLE IF NOT EXISTS builds(id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL, report_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS books(id TEXT PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL, region TEXT, expected_chapters INTEGER, actual_chapters INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL, metadata_json TEXT NOT NULL, source_hash TEXT NOT NULL, indexed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chapters(id INTEGER PRIMARY KEY, book_id TEXT NOT NULL REFERENCES books(id), chapter_index INTEGER NOT NULL, title TEXT NOT NULL, text TEXT NOT NULL, source_path TEXT NOT NULL, source_hash TEXT NOT NULL, text_hash TEXT NOT NULL, material_role TEXT NOT NULL, role_basis TEXT NOT NULL, indexed_at TEXT NOT NULL, UNIQUE(book_id,chapter_index));
CREATE TABLE IF NOT EXISTS passages(id TEXT PRIMARY KEY, chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE, start_char INTEGER NOT NULL, end_char INTEGER NOT NULL, start_block INTEGER NOT NULL, end_block INTEGER NOT NULL, text TEXT NOT NULL, text_hash TEXT NOT NULL, CHECK(end_char>start_char));
CREATE INDEX IF NOT EXISTS passage_chapter ON passages(chapter_id,start_char);
CREATE VIRTUAL TABLE IF NOT EXISTS chapter_fts USING fts5(title,text,content='chapters',content_rowid='id',tokenize='trigram');
CREATE TRIGGER IF NOT EXISTS chapter_ai AFTER INSERT ON chapters BEGIN INSERT INTO chapter_fts(rowid,title,text) VALUES(new.id,new.title,new.text); END;
CREATE TRIGGER IF NOT EXISTS chapter_ad AFTER DELETE ON chapters BEGIN INSERT INTO chapter_fts(chapter_fts,rowid,title,text) VALUES('delete',old.id,old.title,old.text); END;
CREATE TRIGGER IF NOT EXISTS chapter_au AFTER UPDATE ON chapters BEGIN INSERT INTO chapter_fts(chapter_fts,rowid,title,text) VALUES('delete',old.id,old.title,old.text); INSERT INTO chapter_fts(rowid,title,text) VALUES(new.id,new.title,new.text); END;
CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY, doi TEXT UNIQUE, title TEXT NOT NULL, authors_json TEXT NOT NULL, year INTEGER, venue TEXT, publication_type TEXT, record_json TEXT NOT NULL, search_text TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source_aliases(alias TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id));
CREATE TABLE IF NOT EXISTS provider_records(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id), provider TEXT NOT NULL, provider_record_id TEXT, payload_json TEXT NOT NULL, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS provider_source ON provider_records(source_id,provider);
CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(title,search_text,content='sources',content_rowid='rowid',tokenize='trigram');
CREATE TRIGGER IF NOT EXISTS source_ai AFTER INSERT ON sources BEGIN INSERT INTO source_fts(rowid,title,search_text) VALUES(new.rowid,new.title,new.search_text); END;
CREATE TRIGGER IF NOT EXISTS source_ad AFTER DELETE ON sources BEGIN INSERT INTO source_fts(source_fts,rowid,title,search_text) VALUES('delete',old.rowid,old.title,old.search_text); END;
CREATE TRIGGER IF NOT EXISTS source_au AFTER UPDATE ON sources BEGIN INSERT INTO source_fts(source_fts,rowid,title,search_text) VALUES('delete',old.rowid,old.title,old.search_text); INSERT INTO source_fts(rowid,title,search_text) VALUES(new.rowid,new.title,new.search_text); END;
CREATE TABLE IF NOT EXISTS access_checks(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id), checked_at TEXT NOT NULL, outcome TEXT NOT NULL, http_status INTEGER, source_url TEXT, final_url TEXT, content_type TEXT, body_hash TEXT, byte_count INTEGER, duration_ms INTEGER, detail_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS checks_source_time ON access_checks(source_id,checked_at DESC);
CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id), check_id TEXT REFERENCES access_checks(id), kind TEXT NOT NULL, text TEXT NOT NULL, text_hash TEXT NOT NULL, source_url TEXT, locator_json TEXT NOT NULL, origin TEXT NOT NULL, obtained_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS evidence_source ON evidence(source_id,kind);
CREATE TABLE IF NOT EXISTS evidence_checks(check_id TEXT NOT NULL REFERENCES access_checks(id), evidence_id TEXT NOT NULL REFERENCES evidence(id), PRIMARY KEY(check_id,evidence_id));
CREATE TABLE IF NOT EXISTS query_runs(id TEXT PRIMARY KEY, provider TEXT NOT NULL, query TEXT NOT NULL, started_at TEXT NOT NULL, outcome TEXT NOT NULL, result_count INTEGER NOT NULL, duration_ms INTEGER NOT NULL, detail_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS query_hits(run_id TEXT NOT NULL REFERENCES query_runs(id), source_id TEXT NOT NULL REFERENCES sources(source_id), rank INTEGER NOT NULL, PRIMARY KEY(run_id,source_id));
CREATE TABLE IF NOT EXISTS audit_issues(id TEXT PRIMARY KEY, build_id TEXT NOT NULL REFERENCES builds(id), book_id TEXT, source_path TEXT, code TEXT NOT NULL, severity TEXT NOT NULL, detail_json TEXT NOT NULL);
'''


class ResearchStore:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get('PHI_RESEARCH_DB_PATH') or DEFAULT_PATH)

    @contextmanager
    def connect(self, readonly=False):
        if readonly:
            con = sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA busy_timeout=30000')
        try:
            yield con
            if not readonly:
                con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def initialize(self):
        with self.connect() as con:
            version = con.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ValueError('Unsupported research database version')
            con.execute('PRAGMA journal_mode=WAL')
            con.executescript(SCHEMA)
            con.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

    def put_source(self, record, origin='import'):
        """Merge only established DOI identity; preserve all provider snapshots."""
        from scholarly_sources import merge_records, normalize_doi
        rec = json.loads(dump(record))
        original_id = rec['source_record_id']
        doi = normalize_doi((rec.get('identifiers') or {}).get('doi'))
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute('SELECT * FROM sources WHERE doi=? OR source_id=?', (doi, original_id)).fetchone()
            if old is None:
                old = con.execute('SELECT s.* FROM sources s JOIN source_aliases a ON a.source_id=s.source_id WHERE a.alias=?', (original_id,)).fetchone()
            sid = old['source_id'] if old else original_id
            if old:
                before = json.loads(old['record_json'])
                snapshots = {digest(dump(p)): p for p in before.get('provider_records', []) + rec.get('provider_records', [])}
                if snapshots:
                    candidates = merge_records(list(snapshots.values()))
                    merged = next((c for c in candidates if doi and c['identifiers'].get('doi') == doi), candidates[0])
                    # Keep explicit curation and access history; checks are separate facts.
                    for key in ('ingest', 'cluster_ids_accepted', 'cluster_ids_discovery_only', 'cluster_topics', 'related_primary_book_ids', 'philosophical_role', 'peer_review_status', 'reuse_status'):
                        if key in before:
                            merged[key] = before[key]
                    rec = merged
                if not (rec.get('abstract') or {}).get('text') and (before.get('abstract') or {}).get('text'):
                    rec['abstract'] = before['abstract']
                candidates = before.get('full_text_candidates', []) + rec.get('full_text_candidates', [])
                rec['full_text_candidates'] = list({dump(c): c for c in candidates}.values())
            rec['source_record_id'] = sid
            authors = rec.get('authors') or []
            title = rec.get('title') or (old['title'] if old else '') or next((p.get('title') for p in rec.get('provider_records', []) if p.get('title')), '')
            abstract = (rec.get('abstract') or {}).get('text') or ''
            search_text = ' '.join([title, *(str(a.get('name', '')) for a in authors if isinstance(a, dict)), rec.get('container_title') or '', abstract, ' '.join(rec.get('aliases') or [])])
            stamp = now()
            con.execute('INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET doi=coalesce(excluded.doi,sources.doi),title=excluded.title,authors_json=excluded.authors_json,year=excluded.year,venue=excluded.venue,publication_type=excluded.publication_type,record_json=excluded.record_json,search_text=excluded.search_text,updated_at=excluded.updated_at',
                        (sid, doi, title, dump(authors), rec.get('publication_year'), rec.get('container_title'), rec.get('publication_type'), dump(rec), search_text, stamp))
            for alias in {original_id, sid, *rec.get('identifiers', {}).get('provider_ids', [])}:
                existing = con.execute('SELECT source_id FROM source_aliases WHERE alias=?', (alias,)).fetchone()
                if existing and existing[0] != sid:
                    raise ValueError('Conflicting source identity; manual reconciliation required')
                con.execute('INSERT OR IGNORE INTO source_aliases VALUES(?,?)', (alias, sid))
            for p in rec.get('provider_records', []):
                snapshot = dump(p)
                con.execute('INSERT INTO provider_records VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_seen_at=excluded.last_seen_at',
                            (digest(sid + snapshot), sid, p.get('provider') or origin, p.get('provider_record_id'), snapshot, stamp, stamp))
            if abstract:
                self._put_evidence(con, sid, 'ABSTRACT', abstract, None, None, {}, 'PROVIDER_METADATA', stamp)
        return sid

    @staticmethod
    def _put_evidence(con, sid, kind, text, check_id, url, locator, origin, stamp):
        eid = digest(dump([sid, kind, text, url, locator]))
        con.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (eid, sid, check_id, kind, text, digest(text), url, dump(locator), origin, stamp))
        return eid

    def add_evidence(self, sid, kind, text, url=None, locator=None, origin='HISTORICAL_IMPORT'):
        with self.connect() as con:
            return self._put_evidence(con, sid, kind, text, None, url, locator or {}, origin, now())

    def source(self, sid):
        with self.connect(readonly=True) as con:
            row = con.execute('SELECT s.* FROM sources s LEFT JOIN source_aliases a ON a.source_id=s.source_id WHERE s.source_id=? OR a.alias=? LIMIT 1', (sid, sid)).fetchone()
            if not row:
                return None
            out = dict(row)
            out['record'] = json.loads(out.pop('record_json'))
            out['authors'] = json.loads(out.pop('authors_json'))
            out.pop('search_text')
            out['checks'] = [dict(r) for r in con.execute('SELECT * FROM access_checks WHERE source_id=? ORDER BY checked_at DESC LIMIT 10', (row['source_id'],))]
            for check in out['checks']:
                check['detail'] = json.loads(check.pop('detail_json'))
            out['evidence'] = [dict(r) for r in con.execute('SELECT * FROM evidence WHERE source_id=? ORDER BY obtained_at DESC LIMIT 20', (row['source_id'],))]
            for item in out['evidence']:
                item['locator'] = json.loads(item.pop('locator_json'))
            return out

    def save_check(self, sid, outcome, *, url=None, final_url=None, http_status=None, content_type=None, body_hash=None, byte_count=None, duration_ms=0, detail=None, passages=()):
        import uuid
        check_id, stamp = uuid.uuid4().hex, now()
        with self.connect() as con:
            con.execute('INSERT INTO access_checks VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                        (check_id, sid, stamp, outcome, http_status, url, final_url, content_type, body_hash, byte_count, duration_ms, dump(detail or {})))
            for p in passages:
                eid=self._put_evidence(con, sid, p.get('kind', 'FULLTEXT_PASSAGE'), p['text'], check_id,
                                       final_url or url, p.get('locator') or {}, 'VERIFIED_FETCH', stamp)
                con.execute('INSERT OR IGNORE INTO evidence_checks VALUES(?,?)',(check_id,eid))
        return check_id

    def save_query(self, provider, query, started, outcome, duration_ms, sids=(), detail=None):
        import uuid
        run_id = uuid.uuid4().hex
        with self.connect() as con:
            con.execute('INSERT INTO query_runs VALUES(?,?,?,?,?,?,?,?)', (run_id, provider, query, started, outcome, len(sids), duration_ms, dump(detail or {})))
            con.executemany('INSERT OR IGNORE INTO query_hits VALUES(?,?,?)', [(run_id, sid, i + 1) for i, sid in enumerate(sids)])
        return run_id

    @staticmethod
    def _terms(query):
        return list(dict.fromkeys(re.findall(r'[\w]+', str(query).casefold())))[:12]

    def search_sources(self, query, limit=10):
        terms = self._terms(query)
        if not terms:
            return []
        clauses = ' AND '.join('instr(lower(search_text),?)>0' for _ in terms)
        with self.connect(readonly=True) as con:
            rows = con.execute(f'SELECT source_id,title,doi,year,venue,publication_type,record_json FROM sources WHERE {clauses} ORDER BY year DESC LIMIT ?', (*terms, min(max(int(limit), 1), 50)*4)).fetchall()
            from research_relevance import assess
            out=[]
            for row in rows:
                item=dict(row);record=json.loads(item.pop('record_json'));assessment=assess(query,record)
                if assessment['eligible']:out.append({**item,'relevance':assessment})
                if len(out)>=limit:break
            return out

    def search_books(self, query, limit=10, book_id=None):
        terms = self._terms(query)
        if not terms:
            return []
        # A 2-character Chinese term cannot use a trigram index. Keep an exact
        # fallback rather than silently returning no results for 自由/友谊.
        indexed = [t for t in terms if len(t) >= 3]
        fts = ' OR '.join('"' + t.replace('"', '""') + '"' for t in indexed)
        clauses, params = ["b.status<>'not_in_catalogue'"], []
        if book_id:
            clauses.append('c.book_id=?');params.append(book_id)
        for term in terms:
            clauses.append('(instr(lower(c.text),?)>0 OR instr(lower(b.title),?)>0 OR instr(lower(b.author),?)>0)')
            params.extend([term] * 3)
        if fts:
            clauses.append('(c.id IN (SELECT rowid FROM chapter_fts WHERE chapter_fts MATCH ?) OR ' + ' OR '.join('(instr(lower(b.title),?)>0 OR instr(lower(b.author),?)>0)' for _ in indexed) + ')')
            params.append(fts)
            for t in indexed:params.extend([t,t])
        sql = 'SELECT c.*,b.title AS book_title,b.author FROM chapters c JOIN books b ON b.id=c.book_id WHERE ' + ' AND '.join(clauses) + ' ORDER BY c.book_id,c.chapter_index LIMIT ?'
        with self.connect(readonly=True) as con:
            rows = con.execute(sql, (*params, min(max(int(limit),1),50))).fetchall()
        out=[]
        for row in rows:
            text=row['text'];positions=[text.casefold().find(t) for t in terms if t in text.casefold()]
            start=max(0,min(positions)-100) if positions else 0
            out.append({'book_id':row['book_id'],'book_title':row['book_title'],'author':row['author'],'chapter_idx':row['chapter_index'],'chapter_title':row['title'],'snippet':text[start:start+600],'start_char':start,'end_char':min(start+600,len(text)),'source_hash':row['source_hash'],'material_role':row['material_role'],'role_basis':row['role_basis'],'reader_url':f"https://deepphilosophy.top/reader/{row['book_id']}?ch={row['chapter_index']}",'indexed_at':row['indexed_at']})
        return out

    def stats(self):
        with self.connect(readonly=True) as con:
            counts={table:con.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in ['books','chapters','passages','sources','provider_records','access_checks','evidence','query_runs','audit_issues']}
            counts['books_by_status']={r[0]:r[1] for r in con.execute('SELECT status,count(*) FROM books GROUP BY status')}
            counts['checks_by_outcome']={r[0]:r[1] for r in con.execute('SELECT outcome,count(*) FROM access_checks GROUP BY outcome')}
            counts['evidence_by_kind']={r[0]:r[1] for r in con.execute('SELECT kind,count(*) FROM evidence GROUP BY kind')}
            counts['documents_with_verified_passages']=con.execute("SELECT count(DISTINCT source_id) FROM evidence WHERE kind='FULLTEXT_PASSAGE' AND origin='VERIFIED_FETCH'").fetchone()[0]
            counts['latest_check_outcomes']={r[0]:r[1] for r in con.execute('SELECT outcome,count(*) FROM access_checks a WHERE checked_at=(SELECT max(checked_at) FROM access_checks b WHERE b.source_id=a.source_id) GROUP BY outcome')}
            build=con.execute('SELECT id,status,started_at,finished_at FROM builds ORDER BY started_at DESC LIMIT 1').fetchone()
            counts['latest_build']=dict(build) if build else None
            counts['current_issues_by_code']={r[0]:r[1] for r in con.execute('SELECT code,count(*) FROM audit_issues WHERE build_id=? GROUP BY code',(build['id'],))} if build else {}
            counts['schema_version']=con.execute('PRAGMA user_version').fetchone()[0]
            return counts

    def passage(self, passage_id):
        with self.connect(readonly=True) as con:
            row=con.execute('SELECT p.*,c.book_id,c.chapter_index,c.title AS chapter_title,c.source_hash,b.title AS book_title,b.author FROM passages p JOIN chapters c ON c.id=p.chapter_id JOIN books b ON b.id=c.book_id WHERE p.id=?',(passage_id,)).fetchone()
            if not row:return None
            result=dict(row)
            result['reader_url']=f"https://deepphilosophy.top/reader/{row['book_id']}?ch={row['chapter_index']}&sec={row['start_block']}"
            return result

    def lexical_results(self, query, terms):
        """Same exact-match ranking contract as the legacy primary tool, from SQLite."""
        import heapq
        from deep_agent_tools import _fold_for_terms, _passage_result
        from routes.agent_tools_retrieval import _canon_score, _cite_label
        hits=[];metadata=[];book_passages={};total=0;scanned=0
        with self.connect(readonly=True) as con:
            books={row['id']:json.loads(row['metadata_json'])['catalogue'] for row in con.execute("SELECT id,metadata_json FROM books WHERE status<>'not_in_catalogue'")}
            for book in books.values():
                hay=_fold_for_terms(f"{book.get('title','')} {book.get('author','')}",terms)
                if all(t in hay for t in terms):
                    metadata.append({'book_id':book['id'],'book_title':book.get('title',''),'author':book.get('author',''),'snippet':'','citation_label':_cite_label(book.get('title'),''),'score':_canon_score(book.get('title','')),'match_type':'book_metadata','evidence_scope':'catalogue','needs_read':True})
            indexed=[t for t in terms if len(t)>=3]
            matching_books=[bid for bid,b in books.items() if any(t in _fold_for_terms(f"{b.get('title','')} {b.get('author','')}",terms) for t in terms)]
            if indexed:
                match=' OR '.join('"'+t.replace('"','""')+'"' for t in indexed)
                condition='id IN (SELECT rowid FROM chapter_fts WHERE chapter_fts MATCH ?)'
                params=[match]
                if matching_books:
                    condition+=' OR book_id IN ('+','.join('?' for _ in matching_books)+')';params+=matching_books
                rows=con.execute('SELECT book_id,chapter_index,title,text FROM chapters WHERE '+condition,params)
            else:rows=con.execute('SELECT book_id,chapter_index,title,text FROM chapters')
            for chapter in rows:
                book=books.get(chapter['book_id'])
                if not book:continue
                scanned+=1;title=book.get('title','');text=chapter['text']
                book_hay=_fold_for_terms(f"{title} {book.get('author','')}",terms)
                remaining=tuple(t for t in terms if t not in book_hay) or terms
                hay=_fold_for_terms(text,remaining)
                if not text or not all(t in hay for t in remaining):continue
                ch_hay=_fold_for_terms(chapter['title'],terms)
                score=sum(t in ch_hay for t in remaining)*30+sum(min(hay.count(t),5) for t in remaining)+_canon_score(title)+sum(t in _fold_for_terms(title,terms) for t in terms)*40+(len(terms)-len(remaining))*10
                row=_passage_result(book,chapter['chapter_index'],chapter['title'],text,remaining,score,query)
                total+=1;previous=book_passages.get(book['id']);count=(previous or {}).get('matched_chapters',0)+1
                if previous is None or score>previous['score']:book_passages[book['id']]={**row,'matched_chapters':count}
                else:previous['matched_chapters']=count
                heapq.heappush(hits,(score,book['id'],chapter['chapter_index'],row))
                if len(hits)>100:heapq.heappop(hits)
        metadata.sort(key=lambda r:(-r['score'],len(r['book_title']),r['book_id']))
        return {'passages':sorted((h[3] for h in hits),key=lambda r:(-r['score'],r['book_id'],r['chapter_idx'])),'metadata':metadata,'scanned_chapters':scanned,'total_passage_hits':total,'book_passages':sorted(book_passages.values(),key=lambda r:-r['score']),'storage':'SQLITE_RESEARCH_INDEX'}

    def check_integrity(self):
        with self.connect(readonly=True) as con:
            return {'integrity':[r[0] for r in con.execute('PRAGMA integrity_check')], 'foreign_key_errors':[tuple(r) for r in con.execute('PRAGMA foreign_key_check')]}

    def backup(self, destination):
        import uuid
        destination=Path(destination)
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True,exist_ok=True)
        temporary=destination.with_name(destination.name+'.partial-'+uuid.uuid4().hex)
        try:
            with self.connect(readonly=True) as source:
                target=sqlite3.connect(temporary)
                try:source.backup(target)
                finally:target.close()
            if destination.exists():raise FileExistsError(destination)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
