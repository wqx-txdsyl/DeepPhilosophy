#!/usr/bin/env python3
"""R2 zcode评审：汇总计算。

规则（任务书冻结口径）：
- 回合贡献：C族 = C精确分/60×100；R族 = (C精确分+R精确分)/100×100
- 先在题内平均规定回合，再对60题等权平均；用未取整数计算，最终显示两位小数
- 各维度只统计适用题（C维：全部60题；R维：仅R族题）
- 通过标记：冻结pass规则 + 裁定后错误状态（confirmed/pending任一存在则不通过）
"""
import json
import glob
import os
import hashlib
import collections

_d = os.path.dirname(os.path.abspath(__file__))
ROOT = _d
while not os.path.isdir(os.path.join(ROOT, 'docs', 'evidence')):
    ROOT = os.path.dirname(ROOT)

REVIEWS = os.path.join(ROOT, 'docs/evidence/benchmark_ledger/zcode_review_r2_20261003/reviews')
OUTDIR = os.path.join(ROOT, 'docs/evidence/benchmark_ledger/zcode_review_r2_20261003')
PACKETS = os.path.join(ROOT, 'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/packets')
KEY = os.path.join(ROOT, 'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/PRIVATE_KEY.json')
ADJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final_adjudication.json')

C_WEIGHTS = {'C1': 10, 'C2': 15, 'C3': 20, 'C4': 10, 'C5': 5}
R_WEIGHTS = {'R1': 15, 'R2': 15, 'R3': 10}


