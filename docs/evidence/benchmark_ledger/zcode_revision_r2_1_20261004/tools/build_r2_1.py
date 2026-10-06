#!/usr/bin/env python3
"""R2.1定向修订：应用revisions到R2 scores，修正维度公式，产出aggregate与冻结记录。

独立于R2冻结文件；未重审行显式继承。只读R2记录，不写它。
"""
import json
import hashlib
import os
import collections
from pathlib import Path

_d = Path(os.path.abspath(__file__)).parent  # <batch>/tools
BATCH = _d.parent                              # zcode_revision_r2_1_20261004
R2BATCH = BATCH.parent / 'zcode_review_r2_20261003'
ROOT = BATCH.parent.parent                     # docs/evidence/benchmark_ledger -> ...
while not (ROOT / 'docs' / 'evidence').is_dir():
    ROOT = ROOT.parent
OUT = ROOT / 'docs/evidence/benchmark_ledger/frozen_r2_1_20261004'
KEY = ROOT / 'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/PRIVATE_KEY.json'
C_WEIGHTS = {'C1': 10, 'C2': 15, 'C3': 20, 'C4': 10, 'C5': 5}
R_WEIGHTS = {'R1': 15, 'R2': 15, 'R3': 10}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_scores():
    r2scores = json.loads((R2BATCH / 'scores.json').read_text())
    key = json.loads(KEY.read_text())
    revs = {}
    for f in sorted((BATCH / 'revisions').glob('*.json')):
        r = json.loads(f.read_text())
        revs[r['packet_id']] = r
    scores = {}
    ndim_changed = 0
    for pid, s in r2scores.items():
        ratings = dict(s['ratings'])
        changes = {}
        errs_final = [dict(e) for e in s['errors_adjudicated']]
        revised = False
        if pid in revs:
            rev = revs[pid]
            revised = True
            for dim, ch in (rev.get('changes') or {}).items():
                assert int(ch['old']) == ratings[dim], (pid, dim)
                ratings[dim] = int(ch['new'])
                ndim_changed += 1
                changes[dim] = {'old': ch['old'], 'new': ch['new'],
                                'old_basis_flaw': ch.get('old_basis_flaw'), 'new_reason': ch.get('new_reason')}
            for er in rev.get('errors_revised') or []:
                code = er['code']
                if er['new_status'] == 'removed':
                    errs_final = [e for e in errs_final if e['code'] != code]
                else:
                    for e in errs_final:
                        if e['code'] == code:
                            e['final'] = er['new_status'] if er['new_status'] in ('confirmed', 'pending') else 'withdrawn_audit'
        fam = s['family']
        c_prec = sum(C_WEIGHTS[k] * ratings[k] / 4 for k in C_WEIGHTS)
        r_prec = sum(R_WEIGHTS[k] * ratings[k] / 4 for k in R_WEIGHTS) if fam == 'R' else None
        contrib = c_prec / 60 * 100 if fam == 'C' else (c_prec + r_prec) / 100 * 100
        active = [e for e in errs_final if e['final'] in ('confirmed', 'pending')]
        has_u = any(v == 'U' for v in ratings.values())
        c_ok = c_prec >= 45 and all(ratings[k] >= 3 for k in ('C1', 'C2', 'C3'))
        r_ok = True
        if fam == 'R':
            r_ok = (c_prec + r_prec) >= 70 and all(ratings[k] >= 3 for k in ('R1', 'R2', 'R3'))
        meta = key[pid]
        scores[pid] = {
            'packet_id': pid, 'subject_id': s['subject_id'], 'case_id': s['case_id'], 'turn': s['turn'],
            'family': fam, 'ratings': ratings,
            'c_precise': round(c_prec, 4), 'r_precise': round(r_prec, 4) if r_prec is not None else None,
            'turn_contribution': round(contrib, 4),
            'errors_final': errs_final, 'has_U': has_u,
            'pass': c_ok and r_ok and not has_u and not active,
            'revised': revised, 'dimension_changes': changes,
            'inherited': not revised,
        }
    print('rows:', len(scores), 'revised:', sum(1 for s in scores.values() if s['revised']), 'dim changes:', ndim_changed)
    return scores


