"""Serialize publication by the two explicitly authorized book workers."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time

DEFAULT = Path('/Users/sen/.codex/visualizations/2026/10/20/01a1598c-e015-7a02-ab1f-9042a131a4eb/book-quality-round-20261024/publish-lock')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['acquire', 'status', 'release'])
    p.add_argument('--owner', choices=['codex-books', 'zcode-proofread'])
    p.add_argument('--lock-dir', type=Path, default=DEFAULT)
    a = p.parse_args()
    lock = a.lock_dir
    if a.action == 'status':
        print((lock / 'owner.json').read_text() if (lock / 'owner.json').exists() else json.dumps({'locked': lock.exists()}))
        return
    if not a.owner:
        p.error('--owner is required')
    if a.action == 'acquire':
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock.mkdir()
        except FileExistsError:
            raise SystemExit('Publication already locked; inspect status, do not steal or expire the lock.')
        (lock / 'owner.json').write_text(json.dumps({'owner': a.owner, 'pid': os.getpid(), 'acquiredAt': time.time(), 'workspace': str(Path.cwd())}, indent=2))
        print(json.dumps({'acquired': True, 'owner': a.owner}))
    else:
        if not (lock / 'owner.json').exists():
            raise SystemExit('Missing receipt; inspect manually instead of deleting the lock.')
        receipt = json.loads((lock / 'owner.json').read_text())
        if receipt['owner'] != a.owner:
            raise SystemExit('Lock belongs to the other worker; release refused.')
        shutil.rmtree(lock)
        print(json.dumps({'released': True, 'owner': a.owner}))

if __name__ == '__main__':
    main()
