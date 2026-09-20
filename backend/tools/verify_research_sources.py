"""Discover and verify scholarly source accessibility, preserving every attempt."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE)
from research_store import ResearchStore
from research_providers import PROVIDERS, discover, provider_status
from research_access import verify_source


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path)
    parser.add_argument('--query',action='append',default=[])
    parser.add_argument('--providers',nargs='+',choices=PROVIDERS,default=list(PROVIDERS))
    parser.add_argument('--source-id',action='append',default=[])
    parser.add_argument('--limit',type=int,default=5)
    parser.add_argument('--verify-limit',type=int,default=10)
    parser.add_argument('--open-access-only',action='store_true',help='Filter OpenAlex discovery to provider-claimed OA; still verify actual content')
    parser.add_argument('--workers',type=int,choices=[1,2,3],default=2)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if args.report.exists():raise SystemExit('Refusing to overwrite existing report')
    if not 0<=args.verify_limit<=100:raise SystemExit('verify-limit must be 0..100')
    store=ResearchStore(args.db);store.initialize();report={'providers':provider_status(),'discoveries':[],'verifications':[]}
    def save():
        args.report.parent.mkdir(parents=True,exist_ok=True)
        temporary=args.report.with_suffix('.tmp');temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2));temporary.replace(args.report)
    save();sids=list(args.source_id)
    for q in args.query:
        result=discover(store,q,args.providers,args.limit,open_access_only=args.open_access_only);report['discoveries'].append(result);sids.extend(result['source_ids']);save();print(json.dumps(result,ensure_ascii=False),flush=True)
    sids=list(dict.fromkeys(sids))
    if not args.source_id:
        sids.sort(key=lambda sid: not bool(store.source(sid)['record'].get('full_text_candidates')))
    sids=sids[:args.verify_limit]
    def verify(sid):return verify_source(store,sid,query=' '.join(args.query))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(verify,sids):
            report['verifications'].append(result);save();print(json.dumps(result,ensure_ascii=False),flush=True)
    report['stats']=store.stats();save();print('Report:',args.report,flush=True)


if __name__=='__main__':main()
