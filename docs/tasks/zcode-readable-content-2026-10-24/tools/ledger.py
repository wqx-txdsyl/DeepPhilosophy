#!/usr/bin/env python3
"""台账追加工具。用法:
python3 ledger.py coverage <objectId> <file> '<json数组: [{path,before,action,after,note}]>'
python3 ledger.py change  <objectId> <summary>
python3 ledger.py validate <objectId> <result> <metricsJson>
python3 ledger.py blocker <objectId> <desc> <nextAction>
python3 ledger.py cursor <objectId>
"""
import json, sys, os, datetime
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime.datetime.now().isoformat(timespec='seconds')
cmd = sys.argv[1]
def append(name, obj):
    with open(os.path.join(TASK, name), 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
if cmd == 'coverage':
    oid, fname = sys.argv[2], sys.argv[3]
    rows = json.load(open(sys.argv[4]))
    for r in rows:
        append('coverage-a.jsonl', {'objectId': oid, 'file': fname, 'fieldPath': r['path'],
            'before': r.get('before',''), 'readStatus': 'read', 'action': r.get('action','rewrite'),
            'after': r.get('after',''), 'factCheck': r.get('note',''), 'verifiedAt': NOW, 'publishStatus': 'local'})
elif cmd == 'change':
    append('changes-a.jsonl', {'objectId': sys.argv[2], 'summary': sys.argv[3], 'at': NOW})
elif cmd == 'validate':
    append('validation-a.jsonl', {'objectId': sys.argv[2], 'result': sys.argv[3], 'metrics': json.loads(sys.argv[4]), 'at': NOW})
elif cmd == 'blocker':
    append('blockers-a.jsonl', {'objectId': sys.argv[2], 'desc': sys.argv[3], 'next': sys.argv[4], 'at': NOW})
elif cmd == 'cursor':
    p = os.path.join(TASK, 'progress-a.json')
    d = json.load(open(p)); d['queue']['cursor'] = sys.argv[2]; d['queue']['completed'].append(sys.argv[2])
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
print('ledger ok:', cmd, sys.argv[2])
