"""Inspect, verify, back up and export the derived research database."""
import argparse
import json
import os
from pathlib import Path
import sys

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE)
from research_store import ResearchStore,digest


def verify(store,root):
    root=Path(root);result=store.check_integrity();mismatches=[]
    with store.connect(readonly=True) as con:
        for row in con.execute('SELECT book_id,chapter_index,source_path,source_hash FROM chapters'):
            path=root/row['source_path']
            try:ok=path.resolve().is_relative_to((root/'backend/data/book_chapters').resolve()) and digest(path.read_bytes())==row['source_hash']
            except OSError:ok=False
            if not ok:mismatches.append({'book_id':row['book_id'],'chapter_index':row['chapter_index']})
        invalid=con.execute('SELECT count(*) FROM passages p JOIN chapters c ON c.id=p.chapter_id WHERE p.text<>substr(c.text,p.start_char+1,p.end_char-p.start_char)').fetchone()[0]
    result.update(source_hash_mismatches=mismatches,invalid_passage_offsets=invalid)
    result['ok']=result['integrity']==['ok'] and not result['foreign_key_errors'] and not mismatches and not invalid
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',type=Path)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    check=sub.add_parser('check');check.add_argument('--root',type=Path,default=Path(BASE).parent);check.add_argument('--report',type=Path)
    backup=sub.add_parser('backup');backup.add_argument('destination',type=Path)
    export=sub.add_parser('export');export.add_argument('destination',type=Path)
    args=parser.parse_args();store=ResearchStore(args.db)
    if args.command=='status':print(json.dumps(store.stats(),ensure_ascii=False,indent=2))
    elif args.command=='check':
        result=verify(store,args.root)
        if args.report:
            with args.report.open('x') as file:json.dump(result,file,ensure_ascii=False,indent=2)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['ok'] else 1
    elif args.command=='backup':
        store.backup(args.destination);print(args.destination)
    elif args.command=='export':
        args.destination.mkdir(parents=True,exist_ok=False)
        tables=['books','sources','source_aliases','provider_records','access_checks','evidence','evidence_checks','query_runs','query_hits','audit_issues','builds']
        with store.connect(readonly=True) as con:
            for table in tables:
                with (args.destination/(table+'.jsonl')).open('w') as file:
                    for row in con.execute('SELECT * FROM '+table):file.write(json.dumps(dict(row),ensure_ascii=False)+'\n')
        (args.destination/'README.txt').write_text('Metadata and scholarly evidence export. Local chapter text remains authoritative in backend/data/book_chapters; rebuild its derived index with build_research_database.py.\n')
        print(args.destination)
    return 0


if __name__=='__main__':raise SystemExit(main())
