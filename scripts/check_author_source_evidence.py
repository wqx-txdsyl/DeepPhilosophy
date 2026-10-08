#!/usr/bin/env python3
"""Per-source access-scope gates for editorial packets.

Only packets that declare `accessScope` on any source (this round's repairs and
all new packets) are gated; the frozen baseline is exempt. A packet may list a
source it could not really read, but such a source is recorded as clue-level and
can never sit in `sourceRefs` of body assertions: search snippets and unread
records support nothing; abstract/catalog records support only bibliography
metadata (titles, editions). Plain Wikipedia is always clue-level; a suitable
transcription of a primary text (e.g. Wikisource, typed as
`primary-text-transcription`) is not. Each read source must be traceable to a
research evidence record with per-claim locators, and verdicts separate
confirmation, inference, traditional counts and uncertainty.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_ROOT = Path(BASE) / 'docs/author-research/author-quality-2026-10-09'

ACCESS_SCOPES = {
    'full-text',           # 全文读毕
    'partial-text',        # 读了正文的相关章节或段落
    'abstract-or-catalog', # 仅摘要、编目或馆藏著录
    'search-summary',      # 仅检索摘要
    'unread',              # 未读（访问失败等，须说明原因）
}
# abstract-or-catalog may support bibliography metadata only.
BODY_FIELDS = ('life', 'concepts', 'people', 'relations', 'readingRoutes')
EVIDENCE_VERDICTS = {'confirmed', 'corrected', 'inferred', 'traditional-count', 'uncertain'}
EVIDENCE_VERDICTS_REQUIRING_LOCATOR = {'confirmed', 'corrected', 'inferred', 'traditional-count'}


def packet_is_gated(profile):
    return any('accessScope' in source for source in profile.get('sources', []))


def source_type_tokens(source):
    return set(str(source.get('type', '')).lower().replace('_', '-').split('-'))


def source_is_clue(source):
    """Clue-level no matter what the packet claims about access."""
    tokens = source_type_tokens(source)
    if 'clue' in tokens or 'search' in tokens:
        return True
    host = urlparse(source.get('url', '')).hostname or ''
    return host == 'wikipedia.org' or host.endswith('.wikipedia.org')


def source_access(source):
    return source.get('accessScope')


def source_is_readable(source):
    return source_access(source) in ('full-text', 'partial-text') and not source_is_clue(source)


def referenced_refs(profile, editorial):
    """Yield (sourceId, location) for every sourceRefs entry in the packet."""
    for ref in (editorial or {}).get('overviewSourceRefs', []):
        yield ref, 'overviewSourceRefs'
    for ref in (profile.get('debate') or {}).get('sourceRefs', []):
        yield ref, 'debate'
    for field in BODY_FIELDS + ('bibliography',):
        for index, item in enumerate(profile.get(field, [])):
            for ref in item.get('sourceRefs', []):
                yield ref, f'{field}[{index}]'


def find_evidence_record(name):
    filename = name.replace('/', '-').replace(':', '：') + '.json'
    if RESEARCH_ROOT.exists():
        for path in sorted(RESEARCH_ROOT.glob(f'*/{filename}')):
            try:
                return json.loads(path.read_text(encoding='utf-8')), path
            except (json.JSONDecodeError, OSError):
                continue
    return None, None


def evaluate(profile, editorial, name, evidence=None):
    """Return a list of error codes; empty means the source gates pass."""
    errors = []
    sources = profile.get('sources', [])
    if not packet_is_gated(profile):
        return errors
    by_id = {}
    for index, source in enumerate(sources):
        source_id = source.get('id')
        access = source_access(source)
        if source_id in by_id:
            errors.append(f'sources[{index}]:duplicate-id')
        by_id[source_id] = source
        if access not in ACCESS_SCOPES:
            errors.append(f'sources[{index}]:invalid-access-scope')
            continue
        if not str(source.get('readScope') or source.get('coverage') or '').strip():
            errors.append(f'sources[{index}]:missing-read-scope-note')
        if source_is_clue(source) and source_access(source) in ('full-text', 'partial-text'):
            errors.append(f'sources[{index}]:clue-source-marked-readable')

    referenced = {}
    for ref, location in referenced_refs(profile, editorial):
        referenced.setdefault(ref, []).append(location)
    for source_id, locations in sorted(referenced.items(), key=lambda kv: kv[1][0]):
        source = by_id.get(source_id)
        if source is None:
            continue  # unresolvable refs are already reported by the audit
        # abstract-or-catalog may stand anywhere as support for title/edition metadata;
        # search summaries and unread records support nothing anywhere.
        clue = source_is_clue(source) or source_access(source) in ('search-summary', 'unread')
        for location in locations:
            if clue:
                errors.append(f'{location}:clue-source-referenced:{source_id}')

    record, _ = find_evidence_record(name) if evidence is None else (evidence, None)
    if record is None:
        errors.append('missing-source-evidence-record')
        return errors
    evidence_ids = {source.get('id') for source in record.get('sources', [])}
    for source_id in sorted(referenced):
        source = by_id.get(source_id)
        if source is not None and source_is_readable(source) and source_id not in evidence_ids:
            errors.append(f'evidence-record-missing-source:{source_id}')
    checks = record.get('checks', [])
    if not checks:
        errors.append('evidence-record-without-checks')
    for index, check in enumerate(checks):
        verdict = check.get('verdict')
        if verdict not in EVIDENCE_VERDICTS:
            errors.append(f'evidence-checks[{index}]:invalid-verdict')
        elif verdict in EVIDENCE_VERDICTS_REQUIRING_LOCATOR and not str(check.get('locator') or '').strip():
            errors.append(f'evidence-checks[{index}]:missing-locator')
        if not str(check.get('field') or '').strip() or not str(check.get('claim') or '').strip():
            errors.append(f'evidence-checks[{index}]:missing-field-or-claim')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', help='只检查指定人物（目录键）')
    args = parser.parse_args()
    public = Path(BASE) / 'app/public'
    people = json.loads((public / 'philosophers.json').read_text(encoding='utf-8'))
    targets = [args.name] if args.name else sorted(people)
    failures = {}
    gated = 0
    for name in targets:
        if name not in people:
            raise SystemExit(f'未知目录键：{name}')
        filename = name.replace('/', '-').replace(':', '：') + '.json'
        packet_path = public / 'philosopher/editorial' / filename
        if not packet_path.exists():
            continue
        packet = json.loads(packet_path.read_text(encoding='utf-8'))
        if not packet_is_gated(packet['profile']):
            continue
        gated += 1
        errors = evaluate(packet['profile'], packet, name)
        if errors:
            failures[name] = errors
    print(json.dumps({'gatedPackets': gated, 'failures': failures}, ensure_ascii=False, indent=2))
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()
