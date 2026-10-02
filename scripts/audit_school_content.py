"""Check every published school for structural completeness and editorial risks.

This is a reproducible content audit, not a claim that historical assertions
or translations have all been independently verified.
"""
import argparse
import ast
import json
import os
import re
from collections import Counter
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ('name', 'overview', 'thinkers', 'timeline', 'cihai', 'quotes', 'works', 'conclusion', 'subSchools')


def flatten(items):
    for item in items if isinstance(items, list) else []:
        if isinstance(item, list):
            yield from flatten(item)
        elif isinstance(item, dict):
            yield item


def audit(public):
    results = []
    atlas = json.loads((public / 'gene/atlas.json').read_text(encoding='utf-8'))
    expected = {item['detailFile']: item for item in atlas}
    for path in sorted((public / 'schools/data').glob('school_*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        errors, notes = [], []
        for field in REQUIRED:
            if not data.get(field): errors.append(f'missing:{field}')
        for field in ('thinkers', 'relations', 'timeline', 'cihai', 'quotes', 'works', 'subSchools'):
            if not isinstance(data.get(field, []), list): errors.append(f'type:{field}')
            elif any(not isinstance(item, dict) for item in data.get(field, [])): errors.append(f'item-type:{field}')
        for field, keys in {'thinkers': ('name', 'key'), 'timeline': ('year', 'event', 'detail'), 'cihai': ('word', 'def', 'source'), 'quotes': ('text', 'author'), 'works': ('title', 'author', 'desc'), 'subSchools': ('name', 'desc')}.items():
            for index, item in enumerate(flatten(data.get(field, []))):
                for key in keys:
                    if not item.get(key): errors.append(f'empty:{field}.{index}.{key}')
        for index, thinker in enumerate(flatten(data.get('thinkers', []))):
            if not isinstance(thinker.get('works', []), list): errors.append(f'thinker-works-type:{index}')
        words = [re.split(r'[（(]', item.get('word', ''))[0].replace(' ', '') for item in flatten(data.get('cihai', []))]
        duplicate_words = [word for word, count in Counter(words).items() if count > 1]
        if duplicate_words: notes.append({'duplicateConcepts': duplicate_words})
        names = {person.get('name') for person in flatten(data.get('thinkers', []))}
        external = sorted({rel.get(key) for rel in flatten(data.get('relations', [])) for key in ('from', 'to') if rel.get(key) and rel.get(key) not in names})
        if external: notes.append({'relatedExternalNodes': external})
        if len(data.get('overview', '')) < 250: notes.append('short-overview:manual-review')
        if not data.get('sources'): notes.append('independent-source-review-pending')
        bad_quotes = [i for i, q in enumerate(flatten(data.get('quotes', []))) if q.get('kind') == 'quote' and not (q.get('source') or q.get('sourceUrl'))]
        if bad_quotes: errors.append('direct-quotes-without-source')
        entry = expected.get(path.name)
        if not entry: errors.append('not-in-genealogy')
        elif not (public / entry['image'].lstrip('/')).is_file(): errors.append('missing-hero-image')
        results.append({'name': data.get('name'), 'file': path.name, 'errors': errors, 'reviewNotes': notes,
                        'counts': {field: len(data.get(field, [])) for field in ('thinkers', 'relations', 'timeline', 'cihai', 'quotes', 'works', 'subSchools')},
                        'contentReview': data.get('contentReview')})
    return {'scope': 'All published school JSON, structural checks and editorial risk flags; source review is recorded per school.',
            'schools': len(results), 'errorCount': sum(len(row['errors']) for row in results), 'results': results}


def normalize_legacy(public, exclude):
    changed = []
    for path in sorted((public / 'schools/data').glob('school_*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('name') in exclude: continue
        before = json.dumps(data, ensure_ascii=False)
        for field in ('thinkers', 'relations', 'timeline', 'cihai', 'quotes', 'works', 'subSchools'):
            if isinstance(data.get(field), list): data[field] = list(flatten(data[field]))
        for thinker in data.get('thinkers', []):
            works = thinker.get('works', [])
            if isinstance(works, str):
                try: parsed = ast.literal_eval(works)
                except (ValueError, SyntaxError): parsed = [works]
                thinker['works'] = parsed if isinstance(parsed, list) else [str(parsed)]
        for quote in data.get('quotes', []):
            if not quote.get('kind'):
                quote['kind'] = 'paraphrase'
        if data.get('quote'): data.setdefault('quoteKind', 'paraphrase')
        if data.get('closingQuote'): data.setdefault('closingQuoteKind', 'paraphrase')
        if json.dumps(data, ensure_ascii=False) != before:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            changed.append(data.get('name', path.stem))
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normalize-legacy', action='store_true')
    parser.add_argument('--exclude', nargs='*', default=[])
    parser.add_argument('--output')
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args()
    public = Path(BASE) / 'app/public'
    if args.normalize_legacy: print('规范化：' + '、'.join(normalize_legacy(public, set(args.exclude))))
    report = audit(public)
    if args.output: Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"流派 {report['schools']} · 结构错误 {report['errorCount']}")
    for row in report['results']:
        if row['errors']: print(row['name'] + ': ' + ', '.join(row['errors']))
    if args.strict and report['errorCount']: raise SystemExit(1)


if __name__ == '__main__':
    main()