def aggregate(scores):
    subjects = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in scores.values():
        subjects[s['subject_id']][s['case_id']].append(s)
    agg = {}
    for sid, cases in sorted(subjects.items()):
        case_scores, task_vals, c_dim_vals, r_dim_vals = {}, [], [], []
        for cid, turns in cases.items():
            vals = [t['turn_contribution'] for t in turns]
            # C维/R维：逐键题内平均→适用题等权（修正后的公式）
            case_scores[cid] = {'family': turns[0]['family'], 'turns': len(turns),
                                'score': round(sum(vals) / len(vals), 4),
                                'pass': all(t['pass'] for t in turns),
                                'turn_contributions': {str(t['turn']): t['turn_contribution'] for t in turns}}
            task_vals.append(sum(vals) / len(vals))
            for k in C_WEIGHTS:
                c_dim_vals.append(sum(t['ratings'][k] / 4 * 100 for t in turns) / len(turns))
            if turns[0]['family'] == 'R':
                for k in R_WEIGHTS:
                    r_dim_vals.append(sum(t['ratings'][k] / 4 * 100 for t in turns) / len(turns))
        c_dim = sum(c_dim_vals) / len(c_dim_vals)
        r_dim = sum(r_dim_vals) / len(r_dim_vals)
        # R/40研究维（修正标签）
        r40_vals = []
        for cid, turns in cases.items():
            if turns[0]['family'] == 'R':
                r40_vals.append(sum(sum(t['ratings'][k] / 4 * 100 for k in R_WEIGHTS) / len(turns) for k in [0]) / 1 if False else sum(t['r_precise'] / 40 * 100 for t in turns) / len(turns))
        agg[sid] = {'main_score': round(sum(task_vals) / len(task_vals), 2),
                    'c_dimension_c60': round(c_dim, 2), 'r_dimension_r40': round(r_dim, 2),
                    'tasks': len(task_vals), 'cases_pass': sum(1 for c in case_scores.values() if c['pass']),
                    'per_case': case_scores}
    return agg


