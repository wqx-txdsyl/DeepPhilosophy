#!/usr/bin/env python3
"""Show one task without loading historical failure narratives."""
import argparse
import json
import os
from pathlib import Path
from guard_author_quality_worktree import environment
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE)
TASK = ROOT / 'docs/tasks/author-quality-zcode-2026-10-09'

def main():
    environment()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--queue', choices=('sourceRepairs', 'thinkersToComplete', 'identitiesToResolve', 'contextToReview'), default='thinkersToComplete')
    p.add_argument('--name')
    p.add_argument('--limit', type=int, default=1)
    args = p.parse_args()
    if args.limit < 1 or args.limit > 10:
        p.error('limit 必须在 1 到 10 之间。')
    rows = json.loads((TASK / 'queues.json').read_text())['queues'][args.queue]
    indexed = {x['name'] for x in json.loads((ROOT / 'app/public/philosopher/editorial-index.json').read_text())['profiles'] if x.get('status') == 'source-backed'}
    leases = {json.loads(f.read_text())['name']: json.loads(f.read_text()) for f in (TASK / 'claims').glob('*.json')}
    progress = json.loads((TASK / 'progress.json').read_text())
    completed = {x['name'] if isinstance(x,dict) else x for x in progress.get('completed', {}).get(args.queue, [])}
    selected = []
    for row in rows:
        name = row['name'];lease = leases.get(name, {})
        if args.name and name != args.name:
            continue
        if not args.name and (name in completed or lease.get('state') in ('active','blocked') or row.get('ledgerStatus') in ('blocked','blocker') or args.queue == 'thinkersToComplete' and name in indexed):
            continue
        file = name.replace('/', '-').replace(':', '：') + '.json'
        item = {**row,'claimedState':lease.get('state'),'indexed':name in indexed,'legacy':'app/public/philosopher/data/'+file,'editorial':'app/public/philosopher/editorial/'+file}
        if args.queue == 'sourceRepairs':
            findings = json.loads((TASK / 'source-use-findings.json').read_text())
            item['sourceIssues'] = [{'sourceId':f['source']['id'],'sourceType':f['source']['type'],'url':f['source']['url'],'affectedFields':f['affectedFields']} for f in findings if f['name']==name]
        selected.append(item)
    print(json.dumps({'readOnly':True,'queue':args.queue,'baselineRows':len(rows),'eligibleRows':len(selected),'selected':selected[:args.limit],'note':'这是筛选视图，不等于领取。先核对旧草稿与当前正式包，再用 guard --claim 领取。'},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