def main():
    key = json.load(open(KEY))
    # 裁定表：packet -> code列表 -> 最终status（pending保持pending；rejected删除）
    adj_rows = json.load(open(ADJ))
    adjudicated = {}  # pid -> list of {code, final_status}
    for r in adj_rows:
        pid = r['packet']
        if r['verdict'] == 'reject':
            st = 'rejected'
        elif r['verdict'].startswith('uphold'):
            st = r['status']
        else:  # downgrade_to_pending
            st = 'pending'
        adjudicated.setdefault(pid, []).append({'code': r['code'], 'original': r['status'], 'final': st})
    # 审计员reject的两条（R86e146、Rc43b1）在adjudication表里是uphold(pending)——按审计员结论改rejected
    for pid, code in (('R86e1466e078e16', 'E4'), ('Rc43b19482278bd', 'E4')):
        for e in adjudicated.get(pid, []):
            if e['code'] == code:
                e['final'] = 'rejected'

    scores = {}
    for f in sorted(glob.glob(os.path.join(REVIEWS, '*.json'))):
        pid = os.path.basename(f)[:-5]
        pkt = json.load(open(os.path.join(PACKETS, pid + '.json')))
        rev = json.load(open(f))
        meta = key[pid]
        fam = pkt['family']
        ratings = rev['ratings']
        c_prec = sum(C_WEIGHTS[k] * ratings[k] / 4 for k in C_WEIGHTS)
        r_prec = None
        if fam == 'R':
            r_prec = sum(R_WEIGHTS[k] * ratings[k] / 4 for k in R_WEIGHTS)
        contrib = c_prec / 60 * 100 if fam == 'C' else (c_prec + r_prec) / 100 * 100
        # 通过标记（裁定后状态）
        errs = adjudicated.get(pid, [])
        active = [e for e in errs if e['final'] in ('confirmed', 'pending')]
        has_u = any(v == 'U' for v in ratings.values())
        c_ok = c_prec >= 45 and all(ratings[k] >= 3 for k in ('C1', 'C2', 'C3'))
        r_ok = True
        if fam == 'R':
            r_ok = (c_prec + r_prec) >= 70 and all(ratings[k] >= 3 for k in ('R1', 'R2', 'R3'))
        passed = c_ok and r_ok and not has_u and not active
        scores[pid] = {
            'packet_id': pid, 'subject_id': meta['subject_id'], 'case_id': meta['case_id'],
            'turn': meta['turn'], 'family': fam,
            'ratings': ratings, 'c_precise': round(c_prec, 4),
            'r_precise': round(r_prec, 4) if r_prec is not None else None,
            'turn_contribution': round(contrib, 4),
            'errors_initial': [{'code': e['code'], 'status': e['original']} for e in errs],
            'errors_adjudicated': errs,
            'has_U': has_u, 'pass': passed,
        }

    # 题内平均回合 -> 60题 -> 对象
    subjects = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in scores.values():
        subjects[s['subject_id']][s['case_id']].append(s)
    aggregate = {}
    for subj, cases in sorted(subjects.items()):
        case_scores = {}
        task_vals = []
        c_vals = []
        r_vals = []
        for cid, turns in cases.items():
            vals = [t['turn_contribution'] for t in turns]
            cs = [t['c_precise'] / 60 * 100 for t in turns]
            c_vals.extend(cs)
            if turns[0]['family'] == 'R':
                rs = [(t['c_precise'] + t['r_precise']) / 100 * 100 for t in turns]
                r_vals.extend(rs)
            case_scores[cid] = {
                'family': turns[0]['family'], 'turns': len(turns),
                'score': round(sum(vals) / len(vals), 4),
                'pass': all(t['pass'] for t in turns),
                'turn_contributions': {str(t['turn']): t['turn_contribution'] for t in turns},
            }
            task_vals.append(sum(vals) / len(vals))
        n_tasks = len(task_vals)
        main = sum(task_vals) / n_tasks
        c_dim = sum(c_vals) / len(c_vals)
        r_dim = sum(r_vals) / len(r_vals) if r_vals else None
        n_pass = sum(1 for c in case_scores.values() if c['pass'])
        n_conf = sum(1 for s in scores.values() if s['subject_id'] == subj
                     for e in s['errors_adjudicated'] if e['final'] == 'confirmed')
        n_pend = sum(1 for s in scores.values() if s['subject_id'] == subj
                     for e in s['errors_adjudicated'] if e['final'] == 'pending')
        aggregate[subj] = {
            'main_score': round(main, 2),
            'c_dimension': round(c_dim, 2),
            'r_dimension': round(r_dim, 2) if r_dim is not None else None,
            'tasks': n_tasks, 'turns': sum(len(v) for v in cases.values()),
            'cases_pass': n_pass,
            'adjudicated_confirmed_errors': n_conf,
            'adjudicated_pending_errors': n_pend,
            'per_case': case_scores,
        }

    out = {
        'version': 'R2-zcode-20261004',
        'rules': {
            'turn_contribution': 'C: C_precise/60*100; R: (C_precise+R_precise)/100*100',
            'aggregation': 'mean turns within task, then equal-weight mean over 60 tasks',
            'pass_rule': 'frozen v1.2 pass rule with adjudicated error statuses (confirmed or pending blocks)',
            'dimension_scopes': 'C dimension over all 60 tasks; R dimension over R-family tasks only',
        },
        'subjects': {k: {kk: vv for kk, vv in v.items() if kk != 'per_case'} for k, v in aggregate.items()},
        'per_case_full': aggregate,
    }
    json.dump(out, open(os.path.join(OUTDIR, 'aggregate.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(scores, open(os.path.join(OUTDIR, 'scores.json'), 'w'), ensure_ascii=False, indent=1)

    print(f'rows: {len(scores)}  subjects: {len(aggregate)}')
    for subj, a in sorted(aggregate.items()):
        print(f"{subj:38s} main={a['main_score']:6.2f}  C={a['c_dimension']:6.2f}  R={a['r_dimension'] if a['r_dimension'] is not None else float('nan'):6.2f}  pass={a['cases_pass']}/60  conf={a['adjudicated_confirmed_errors']} pend={a['adjudicated_pending_errors']}")
    # 完整性
    assert len(scores) == 648
    assert all(len(v) == 60 for v in subjects.values()), {k: len(v) for k, v in subjects.items()}
    assert all(sum(len(ts) for ts in v.values()) == 72 for v in subjects.values())
    dist = collections.Counter()
    for s in scores.values():
        for k, val in s['ratings'].items():
            dist[val] += 1
    print('rating distribution:', dict(sorted(dist.items(), key=lambda x: str(x[0]))))
    print('coverage OK: 648 rows, 9 subjects x 60 tasks x 72 turns')


if __name__ == '__main__':
    main()
