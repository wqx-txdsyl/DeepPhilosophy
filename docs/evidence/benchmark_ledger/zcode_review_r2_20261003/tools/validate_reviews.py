#!/usr/bin/env python3
"""校验R2 zcode评审输出完整性：键齐全、值合法、单位ID存在于包、错误字段齐全。"""
import json
import glob
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
ROOT = _d
while not os.path.isdir(os.path.join(ROOT, 'docs')):
    ROOT = os.path.dirname(ROOT)
PACKETS = os.path.join(ROOT, 'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/packets')
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs/evidence/benchmark_ledger/zcode_review_r2_20261003/reviews')

problems = []
n = 0
for f in sorted(glob.glob(os.path.join(OUTDIR, '*.json'))):
    pid = os.path.basename(f)[:-5]
    src = os.path.join(PACKETS, pid + '.json')
    if not os.path.exists(src):
        problems.append(f'{pid}: no source packet')
        continue
    pkt = json.load(open(src))
    r = json.load(open(f))
    n += 1
    keys = pkt['rating_keys']
    if r.get('id') != pid:
        problems.append(f'{pid}: id mismatch')
    rat = r.get('ratings')
    if not isinstance(rat, dict) or set(rat.keys()) != set(keys):
        problems.append(f'{pid}: ratings keys {sorted(rat.keys()) if isinstance(rat, dict) else None} != {sorted(keys)}')
        continue
    unit_ids = {u['id'] for u in pkt.get('answer_units') or []}
    for k, v in rat.items():
        if v not in (0, 1, 2, 3, 4, 'U') or isinstance(v, bool):
            problems.append(f'{pid}: {k}={v!r} invalid')
    reasons = r.get('reasons')
    if not isinstance(reasons, dict) or set(reasons.keys()) != set(keys):
        problems.append(f'{pid}: reasons keys mismatch')
    else:
        for k, v in reasons.items():
            if not isinstance(v, dict) or not v.get('reason'):
                problems.append(f'{pid}: reason {k} empty')
            for uid in v.get('answer_unit_ids') or []:
                if uid not in unit_ids:
                    problems.append(f'{pid}: reason {k} cites unknown unit {uid}')
    audit = r.get('audit')
    if not isinstance(audit, dict) or not all(k in audit for k in ('condition_changes', 'unsupported_bridges', 'source_scope_issues')):
        problems.append(f'{pid}: audit incomplete')
    else:
        for sec in ('condition_changes', 'unsupported_bridges', 'source_scope_issues'):
            for item in audit[sec]:
                if item.get('unit_id') not in unit_ids:
                    problems.append(f'{pid}: audit {sec} unknown unit {item.get("unit_id")}')
    for e in r.get('errors') or []:
        if e.get('code') not in ('E1', 'E2', 'E3', 'E4'):
            problems.append(f'{pid}: error code {e.get("code")}')
        if e.get('status') not in ('confirmed', 'pending'):
            problems.append(f'{pid}: error status {e.get("status")}')
        if not e.get('reference_or_condition') or not e.get('reason'):
            problems.append(f'{pid}: error missing basis')
        if not e.get('answer_unit_ids') and unit_ids:
            problems.append(f'{pid}: error missing units')
        else:
            for uid in e['answer_unit_ids']:
                if uid not in unit_ids:
                    problems.append(f'{pid}: error cites unknown unit {uid}')
    if not r.get('strength'):
        problems.append(f'{pid}: strength missing')
    # 空正文包必须全0
    if pkt.get('answer_char_count') == 0:
        if any(v != 0 for v in rat.values()):
            problems.append(f'{pid}: empty answer but non-zero ratings')
    # 矛盾检查：confirmed E1/E2/E3存在时核心维不应全>=3；E4允许落在R3/C1
    confirmed = [e for e in r.get('errors') or [] if e.get('status') == 'confirmed' and e.get('code') in ('E1', 'E2', 'E3')]
    if confirmed:
        core = ['C1', 'C2', 'C3']
        rcore = ['R1', 'R2']
        if all(isinstance(rat.get(k), int) and rat.get(k) >= 3 for k in core):
            problems.append(f'{pid}: confirmed E1/E2/E3 but C1/C2/C3 all >=3 (suspicious)')
        if pkt['family'] == 'R' and all(isinstance(rat.get(k), int) and rat.get(k) >= 3 for k in rcore):
            problems.append(f'{pid}: confirmed E1/E2/E3 but R1/R2 all >=3 (suspicious)')

print(f'validated {n} reviews')
if problems:
    print(f'{len(problems)} PROBLEMS:')
    for p in problems[:80]:
        print(' -', p)
    sys.exit(1)
print('ALL OK')
