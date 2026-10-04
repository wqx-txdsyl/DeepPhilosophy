#!/usr/bin/env python3
"""Seal development scoring record R2 (zcode unified re-review); never edits rubric, answers or R1.

Reads the zcode_review_r2_20261003 batch (scores.json / aggregate.json) and emits
frozen_r2_20261004/ in the same schema as R1. Offline only.
"""
import json
import hashlib
import os
import collections
from pathlib import Path

_d = Path(os.path.dirname(os.path.abspath(__file__)))
ROOT = _d.parents[3]  # backend/tools/_tmp/r2_zcode_work -> repo root
BATCH = ROOT / 'docs/evidence/benchmark_ledger/zcode_review_r2_20261003'
OUT = ROOT / 'docs/evidence/benchmark_ledger/frozen_r2_20261004'
PACKETS = ROOT / 'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/packets'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    scores = json.loads((BATCH / 'scores.json').read_text())
    agg = json.loads((BATCH / 'aggregate.json').read_text())
    suite = json.loads((ROOT / 'docs/evidence/phiagent_benchmark_v0_1/suite.json').read_text())
    rules = json.loads((ROOT / 'docs/evidence/rubric_v1_2/RULES_FROZEN.json').read_text())
    primary = sorted({s['case_id'] for s in scores.values()})
    assert len(primary) == 60

    by_subject = collections.defaultdict(list)
    for s in scores.values():
        by_subject[s['subject_id']].append(s)

    labels = {
        'phiagent-0.1.0': ('PhiAgent', 'v0.1.0'), 'phiagent-0.1.1': ('PhiAgent', 'v0.1.1'),
        'phiagent-0.1.2': ('PhiAgent', 'v0.1.2'), 'phiagent-0.1.3': ('PhiAgent', 'v0.1.3'),
        'phiagent-0.1.4': ('PhiAgent', 'v0.1.4'), 'phiagent-0.1.5': ('PhiAgent', 'v0.1.5'),
        'deepseek-browser-run1-20261002': ('DeepSeek', '网页型号未记录 · 深度思考＋联网'),
        'doubao-browser-run1-20261002': ('豆包', '网页型号未记录 · 快速默认档'),
        'chatgpt-work-sol61-high-20261002': ('ChatGPT', 'Work · 6.1 Sol · high'),
    }
    order = ['phiagent-0.1.0', 'phiagent-0.1.1', 'phiagent-0.1.2', 'phiagent-0.1.3',
             'phiagent-0.1.4', 'phiagent-0.1.5', 'deepseek-browser-run1-20261002',
             'doubao-browser-run1-20261002', 'chatgpt-work-sol61-high-20261002']

    subjects = []
    for sid in order:
        rows = sorted(by_subject[sid], key=lambda r: (r['case_id'], r['turn']))
        assert len(rows) == 72 and all('U' not in r['ratings'].values() for r in rows)
        # 维度分：与R1同口径——逐键：题内平均回合等级，再对适用题等权
        dims = {}
        for layer in ('C', 'R'):
            for key in rules[layer]:
                by_case = collections.defaultdict(list)
                for r in rows:
                    if key in r['ratings']:
                        by_case[r['case_id']].append(r['ratings'][key])
                value = sum(sum(v / 4 * 100 for v in vals) / len(vals) for vals in by_case.values()) / len(by_case)
                dims[key] = {'score': value, 'applicable_cases': len(by_case)}
        name, label = labels[sid]
        subj_agg = agg['subjects'][sid]
        serious = collections.Counter()
        for r in rows:
            for e in r['errors_adjudicated']:
                if e['final'] in ('confirmed', 'pending'):
                    serious[e['final']] += 1
        subjects.append({
            'id': sid, 'name': name, 'label': label,
            'kind': 'phiagent' if sid.startswith('phiagent') else 'external',
            'source_review': 'docs/evidence/benchmark_ledger/zcode_review_r2_20261003/scores.json',
            'source_review_sha256': sha(BATCH / 'scores.json'),
            'review_condition': 'zcode unified re-review: single frozen protocol, 648/648 turns independently re-scored; control sample passed; error claims adjudicated with subject-aware receipt-availability rule',
            'reviewed_primary_turns': 72,
            'primary': {'case_count': 60, 'case_ids': primary,
                        'score': agg['subjects'][sid]['main_score'],
                        'lower': agg['subjects'][sid]['main_score'],
                        'upper': agg['subjects'][sid]['main_score']},
            'dimensions': dims,
            'primary_serious_error_records': dict(serious),
            'cases_pass': subj_agg['cases_pass'],
            'rows': [{'id': f"{r['case_id']}-T{r['turn']}", 'packet_id': r['packet_id'],
                      'case_id': r['case_id'], 'turn': r['turn'], 'family': r['family'],
                      'ratings': r['ratings'], 'c_precise': r['c_precise'],
                      'r_precise': r['r_precise'], 'turn_contribution': r['turn_contribution'],
                      'pass': r['pass'],
                      'errors_initial': r['errors_initial'],
                      'errors_adjudicated': r['errors_adjudicated']} for r in rows],
        })

    record = {
        'record_id': 'R2-20261004',
        'status': 'frozen_development_scoring_record',
        'scoring_rubric': '1.2',
        'benchmark_suite': '0.1',
        'primary_label': '统一60题总分（zcode统一重评）',
        'primary_scope': 'Same 60 C/R cases as R1; all 72 turns per subject re-scored under one frozen protocol.',
        'primary_case_ids': primary,
        'primary_turn_count': 72,
        'primary_weighting': 'Each case equal, all specified turns averaged within case; C contribution C/60*100, R contribution (C+R)/100*100. No U in primary. Empty A05 answer retained as zero.',
        'verification_case_ids': [],
        'unrun_fixture_case_ids': ['D01', 'D02', 'D04', 'D05', 'E05'],
        'source_grades_preserved': True,
        'new_answer_runs': 0,
        'automated_evaluator_calibrated': False,
        'quality_acceptance_claim': False,
        'review_limit': 'Single reviewer family (zcode subagents under one frozen protocol, anonymized packets). No inter-rater reliability established; PhiAgent answers reviewed within the producing project (affiliation bias possible). Browser subjects have no tool-receipt layer in capture; execution-fabrication claims therefore capped at pending. Freeze locks the record, not truth or causal/model ranking validity.',
        'replaces': 'R1-20261003 remains frozen and untouched; R2 is the new primary comparison record.',
        'future_update_rule': 'New evidence/review must produce a new named record with reasons; never silently overwrite R1 or R2.',
        'adjudications': json.loads((BATCH / 'source_audit_adjudications.json').read_text()) if (BATCH / 'source_audit_adjudications.json').exists() else [],
        'subjects': subjects,
    }
    return record


