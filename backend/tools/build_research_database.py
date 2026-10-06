"""Build/refresh the local research index without rewriting any source book JSON."""
import argparse
import json
import os
from pathlib import Path
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from research_store import ResearchStore
from research_ingest import build_library, import_scholarly


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path)
    parser.add_argument('--root',type=Path,default=Path(BASE).parent)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--skip-books',action='store_true')
    parser.add_argument('--skip-scholarly',action='store_true')
    args=parser.parse_args()
    if args.report.exists():raise SystemExit('Refusing to overwrite an existing report')
    store=ResearchStore(args.db);store.initialize();report={}
    if not args.skip_books:report['library']=build_library(store,args.root,lambda c:print(json.dumps(c),flush=True))
    if not args.skip_scholarly:report['scholarly']=import_scholarly(store,args.root)
    report['stats']=store.stats();report['integrity']=store.check_integrity()
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report['stats'],ensure_ascii=False,indent=2))
    print('Report:',args.report)


if __name__=='__main__':main()
