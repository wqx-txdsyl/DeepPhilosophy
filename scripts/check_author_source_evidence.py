#!/usr/bin/env python3
"""Per-source access-scope gates for editorial packets.

Whether a packet is gated is decided by packet identity, never by whether the
reading metadata happens to be filled in: packets created after the frozen
baseline, baseline packets whose content has been revised, and this round's
authorized repair list are all gated. Only a baseline packet whose bytes still
match the lock file's frozen content digest stays exempt, explicitly recorded
as historical compatibility; a missing or unreadable lock file is an error,
not an automatic exemption. A packet may list a source it could not really
read, but such a source is recorded as clue-level and can never sit in
`sourceRefs` of body assertions: search snippets and unread records support
nothing; abstract/catalog records support only bibliography metadata (titles,
editions, years), not life, doctrine, lineage or controversy claims. Plain
Wikipedia is always clue-level; a suitable transcription of a primary text
(e.g. Wikisource, typed as `primary-text-transcription`) is not. Each read
source must be traceable to a research evidence record with per-claim
locators, and verdicts rest only on sources actually read at the declared
scope.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_ROOT = Path(BASE) / 'docs/author-research/author-quality-2026-10-09'
LOCK_PATH = Path(BASE) / 'docs/tasks/author-quality-zcode-2026-10-09/worktree-lock.json'

ACCESS_SCOPES = {
    'full-text',           # 全文读毕
    'partial-text',        # 读了正文的相关章节或段落
    'abstract-or-catalog', # 仅摘要、编目或馆藏著录
    'search-summary',      # 仅检索摘要
    'unread',              # 未读（访问失败等，须说明原因）
}
# abstract-or-catalog may support bibliography metadata only.
BIBLIOGRAPHY_ONLY_SCOPES = {'abstract-or-catalog'}
BODY_FIELDS = ('life', 'concepts', 'people', 'relations', 'readingRoutes')
SOURCE_REQUIRED_FIELDS = ('id', 'title', 'url', 'type', 'accessedAt', 'accessScope')
# verdicts that assert fact must cite a source actually read at a readable scope
EVIDENCE_VERDICTS = {'confirmed', 'corrected', 'inferred', 'traditional-count', 'uncertain'}
EVIDENCE_VERDICTS_REQUIRING_LOCATOR = {'confirmed', 'corrected', 'inferred', 'traditional-count'}
EVIDENCE_VERDICTS_REQUIRING_READABLE_SOURCE = {'confirmed', 'corrected', 'inferred'}

_lock_cache = {}


def load_lock(lock=None):
    """Return the trusted baseline lock; missing or broken lock is a hard error."""
    if lock is not None:
        return lock
    if 'lock' in _lock_cache:
        return _lock_cache['lock']
    if not LOCK_PATH.exists():
        raise SystemExit(f'来源门禁找不到可信基线：{LOCK_PATH} 不存在；须提供明确基线上下文，不得自动全免。')
    try:
        lock_data = json.loads(LOCK_PATH.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f'来源门禁无法解析基线锁文件：{exc}')
    _lock_cache['lock'] = lock_data
    return lock_data


def round_repair_names(lock):
    return set((load_lock(lock).get('roundAuthorization') or {}).get('additionalRepairNames') or [])


def editorial_relpath(name):
    filename = str(name or '').replace('/', '-').replace(':', '：')
    return f'app/public/philosopher/editorial/{filename}.json'


def packet_is_gated(profile, name='', lock=None, content=None):
    """Gate by packet identity, not by whether accessScope happens to be filled.

    Gated: this round's authorized repairs, packets absent from the frozen
    baseline (new since the task start or in memory), and baseline packets
    whose current bytes no longer match the frozen digest (revised).
    Historically compatible (explicitly exempt, never silently): an unchanged
    baseline packet verified against the lock file's frozen content digest.
    """
    lock_data = load_lock(lock)
    if name and name in round_repair_names(lock_data):
        return True
    rel = editorial_relpath(name)
    frozen = lock_data.get('frozenEditorialHashes') or {}
    if rel not in frozen:
        return True
    path = Path(BASE) / rel
    if content is None:
        if not path.exists():
            return True
        content = path.read_bytes()
    return hashlib.sha256(content).hexdigest() != frozen[rel]


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


def evaluate(profile, editorial, name, evidence=None, lock=None, content=None):
    """Return a list of error codes; empty means the source gates pass."""
    errors = []
    if editorial is None:
        return errors  # 没有资料包就没有可门禁的对象
    if not packet_is_gated(profile, name, lock=lock, content=content):
        return errors
    sources = profile.get('sources', [])
    by_id = {}
    for index, source in enumerate(sources):
        source_id = source.get('id')
        access = source_access(source)
        if source_id in by_id:
            errors.append(f'sources[{index}]:duplicate-id')
        by_id[source_id] = source
        for field in SOURCE_REQUIRED_FIELDS:
            if not str(source.get(field) or '').strip():
                errors.append(f'sources[{index}]:missing-required-field:{field}')
        if access is None or not str(access).strip():
            continue  # missing accessScope already reported above
        if access not in ACCESS_SCOPES:
            errors.append(f'sources[{index}]:invalid-access-scope')
            continue
        if not str(source.get('readScope') or source.get('coverage') or '').strip():
            errors.append(f'sources[{index}]:missing-read-scope-note')
        if source_is_clue(source) and access in ('full-text', 'partial-text'):
            errors.append(f'sources[{index}]:clue-source-marked-readable')

    referenced = {}
    for ref, location in referenced_refs(profile, editorial):
        referenced.setdefault(ref, []).append(location)
    for source_id, locations in sorted(referenced.items(), key=lambda kv: kv[1][0]):
        source = by_id.get(source_id)
        if source is None:
            continue  # unresolvable refs are already reported by the audit
        # search summaries and unread records support nothing anywhere;
        # abstract-or-catalog supports only bibliography title/edition facts.
        clue = source_is_clue(source) or source_access(source) in ('search-summary', 'unread')
        for location in locations:
            field = location.split('[')[0]
            if field == 'overviewSourceRefs':
                field = 'overview'
            if clue:
                errors.append(f'{location}:clue-source-referenced:{source_id}')
            elif source_access(source) in BIBLIOGRAPHY_ONLY_SCOPES and field != 'bibliography':
                errors.append(f'{location}:abstract-catalog-supports-bibliography-only:{source_id}')

    record, _ = find_evidence_record(name) if evidence is None else (evidence, None)
    if record is None:
        errors.append('missing-source-evidence-record')
        return errors
    evidence_sources = {source.get('id'): source for source in record.get('sources', [])}
    for source_id in sorted(referenced):
        source = by_id.get(source_id)
        if source is not None and source_is_readable(source) and source_id not in evidence_sources:
            errors.append(f'evidence-record-missing-source:{source_id}')
    checks = record.get('checks', [])
    if not checks:
        errors.append('evidence-record-without-checks')
    for index, check in enumerate(checks):
        verdict = check.get('verdict')
        if verdict not in EVIDENCE_VERDICTS:
            errors.append(f'evidence-checks[{index}]:invalid-verdict')
            continue
        if verdict in EVIDENCE_VERDICTS_REQUIRING_LOCATOR and not str(check.get('locator') or '').strip():
            errors.append(f'evidence-checks[{index}]:missing-locator')
        if verdict in EVIDENCE_VERDICTS_REQUIRING_READABLE_SOURCE:
            cited = by_id.get(check.get('sourceId'))
            if cited is None:
                errors.append(f'evidence-checks[{index}]:unknown-source:{check.get("sourceId")}')
            elif not source_is_readable(cited):
                # abstract-or-catalog may stand behind verdicts on bibliography fields only
                # (titles, editions, years); any other field needs an actually read source.
                field = str(check.get('field') or '')
                catalog_ok = (source_access(cited) in BIBLIOGRAPHY_ONLY_SCOPES
                              and 'bibliography' in field)
                if not catalog_ok:
                    errors.append(f'evidence-checks[{index}]:verdict-source-not-readable:{check.get("sourceId")}')
        if not str(check.get('field') or '').strip() or not str(check.get('claim') or '').strip():
            errors.append(f'evidence-checks[{index}]:missing-field-or-claim')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', help='只检查指定人物（目录键）')
    args = parser.parse_args()
    public = Path(BASE) / 'app/public'
    people = json.loads((public / 'philosophers.json').read_text(encoding='utf-8'))
    lock = load_lock()
    targets = [args.name] if args.name else sorted(people)
    failures = {}
    gated = 0
    historical_compat = []
    for name in targets:
        if name not in people:
            raise SystemExit(f'未知目录键：{name}')
        filename = name.replace('/', '-').replace(':', '：') + '.json'
        packet_path = public / 'philosopher/editorial' / filename
        if not packet_path.exists():
            continue
        packet = json.loads(packet_path.read_text(encoding='utf-8'))
        if not packet_is_gated(packet['profile'], name, lock=lock):
            historical_compat.append(name)
            continue
        gated += 1
        errors = evaluate(packet['profile'], packet, name, lock=lock)
        if errors:
            failures[name] = errors
    print(json.dumps({'gatedPackets': gated, 'historicalCompatibilityExempt': len(historical_compat), 'failures': failures}, ensure_ascii=False, indent=2))
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()
