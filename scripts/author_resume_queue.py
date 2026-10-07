#!/usr/bin/env python3
"""Read-only, concise resume view for the philosopher audit; never edit its ledger."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE)
QUEUES = ('thinkersToComplete', 'identitiesToResolve', 'contextToReview', 'existingPacketsToPreserve')


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', choices=QUEUES, default=QUEUES[0])
    parser.add_argument('--state', choices=('remaining', 'blocked', 'indexed', 'all'), default='remaining')
    parser.add_argument('--limit', type=int, default=1)
    parser.add_argument('--name', help='Inspect one canonical name, including blocked entries')
    parser.add_argument('--instructions', action='store_true', help='Print current execution sections, excluding historical snapshots and appendices')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if args.instructions:
        text = (ROOT / 'docs/tasks/philosopher-assets-continuation-zcode.md').read_text(encoding='utf-8')
        for number in (0, 3, 5, 6):
            start = text.index(f'## {number}.')
            end = text.find('\n## ', start + 3)
            print(text[start:end if end >= 0 else None].strip(), end='\n\n')
        return
    snapshot = load('docs/tasks/philosopher-assets-remaining-2026-10-03.json')
    progress = load('docs/tasks/philosopher-assets-progress.json')
    index = load('app/public/philosopher/editorial-index.json')
    people = progress.get('people', {})
    if isinstance(people, list):
        people = {item['name']: item for item in people}
    profiles = index.get('profiles', [])
    indexed = set(profiles) if isinstance(profiles, dict) else {item['name'] for item in profiles}
    counts = Counter()
    rows = []
    for baseline in snapshot['queues'][args.queue]:
        name = baseline['name']
        entry = people.get(name, {})
        status = entry.get('status', 'pending')
        blocked = status in ('blocked', 'blocker')
        packet = entry.get('packetPath') or baseline.get('editorialPath')
        draft = entry.get('draftPath')
        evidence = entry.get('evidenceLogPath')
        exists = lambda value: bool(value and (ROOT / value).is_file())
        # Indexing is an observation, not proof of an independent academic review.
        bucket = 'blocked' if blocked else 'indexed' if name in indexed else 'remaining'
        counts[bucket] += 1
        if args.name:
            if name != args.name:
                continue
        elif args.state != 'all' and bucket != args.state:
            continue
        if blocked:
            stage = 'external-review'
        elif name in indexed:
            stage = 'preserve-indexed-packet'
        elif exists(packet) or status in ('validated', 'published', 'preserved'):
            stage = 'check-existing-packet-index-and-release'
        elif exists(draft):
            stage = 'review-existing-draft'
        elif exists(evidence):
            stage = 'resume-source-review'
        else:
            stage = 'verify-identity-and-research'
        rows.append({
            'name': name, 'queue': args.queue, 'ledgerStatus': status, 'resumeStage': stage,
            'contentErrorRecorded': blocked and '1301' in str(entry.get('blocker', '')),
            'indexedLocally': name in indexed, 'cohort': entry.get('cohort') or None,
            'paths': {'legacy': baseline.get('detailPath'), 'packet': packet, 'draft': draft, 'evidence': evidence},
            'existingFiles': {'packet': exists(packet), 'draft': exists(draft), 'evidence': exists(evidence)},
        })
    print(json.dumps({
        'readOnly': True, 'queue': args.queue, 'localCounts': dict(counts),
        'ledgerStatusCounts': dict(Counter(v.get('status', 'pending') for v in people.values())),
        'selected': rows[:args.limit],
        'note': 'Counts describe local files only. Reconcile release evidence before claiming completion; selection does not reserve a task. Failure narratives are not included.',
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