def inputs_manifest():
    files = {}
    base = [
        'docs/evidence/rubric_v1_2/RULES_FROZEN.json',
        'docs/evidence/rubric_v1_2/BLIND_PACKETS.json',
        'docs/evidence/rubric_v1_2/BLIND_KEY.json',
        'docs/evidence/rubric_v1_2/PLAN.json',
        'docs/evidence/phiagent_benchmark_v0_1/suite.json',
        'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/PLAN.json',
        'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/PRIVATE_KEY.json',
        'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/system.txt',
        'docs/tasks/2026-10-03-unified-answer-review-r2.md',
    ]
    for f in base:
        files[f] = sha(ROOT / f)
    for p in sorted(PACKETS.glob('*.json')):
        files[str(p.relative_to(ROOT))] = sha(p)
    return files


def create():
    assert not (OUT / 'FREEZE_MANIFEST.json').exists(), 'R2 freeze already exists'
    OUT.mkdir(exist_ok=True)
    record = build()
    (OUT / 'SCORES.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 冻结开发评审记录 R2（zcode统一重评）', '',
             '同一60道分析/研究题、每对象72回合全部由zcode按冻结v1.2统一重评（648/648）。控制样本T1-T6通过；错误指控经主体感知回执可得性规则裁定。R1保持冻结不动。', '',
             '|对象|统一60题总分 /100|C维|R维|通过题数|裁定后严重错误|', '|---|---:|---:|---:|---:|---:|']
    for s in record['subjects']:
        lines.append(f"|{s['name']} {s['label']}|{s['primary']['score']:.2f}|"
                     f"{sum(s['dimensions'][k]['score'] for k in ('C1','C2','C3','C4','C5'))/5:.1f}*|"
                     f"{sum(s['dimensions'][k]['score'] for k in ('R1','R2','R3'))/3:.1f}*|"
                     f"{s['cases_pass']}/60|"
                     f"confirmed {s['primary_serious_error_records'].get('confirmed',0)} / pending {s['primary_serious_error_records'].get('pending',0)}|")
    lines += ['', '*维度列为逐键百分制的简单平均，仅作速览；正式口径见aggregate.json（C/R按贡献公式合成）。', '',
              'R1→R2主要差异：R1为混合方法抽样评审（每对象9-28轮直接复核+模型初评，ChatGPT为全文文档评审），R2为单一冻结协议全量重评。ChatGPT大幅下降主因是R1未做逐轮评审；PhiAgent上升部分反映全量引文核验下的真实完成度，但同项目评审从属关系与单一评审族限制已如实登记，不构成受控排行。', '',
              '完整逐轮等级、裁定后错误记录与hash在[SCORES.json](SCORES.json)。冻结校验见[FREEZE_MANIFEST.json](FREEZE_MANIFEST.json)。',]
    (OUT / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
    manifest = {
        'record_id': record['record_id'],
        'source_files_sha256': inputs_manifest(),
        'record_files_sha256': {n: sha(OUT / n) for n in ['SCORES.json', 'SUMMARY.md']},
        'frozen_rules_modified': False,
        'historical_source_grades_modified': False,
        'r1_record_untouched': True,
        'permitted_future_change': 'New explicit revision record only; never edit these frozen files.',
    }
    (OUT / 'FREEZE_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    print('R2 frozen:', OUT)


if __name__ == '__main__':
    create()
