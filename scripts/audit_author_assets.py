"""Audit every published author; field presence is not evidence of scholarly review."""
import argparse
import datetime
import json
import os
from urllib.parse import urlparse
from collections import Counter
from pathlib import Path

from check_author_source_evidence import evaluate as evaluate_source_evidence

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = Path(BASE) / 'app/public'
FIELDS = ('overview', 'life', 'concepts', 'people', 'relations', 'bibliography', 'sources', 'readingRoutes')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def assess(profile, editorial=None, kind='thinker'):
    counts = {field: len(profile.get(field, [])) for field in FIELDS}
    gaps = []
    for field, minimum in [('overview', 3), ('life', 4), ('concepts', 4), ('bibliography', 3), ('people', 2), ('sources', 2), ('readingRoutes', 2)]:
        if field == 'life' and editorial and editorial.get('chronologyPolicy') == 'limited-evidence':
            minimum = 2
        if field == 'bibliography' and editorial and editorial.get('worksPolicy') in ['no-autographs', 'single-surviving-corpus']:
            minimum = 1
        if counts[field] < minimum:
            gaps.append(field)
    errors = []
    if not editorial:
        gaps.append('editorial-review')
    else:
        if not editorial.get('reviewedAt') or not editorial.get('reviewMethod'):
            errors.append('missing-review-record')
        for source in profile.get('sources', []):
            url = urlparse(source.get('url', ''))
            if url.scheme != 'https' or not url.netloc or not source.get('title') or not source.get('type') or not source.get('accessedAt'):
                errors.append('invalid-source-metadata')
        source_ids = {source.get('id') for source in profile.get('sources', [])}
        if None in source_ids or len(source_ids) != counts['sources']:
            errors.append('invalid-source-ids')
        for field in ['life', 'concepts', 'people', 'relations', 'bibliography', 'readingRoutes']:
            for index, item in enumerate(profile.get(field, [])):
                required = {
                    'life': ['year', 'title', 'body'],
                    'concepts': ['name', 'definition', 'source'],
                    'people': ['name', 'role', 'summary'],
                    'relations': ['from', 'to', 'label'],
                    'bibliography': ['title', 'year', 'kind', 'description'],
                    'readingRoutes': ['title', 'description'],
                }[field]
                if any(not str(item.get(key, '')).strip() or item.get(key) is None for key in required):
                    errors.append(f'{field}[{index}]:missing-content')
                if not item.get('sourceRefs') or any(ref not in source_ids for ref in item['sourceRefs']):
                    errors.append(f'{field}[{index}]:missing-source-reference')
        if not editorial.get('overviewSourceRefs') or any(ref not in source_ids for ref in editorial['overviewSourceRefs']):
            errors.append('overview:missing-source-reference')
        if editorial.get('debateAssessment', {}).get('status') not in ['included', 'not-required', 'insufficient-evidence']:
            errors.append('missing-debate-assessment')
        debate = profile.get('debate')
        status = editorial.get('debateAssessment', {}).get('status')
        if status == 'included' and not debate:
            errors.append('debate-assessment-without-body')
        if status != 'included' and debate:
            errors.append('debate-body-without-included-assessment')
        if debate and (not debate.get('sourceRefs') or any(ref not in source_ids for ref in debate['sourceRefs'])):
            errors.append('debate:missing-source-reference')
        if editorial.get('chronologyPolicy') == 'limited-evidence' and not editorial.get('evidenceLimits'):
            errors.append('missing-chronology-explanation')
        if editorial.get('worksPolicy') in ['no-autographs', 'single-surviving-corpus'] and not editorial.get('evidenceLimits'):
            errors.append('missing-textual-evidence-explanation')
    errors.extend(evaluate_source_evidence(profile, editorial, (editorial or {}).get('name', '')))
    level = 'source-backed' if editorial and not gaps and not errors else 'needs-review'
    if kind == 'review':
        level = 'identity-unresolved'
    elif kind != 'thinker':
        level = 'context-material'
    return {'level': level, 'counts': counts, 'debate': bool(profile.get('debate')), 'gaps': gaps, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', default=datetime.date.today().isoformat(), help='审计执行日期（YYYY-MM-DD）；同参数重复运行输出幂等，历史基线文件不受影响')
    args = parser.parse_args()
    people = read(PUBLIC / 'philosophers.json')
    rows = []
    packets = []
    for name, person in people.items():
        filename = name.replace('/', '-').replace(':', '：') + '.json'
        detail = read(PUBLIC / 'philosopher/data' / filename)
        authored = PUBLIC / 'philosopher/editorial' / filename
        editorial = read(authored) if authored.exists() else None
        result = assess(detail['profile'], editorial, person['listingKind'])
        rows.append({'name': name, 'kind': person['listingKind'], 'rank': person.get('rank', 0), **result})
        if editorial:
            packets.append({'name': name, 'path': '/philosopher/editorial/' + filename, 'batch': editorial.get('batch'), 'regionCohort': editorial.get('regionCohort'), 'reviewedAt': editorial.get('reviewedAt'), 'status': result['level'], 'counts': result['counts']})
    summary = {}
    for group in ['all', 'thinker']:
        selected = [row for row in rows if group == 'all' or row['kind'] == group]
        summary[group] = {'records': len(selected), 'levels': dict(Counter(row['level'] for row in selected)), 'coverage': {field: sum(row['counts'][field] > 0 for row in selected) for field in FIELDS}, 'debate': sum(row['debate'] for row in selected), 'missing': dict(Counter(gap for row in selected for gap in row['gaps']))}
    result = {'date': args.date, 'standard': 'author-assets-v1', 'note': 'source-backed 表示本轮按所列来源编写并通过逐项出处和结构检查，不表示学界无争议或完成外部同行评审。争议栏目按证据适用性评估，不以政治争议数量评分。', 'summary': summary, 'records': rows}
    (Path(BASE) / 'docs/author-assets-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    index = {'schemaVersion': 1, 'updatedAt': args.date, 'standard': 'author-assets-v1', 'profiles': packets, 'coverage': summary['thinker']}
    (PUBLIC / 'philosopher/editorial-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    invalid = [row['name'] for row in rows if row['errors']]
    if invalid:
        raise SystemExit('Editorial validation failed: ' + '、'.join(invalid))


if __name__ == '__main__':
    main()
