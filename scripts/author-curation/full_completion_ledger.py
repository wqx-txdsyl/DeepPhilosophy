#!/usr/bin/env python3
"""Initialize and update the 2026-10-15 full-completion round ledger.

The ledger keeps one per-name state entry per queue so any session can
resume the same continuous task without recounting from stale fields:
    pending / researching / evidence-ready / validated / committed /
    published / identity-unresolved / blocked
Historical compatibility is recorded separately (acceptedBy), never as a
pass of this round's claim-evidence review.
"""
import argparse
import datetime
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASK = os.path.join(BASE, 'docs/tasks/author-quality-zcode-2026-10-09')
QUEUES = os.path.join(TASK, '2026-10-15-full-completion-queues.json')
LEDGER = os.path.join(TASK, '2026-10-15-full-completion-ledger.json')

QUEUE_KEYS = ('thinkersToComplete', 'acceptedThinkersEvidenceReview',
              'identityReview', 'contextReview', 'portraitReview')

VALID_STATES = ('pending', 'researching', 'evidence-ready', 'validated',
                'committed', 'published', 'identity-unresolved', 'blocked')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def init(_args=None):
    queues = load(QUEUES)
    ledger = {
        'schemaVersion': 1,
        'taskId': 'author-quality-zcode-2026-10-09',
        'roundId': '2026-10-15-full-completion',
        'initializedAt': now(),
        'lastUpdatedAt': now(),
        'snapshotCommit': queues['publishedCommit'],
        'queueTotals': {},
        'queues': {},
        'publications': [],
        'blocks': [],
        'notes': [],
    }
    for key in QUEUE_KEYS:
        entries = queues['queues'][key]
        ledger['queueTotals'][key] = len(entries)
        ledger['queues'][key] = {}
        for e in entries:
            name = e['name'] if isinstance(e, dict) else e
            record = {'state': 'pending', 'updatedAt': ledger['initializedAt']}
            if isinstance(e, dict):
                for src in ('listingKind', 'region', 'indexedStatus',
                            'editorialExists', 'currentPortrait', 'previousIssueRecord',
                            'snapshotGaps', 'issue', 'action'):
                    if src in e:
                        record[src] = e[src]
            if key == 'acceptedThinkersEvidenceReview':
                record['reviewState'] = 'pending'  # strict this-round claim-evidence review
                record['acceptedBy'] = 'unreviewed-this-round'  # or current-gate / historical-compatibility
            if key == 'portraitReview':
                record['displayDecision'] = 'not-yet-reviewed'  # shown-verified / hidden-unverified / n-a / replaced-verified
            ledger['queues'][key][name] = record
    save(LEDGER, ledger)
    print(json.dumps({k: ledger['queueTotals'][k] for k in QUEUE_KEYS}, ensure_ascii=False))


def update_state(ledger, queue, name, changes):
    if queue not in ledger['queues']:
        raise SystemExit('unknown queue: ' + queue)
    if name not in ledger['queues'][queue]:
        raise SystemExit(f'{name} not in queue {queue}')
    entry = ledger['queues'][queue][name]
    state = changes.get('state')
    if state and state not in VALID_STATES:
        raise SystemExit('invalid state: ' + state)
    entry.update(changes)
    entry['updatedAt'] = now()


def update(args):
    ledger = load(LEDGER)
    changes = {}
    if args.state:
        changes['state'] = args.state
    if args.review_state:
        if 'reviewState' not in ledger['queues'][args.queue].get(args.name, {}):
            raise SystemExit('reviewState only applies to acceptedThinkersEvidenceReview')
        changes['reviewState'] = args.review_state
    if args.accepted_by:
        changes['acceptedBy'] = args.accepted_by
    if args.display_decision:
        if 'displayDecision' not in ledger['queues'][args.queue].get(args.name, {}):
            raise SystemExit('displayDecision only applies to portraitReview')
        changes['displayDecision'] = args.display_decision
    for field, attr in (('outcome', 'outcome'), ('evidencePath', 'evidence_path'),
                        ('releaseCommit', 'release_commit'), ('note', 'note')):
        val = getattr(args, attr, None)
        if val:
            changes[field] = val
    if not changes:
        raise SystemExit('nothing to update')
    update_state(ledger, args.queue, args.name, changes)
    ledger['lastUpdatedAt'] = now()
    save(LEDGER, ledger)
    print(json.dumps(ledger['queues'][args.queue][args.name], ensure_ascii=False))


def record_publication(args):
    ledger = load(LEDGER)
    ledger['publications'].append({
        'batch': args.batch, 'commit': args.commit, 'pushedAt': now(),
        'names': args.names.split(',') if args.names else [],
        'oss': args.oss, 'site': args.site, 'checks': args.checks,
    })
    ledger['lastUpdatedAt'] = now()
    save(LEDGER, ledger)
    print('publications:', len(ledger['publications']))


def record_block(args):
    ledger = load(LEDGER)
    ledger['blocks'].append({
        'name': args.name, 'queue': args.queue, 'stage': args.stage,
        'code': args.code, 'traceId': args.trace, 'detail': args.detail,
        'recordedAt': now(),
    })
    if args.name in ledger['queues'].get(args.queue, {}):
        ledger['queues'][args.queue][args.name]['state'] = 'blocked'
        ledger['queues'][args.queue][args.name]['updatedAt'] = now()
    ledger['lastUpdatedAt'] = now()
    save(LEDGER, ledger)
    print('blocks:', len(ledger['blocks']))


def counts(_args=None):
    ledger = load(LEDGER)
    out = {}
    for key, names in ledger['queues'].items():
        tally = {}
        for entry in names.values():
            state = entry.get('state', 'pending')
            if key == 'acceptedThinkersEvidenceReview':
                state += '/' + entry.get('reviewState', 'pending')
            elif key == 'portraitReview':
                state += '/' + entry.get('displayDecision', 'not-yet-reviewed')
            tally[state] = tally.get(state, 0) + 1
        out[key] = dict(sorted(tally.items()))
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init', help='initialize ledger from the queues snapshot')
    u = sub.add_parser('update', help='update one name in one queue')
    u.add_argument('--queue', required=True)
    u.add_argument('--name', required=True)
    u.add_argument('--state')
    u.add_argument('--review-state')
    u.add_argument('--accepted-by')
    u.add_argument('--display-decision')
    u.add_argument('--outcome')
    u.add_argument('--evidence-path')
    u.add_argument('--release-commit')
    u.add_argument('--note')
    pub = sub.add_parser('publication', help='record a published batch')
    pub.add_argument('--batch', required=True)
    pub.add_argument('--commit', required=True)
    pub.add_argument('--names', default='')
    pub.add_argument('--oss', default='pending')
    pub.add_argument('--site', default='pending')
    pub.add_argument('--checks', default='')
    b = sub.add_parser('block', help='record a genuine external block')
    b.add_argument('--name', required=True)
    b.add_argument('--queue', default='thinkersToComplete')
    b.add_argument('--stage', default='')
    b.add_argument('--code', default='1301')
    b.add_argument('--trace', default='')
    b.add_argument('--detail', default='')
    sub.add_parser('counts', help='show per-queue state tallies')
    args = p.parse_args()
    {'init': init, 'update': update, 'publication': record_publication,
     'block': record_block, 'counts': counts}[args.cmd](args)


if __name__ == '__main__':
    main()
