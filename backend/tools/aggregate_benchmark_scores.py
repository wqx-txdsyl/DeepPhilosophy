"""Offline suite-level index over immutable v1.2 ratings; never calls a model.

Task ratings remain on their original scales. This separately versioned report
normalizes only for aggregation, averages turns within each case, then cases.
Unknown and unrun entries produce bounds, never fabricated zero grades.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re

BASE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = BASE.parent
REGISTRY = ROOT / 'docs/evidence/benchmark_ledger/registry.json'
LEDGER = ROOT / 'docs/evaluation/benchmark-ledger.md'
START = '<!-- benchmark-dashboard:start -->'
END = '<!-- benchmark-dashboard:end -->'
REVIEWED = {'Codex targeted review', 'independent_model_development_review'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def turn_bounds(row, rules):
    family = row['family']
    layers = ['K'] if family == 'K' else ['C', 'R'] if family == 'R' else ['C'] if family == 'C' else []
    if not layers:
        raise ValueError('unknown family')
    expected = {key for layer in layers for key in rules[layer]}
    ratings = row['ratings']
    if set(ratings) != expected:
        raise ValueError('missing or extra rating keys')
    maximum = 1 if family == 'K' else 4
    denominator = 4 if family == 'K' else 100 if family == 'R' else 60
    low = high = Fraction(0)
    for key, value in ratings.items():
        if value != 'U' and (type(value) is not int or not 0 <= value <= maximum):
            raise ValueError('invalid frozen rating scale')
        weight = Fraction(1) if family == 'K' else Fraction(rules[key[0]][key]['weight'], 4)
        low += weight * (0 if value == 'U' else value)
        high += weight * (maximum if value == 'U' else value)
    # 0 and maximum are bounds on unknown values, not assigned ratings.
    return low * 100 / denominator, high * 100 / denominator


def mean_bounds(bounds):
    if not bounds:
        return None
    count = len(bounds)
    return sum((v[0] for v in bounds), Fraction()) / count, sum((v[1] for v in bounds), Fraction()) / count


def export(bounds):
    if bounds is None:
        return {'score': None, 'lower': None, 'upper': None}
    return {'score': float(bounds[0]) if bounds[0] == bounds[1] else None,
            'lower': float(bounds[0]), 'upper': float(bounds[1])}


def summarize(rows, cases, rules):
    by_case = {case['id']: {} for case in cases}
    case_map = {case['id']: case for case in cases}
    if len(case_map) != len(cases):
        raise ValueError('duplicate suite case')
    for row in rows:
        cid = row['case_id']
        if cid not in case_map:
            raise ValueError('review contains a case outside the frozen suite')
        match = re.fullmatch(re.escape(cid) + r'-T([1-9]\d*)', row['id'])
        if not match:
            raise ValueError('invalid turn id')
        turn = int(match[1])
        case = case_map[cid]
        questions = [case['prompt'], *case['follow_up_turns']]
        if turn > len(questions) or turn in by_case[cid]:
            raise ValueError('unexpected or duplicate turn')
        if row['family'] != case['rubric_family']:
            raise ValueError('family mismatch')
        if row.get('question', '').strip() != questions[turn - 1].strip():
            raise ValueError('question differs from frozen suite')
        by_case[cid][turn] = row
    results = {}
    for case in cases:
        cid = case['id']; selected = by_case[cid]
        expected = 1 + len(case['follow_up_turns'])
        bounds = [turn_bounds(selected[t], rules) if t in selected else (Fraction(0), Fraction(100))
                  for t in range(1, expected + 1)]
        results[cid] = {'bounds': mean_bounds(bounds), 'present': len(selected), 'expected': expected,
                       'complete': len(selected) == expected,
                       'reviewed': len(selected) == expected and all(r['review_level'] in REVIEWED for r in selected.values())}
    return results


def cohort(result, ids):
    return {'case_count': len(ids), 'case_ids': sorted(ids),
            **export(mean_bounds([result[c]['bounds'] for c in sorted(ids)]))}


def build(registry_path=REGISTRY):
    registry = json.loads(Path(registry_path).read_text())
    for relative, expected in registry['frozen_inputs'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('frozen input changed: ' + relative)
    rules = json.loads((ROOT / registry['rubric']).read_text())
    cases = json.loads((ROOT / registry['suite']).read_text())['cases']
    results = {}; runs = {}
    for entry in registry['versions']:
        version = entry['version']
        if not entry.get('review'):
            runs[version] = {'status': 'not_full_suite_tested', 'score': None}
            continue
        path = ROOT / entry['review']
        if sha(path) != entry['review_sha256']:
            raise ValueError('review changed; register a new review snapshot: ' + version)
        raw = json.loads(path.read_text()); rows = raw['rows']
        result = summarize(rows, cases, rules); results[version] = result
        complete = {cid for cid, item in result.items() if item['complete']}
        errors = Counter(e['status'] for r in rows for e in r.get('errors', []))
        runs[version] = {'status': 'provisional_existing_review_not_calibrated',
            'review_sha256': entry['review_sha256'], 'reviewed_turns': sum(r['review_level'] in REVIEWED for r in rows),
            'total_turns': len(rows), 'serious_error_records': dict(errors),
            'full_frozen_suite': cohort(result, set(result)), 'completed_cases': cohort(result, complete),
            'case_bounds': {cid: {**export(item['bounds']), **{k:v for k,v in item.items() if k!='bounds'}} for cid,item in result.items()},
            'group_bounds': {group: cohort(result, {c for c in result if c[0] == group}) for group in sorted({c[0] for c in result})}}
    if results:
        fixed = registry.get('comparison_cohorts')
        if fixed:
            common = set(fixed['fully_scored_case_ids'])
            paired_reviewed = set(fixed['reviewed_case_ids'])
            eligible = {c['id'] for c in cases if c['manual_prompt_ready']}
            if not paired_reviewed <= common <= eligible:
                raise ValueError('invalid fixed comparison cohort')
        else:
            common = set.intersection(*[{c for c,v in r.items() if v['complete'] and v['bounds'][0]==v['bounds'][1]} for r in results.values()])
            paired_reviewed = {c for c in common if all(r[c]['reviewed'] for r in results.values())}
        for v,r in results.items():
            runs[v]['common_fully_scored_cases'] = cohort(r, common)
            runs[v]['common_independently_reviewed_cases'] = cohort(r, paired_reviewed)
    external_results = {}
    for entry in registry.get('external_baselines', []):
        if not entry.get('review'):
            continue
        path = ROOT / entry['review']
        if sha(path) != entry['review_sha256']:
            raise ValueError('external review changed; register a new snapshot: ' + entry['id'])
        review = json.loads(path.read_text())
        result = summarize(review['rows'], cases, rules)
        complete = {cid for cid, item in result.items() if item['complete']}
        external_results[entry['id']] = {
            'display_name': entry['display_name'], 'model': entry['model_snapshot'],
            'mode': entry['mode'], 'resource_condition': entry['resource_condition'],
            'status': 'provisional_browser_review_not_expert_acceptance' if entry.get('surface') == 'official_web_chat' else 'provisional_document_review_not_live_execution_acceptance',
            'review_method': entry.get('review_method', 'codex_document_review'),
            'review_coverage_label': entry.get('review_coverage_label'),
            'review_sha256': entry['review_sha256'], 'total_turns': len(review['rows']),
            'document_reviewed_turns': review.get('document_reviewed_turns', 0),
            'full_frozen_suite': cohort(result, set(result)),
            'completed_cases': cohort(result, complete),
            # Keep the existing PhiAgent comparison cohorts fixed. A new
            # submission must not silently change historical denominators.
            'common_fully_scored_cases': cohort(result, common) if results else None,
            'common_independently_reviewed_cases': cohort(result, paired_reviewed) if results else None,
            'case_bounds': {cid: {**export(item['bounds']), **{k:v for k,v in item.items() if k!='bounds'}} for cid,item in result.items()}}
    return {'aggregation_version': registry['aggregation_version'], 'scale': 100,
            'registry_sha256': sha(registry_path), 'frozen_input_sha256': registry['frozen_inputs'],
            'method': 'turn mean within case, then equal-weight case macro mean',
            'no_quality_pass_claim': True, 'unknown_bounds_are_not_confidence_intervals': True,
            'runs': runs, 'external_baselines': registry['external_baselines'], 'external_results': external_results}


def render_dashboard(data):
    r21_dir=ROOT/'docs/evidence/benchmark_ledger/frozen_r2_1_20261004'
    if (r21_dir/'FREEZE_MANIFEST.json').exists():
        manifest=json.loads((r21_dir/'FREEZE_MANIFEST.json').read_text())
        if sha(r21_dir/'SCORES.json')!=manifest['record_files_sha256']['SCORES.json']:
            raise ValueError('frozen R2.1 scores changed')
        sealed=json.loads((r21_dir/'SCORES.json').read_text())
        lines=['|对象|统一60题总分 /100|记录|','|---|---:|---|']
        for subject in sealed['subjects']:
            lines.append(f"|{subject['name']} {subject['label']}|{subject['primary']['score']:.2f}|R2.1 已冻结（主记录）|")
        return '\n'.join(lines)
    r2_dir=ROOT/'docs/evidence/benchmark_ledger/frozen_r2_20261004'
    if (r2_dir/'FREEZE_MANIFEST.json').exists():
        manifest=json.loads((r2_dir/'FREEZE_MANIFEST.json').read_text())
        if sha(r2_dir/'SCORES.json')!=manifest['record_files_sha256']['SCORES.json']:
            raise ValueError('frozen R2 scores changed')
        sealed=json.loads((r2_dir/'SCORES.json').read_text())
        lines=['|对象|统一60题总分 /100|记录|','|---|---:|---|']
        for subject in sealed['subjects']:
            lines.append(f"|{subject['name']} {subject['label']}|{subject['primary']['score']:.2f}|R2 已冻结（主记录）|")
        return '\n'.join(lines)
    frozen_dir=ROOT/'docs/evidence/benchmark_ledger/frozen_r1_20261003'
    if (frozen_dir/'FREEZE_MANIFEST.json').exists():
        manifest=json.loads((frozen_dir/'FREEZE_MANIFEST.json').read_text())
        if sha(frozen_dir/'SCORES.json')!=manifest['record_files_sha256']['SCORES.json']:
            raise ValueError('frozen R1 scores changed')
        sealed=json.loads((frozen_dir/'SCORES.json').read_text())
        lines=['|对象|统一60题总分 /100|记录|','|---|---:|---|']
        for subject in sealed['subjects']:
            lines.append(f"|{subject['name']} {subject['label']}|{subject['primary']['score']:.2f}|R1 已冻结|")
        return '\n'.join(lines)

    def number(cohort):
        if cohort['lower'] is None:
            return '—'
        if cohort['score'] is not None:
            return f"{cohort['score']:.2f}"
        return f"{cohort['lower']:.2f}–{cohort['upper']:.2f}"
    def cohort_number(value):
        return f"{number(value)}（{value['case_count']}题）"
    lines = ['|版本或答卷|完整70题指数 /100|已实测题集指数 /100|固定64题子集 /100|固定10题复核子集 /100|评审覆盖|',
             '|---|---|---|---|---|---|']
    for version, run in data['runs'].items():
        if 'full_frozen_suite' not in run:
            lines.append(f'|v{version}|未测全套|—|—|—|—|')
            continue
        full = run['full_frozen_suite']
        full_label = number(full) if full['score'] is not None else '未完成；可取范围 ' + number(full)
        lines.append(f"|v{version}|{full_label}|{cohort_number(run['completed_cases'])}|{cohort_number(run['common_fully_scored_cases'])}|{cohort_number(run['common_independently_reviewed_cases'])}|{run['reviewed_turns']}/{run['total_turns']} 轮|")
    for run in data.get('external_results', {}).values():
        full = run['full_frozen_suite']
        label = number(full) if full['score'] is not None else '未完成；可取范围 ' + number(full)
        coverage = run.get('review_coverage_label') or f"{run['document_reviewed_turns']}/{run['total_turns']} 段文本评审"
        lines.append(f"|{run['display_name']} · {run['model']} {run['mode']}|{label}|{cohort_number(run['completed_cases'])}|{cohort_number(run['common_fully_scored_cases'])}|{cohort_number(run['common_independently_reviewed_cases'])}|{coverage}|")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'docs/evidence/benchmark_ledger/aggregate.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    encoded = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    document = LEDGER.read_text()
    if document.count(START) != 1 or document.count(END) != 1:
        raise SystemExit('Ledger dashboard markers missing or duplicated')
    before, remainder = document.split(START)
    _, after = remainder.split(END)
    updated = before + START + '\n' + render_dashboard(data) + '\n' + END + after
    if args.check:
        if not args.output.exists() or args.output.read_text() != encoded or document != updated:
            raise SystemExit('Aggregate is missing or stale')
        print('Aggregate is reproducible; frozen inputs and review fingerprints match.')
    else:
        args.output.write_text(encoded)
        LEDGER.write_text(updated)
        print(args.output)


if __name__ == '__main__':
    main()