def freeze(scores, agg):
    assert not (OUT / 'FREEZE_MANIFEST.json').exists()
    OUT.mkdir(exist_ok=True)
    (BATCH / 'scores.json').write_text(json.dumps(scores, ensure_ascii=False, indent=1))
    (BATCH / 'aggregate.json').write_text(json.dumps(
        {'version': 'R2.1-20261004', 'dimension_convention': 'per-key: mean turns within case, equal weight over applicable cases; C/60, R/40 (fixed from R2 aggregate)',
         'subjects': {k: {kk: vv for kk, vv in v.items() if kk != 'per_case'} for k, v in agg.items()},
         'per_case_full': agg}, ensure_ascii=False, indent=1))
    key = json.loads(KEY.read_text())
    labels = {'phiagent-0.1.0': ('PhiAgent', 'v0.1.0'), 'phiagent-0.1.1': ('PhiAgent', 'v0.1.1'),
              'phiagent-0.1.2': ('PhiAgent', 'v0.1.2'), 'phiagent-0.1.3': ('PhiAgent', 'v0.1.3'),
              'phiagent-0.1.4': ('PhiAgent', 'v0.1.4'), 'phiagent-0.1.5': ('PhiAgent', 'v0.1.5'),
              'deepseek-browser-run1-20261002': ('DeepSeek', '网页型号未记录 · 深度思考＋联网'),
              'doubao-browser-run1-20261002': ('豆包', '网页型号未记录 · 快速默认档'),
              'chatgpt-work-sol61-high-20261002': ('ChatGPT', 'Work · 6.1 Sol · high')}
    by_subj = collections.defaultdict(list)
    for s in scores.values():
        by_subj[s['subject_id']].append(s)
    subjects = []
    for sid in labels:
        rows = sorted(by_subj[sid], key=lambda r: (r['case_id'], r['turn']))
        dim = {}
        for kk in [*C_WEIGHTS, *R_WEIGHTS]:
            bycase = collections.defaultdict(list)
            for r in rows:
                if kk in r['ratings']:
                    bycase[r['case_id']].append(r['ratings'][kk])
            dim[kk] = {'score': sum(sum(v / 4 * 100 for v in vs) / len(vs) for vs in bycase.values()) / len(bycase),
                       'applicable_cases': len(bycase)}
        a = agg[sid]
        serious = collections.Counter(e['final'] for r in rows for e in r['errors_final'] if e['final'] in ('confirmed', 'pending'))
        name, label = labels[sid]
        subjects.append({'id': sid, 'name': name, 'label': label, 'kind': 'phiagent' if sid.startswith('phiagent') else 'external',
                         'review_condition': 'R2.1 targeted revision of R2: protocol fix (no zero-receipt inference for capture-less browser subjects; Doubao banner excluded as product UI; empty answer not E4) + dimension formula fix; un-revised rows explicitly inherited',
                         'primary': {'case_count': 60, 'score': a['main_score'], 'lower': a['main_score'], 'upper': a['main_score']},
                         'dimensions': dim, 'cases_pass': a['cases_pass'],
                         'primary_serious_error_records': dict(serious),
                         'rows': [{k: r[k] for k in ('packet_id', 'case_id', 'turn', 'family', 'ratings', 'turn_contribution', 'pass', 'revised', 'inherited', 'dimension_changes', 'errors_final')} for r in rows]})
    record = {'record_id': 'R2.1-20261004', 'status': 'frozen_development_scoring_record',
              'revises': 'R2-20261004 (retained frozen)', 'revision_type': 'targeted_revision_not_full_rereview',
              'scoring_rubric': '1.2', 'benchmark_suite': '0.1',
              'primary_scope': 'Same 60 C/R cases; 72 turns/subject; 73 rows re-examined under corrected protocol, rest inherited.',
              'protocol_fixes': ['zero-receipt cannot ground non-execution for capture-less browser subjects (ruling c withdrawn)',
                                 'Doubao banner = product UI, excluded from model-content evaluation (17 packets)',
                                 'empty answer: completeness defect, not E4',
                                 'J01-T4 condition-fidelity recheck (fabricated states)',
                                 'A04-T1 hypothesis-vs-fact attribution line',
                                 'dimension aggregation fixed to per-key case-equal C/60 and R/40'],
              'rows_revised': sum(1 for s in scores.values() if s['revised']),
              'rows_inherited': sum(1 for s in scores.values() if not s['revised']),
              'review_limit': 'Same single-reviewer-family limits as R2; targeted revision, not full re-review; not a controlled ranking.',
              'subjects': subjects}
    (OUT / 'SCORES.json').write_text(json.dumps(record, ensure_ascii=False, indent=1))
    lines = ['# 冻结修订记录 R2.1（R2定向修订）', '',
             '对R2的定向修订：修正协议判据（浏览器主体零回执不作未执行证据；豆包横幅按产品UI剥离；空答不列E4）、重审J01-T4条件保真与A04-T1假设边界、修正维度汇总公式。未重审行显式继承R2。', '',
             '|对象|R2.1主分|R2主分|通过题数|', '|---|---:|---:|---:|']
    r2 = json.loads((ROOT / 'docs/evidence/benchmark_ledger/frozen_r2_20261004/SCORES.json').read_text())
    r2m = {s['id']: s['primary']['score'] for s in r2['subjects']}
    for s in subjects:
        lines.append(f"|{s['name']} {s['label']}|{s['primary']['score']:.2f}|{r2m[s['id']]:.2f}|{s['cases_pass']}/60|")
    lines += ['', f"修订{record['rows_revised']}行、继承{record['rows_inherited']}行；维度改为按题等权C/60与R/40口径。协议、逐轮理由（R2 reviews+R2.1 revisions）与本记录全部纳入冻结清单。R1、R2冻结文件未动。", '',
              '完整数据：[SCORES.json](SCORES.json)；修订留痕：[../zcode_revision_r2_1_20261004/revisions/](../zcode_revision_r2_1_20261004/revisions/)；协议：[../zcode_revision_r2_1_20261004/protocol_supplement.md](../zcode_revision_r2_1_20261004/protocol_supplement.md)。']
    (OUT / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
    src = {}
    LEDGER = ROOT / 'docs/evidence/benchmark_ledger'
    for rel in ['zcode_revision_r2_1_20261004/protocol_supplement.md', 'zcode_review_r2_20261003/tools/protocol.md',
                'zcode_review_r2_20261003/reviews', 'zcode_revision_r2_1_20261004/revisions',
                'zcode_review_r2_20261003/source_audit_adjudications.json']:
        p = LEDGER / rel
        if p.is_dir():
            for f in sorted(p.glob('*.json')):
                src[str(f.relative_to(ROOT))] = sha(f)
        else:
            src[str(p.relative_to(ROOT))] = sha(p)
    for f in ['docs/tasks/2026-10-03-unified-answer-review-r2.md',
              'docs/evaluation/r2-handoff-audit-2026-10-04.md',
              'docs/evidence/rubric_v1_2/RULES_FROZEN.json']:
        src[f] = sha(ROOT / f)
    (OUT / 'FREEZE_MANIFEST.json').write_text(json.dumps({
        'record_id': record['record_id'], 'source_files_sha256': src,
        'record_files_sha256': {n: sha(OUT / n) for n in ['SCORES.json', 'SUMMARY.md']},
        'r1_r2_untouched': True, 'permitted_future_change': 'New explicit revision record only.'}, ensure_ascii=False, indent=1))
    print('R2.1 frozen at', OUT)
    for sid, a in agg.items():
        print(f"{sid:38s} {a['main_score']:6.2f}  (R2: {r2m[sid]:.2f})  pass={a['cases_pass']}/60  C/60={a['c_dimension_c60']}  R/40={a['r_dimension_r40']}")


if __name__ == '__main__':
    sc = build_scores()
    freeze(sc, aggregate(sc))
