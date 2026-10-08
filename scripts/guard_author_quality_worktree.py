#!/usr/bin/env python3
"""Check the reserved worktree, declared changes, and single-person claims."""
import argparse
from collections import Counter
import datetime
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE).resolve()
TASK = ROOT / 'docs/tasks/author-quality-zcode-2026-10-09'
LOCK = TASK / 'worktree-lock.json'

def git(*args):
    return subprocess.check_output(['git', '-c', 'core.quotePath=false', *args], cwd=ROOT, text=True).strip()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def fail(message):
    raise SystemExit('GUARD FAILED: ' + message)

def allowed(path, patterns):
    for pattern in patterns:
        if pattern.startswith('app/public/') and path.count('/') != pattern.count('/'):
            continue
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False

def append_only(before, after):
    """A mirror edit may only append sources, people, and relations."""
    if set(before) != set(after):
        return False
    for key in before:
        if key != 'profile':
            if before[key] != after[key]:
                return False
            continue
        if set(before[key]) != set(after[key]):
            return False
        for field in before[key]:
            old, new = before[key][field], after[key][field]
            if field not in ('sources', 'people', 'relations'):
                if old != new:
                    return False
            else:
                encode = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)
                if not isinstance(old, list) or not isinstance(new, list) or Counter(map(encode, old)) - Counter(map(encode, new)):
                    return False
    return True

def environment():
    lock = read(LOCK)
    if ROOT != Path(lock['workspace']).resolve() or Path.cwd().resolve() != ROOT:
        fail('必须从锁定的工作树根目录运行；不自动切换目录。')
    if git('rev-parse', '--show-toplevel') != str(ROOT) or git('branch', '--show-current') != lock['branch']:
        fail('工作树或分支不匹配。')
    if subprocess.run(['git', 'merge-base', '--is-ancestor', lock['baseCommit'], 'HEAD'], cwd=ROOT).returncode:
        fail('任务基线不在当前提交历史中。')
    for relative in ('app/public/philosophers.json', 'app/public/books.json'):
        if (ROOT / relative).read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
            fail(relative + ' 尚为 LFS 指针；先按任务书取回数据。')
    return lock

def claims():
    return [read(p) for p in (TASK / 'claims').glob('*.json')]

def claim_file(name):
    return TASK / 'claims' / (hashlib.sha256(name.encode()).hexdigest()[:20] + '.json')

def change_claim(args, lock):
    name = args.claim or args.release or args.block
    catalog = read(ROOT / 'app/public/philosophers.json')
    aliases = read(ROOT / 'scripts/author-curation/roster.json').get('aliases', {})
    canonical = name if name in catalog else aliases.get(name)
    if canonical not in catalog and (args.claim or not claim_file(name).exists()):
        fail('姓名不是当前目录键或可解析别名。')
    folder = TASK / 'claims'
    folder.mkdir(exist_ok=True)
    path = claim_file(name)
    semaphore = path.with_suffix('.lock')
    try:
        fd = os.open(semaphore, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail('该对象的领取记录正在写入；不要覆盖锁文件。')
    try:
        os.close(fd)
        old = read(path) if path.exists() else {}
        if args.claim:
            if old.get('state') == 'blocked':
                fail('对象已阻断，先由外层核对检查点和研究安排。')
            if old.get('state') == 'active' and old.get('owner') != args.owner:
                fail('对象已被其他执行者领取。')
            indexed = {p['name'] for p in read(ROOT / 'app/public/philosopher/editorial-index.json')['profiles'] if p.get('status') == 'source-backed'}
            if canonical in indexed and args.mode not in ('repair', 'mirror', 'portrait'):
                fail('已有资料包，不能以新研究覆盖。')
            if args.mode == 'repair' and name not in lock['repairExistingPackets']:
                fail('不在本轮既有包修复白名单。')
            if args.mode == 'mirror' and not args.reason:
                fail('镜像追加必须先登记相关新包和证据理由。')
            record = {'name': name, 'owner': args.owner, 'mode': args.mode, 'state': 'active', 'reason': args.reason, 'previousModes': sorted(set(old.get('previousModes', []) + ([old['mode']] if old.get('mode') else [])))}
        else:
            if not old:
                fail('对象没有领取记录。')
            if args.release and old.get('owner') != args.owner:
                fail('不能释放别人的领取记录。')
            record = {**old, 'state': 'blocked' if args.block else 'released'}
            if args.block:
                record['failure'] = {'code': args.code or '1301', 'traceId': args.trace, 'stage': args.stage, 'recordedBy': args.owner}
        record['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temp.replace(path)
        print(json.dumps(record, ensure_ascii=False))
    finally:
        semaphore.unlink(missing_ok=True)

def check(args, lock):
    upstream = 'origin/master'
    base = git('merge-base', 'HEAD', upstream)
    changed = set(filter(None, git('diff', '--name-only', '--no-renames', base).splitlines()))
    untracked = set(filter(None, git('ls-files', '--others', '--exclude-standard').splitlines()))
    changed.update(untracked)
    if args.role != 'main':
        changed = set(filter(None, git('diff', '--name-only', '--no-renames', 'HEAD').splitlines())) | untracked
    deleted = set(filter(None, git('diff', '--name-only', '--no-renames', '--diff-filter=D', base).splitlines()))
    records = claims()
    named = {r['name'] for r in records}
    aliases = read(ROOT / 'scripts/author-curation/roster.json').get('aliases', {})
    named |= {aliases[n] for n in list(named) if n in aliases}
    named |= {old for old, target in aliases.items() if target in named}
    file_names = {n.replace('/', '-').replace(':', '：') for n in named}
    mirrors = {r['name'] for r in records if 'mirror' in [r.get('mode'), *r.get('previousModes', [])]}
    known = set(read(ROOT / 'app/public/philosophers.json'))
    frozen = set(filter(None, git('ls-tree', '-r', '--name-only', base, 'app/public/philosopher/editorial').splitlines()))
    for path in sorted(changed):
        if not allowed(path, lock['allowedPaths']):
            fail('越界路径：' + path)
        if path in deleted and path.startswith('app/public/'):
            fail('不得删除公共路径：' + path)
        if (ROOT / path).exists() and ROOT not in (ROOT / path).resolve().parents:
            fail('改动指向工作树之外：' + path)
        if args.role != 'main':
            prefix = 'docs/author-research/author-quality-2026-10-09/'
            if not args.name or not path.startswith(prefix) or Path(path).name != args.name.replace('/', '-').replace(':', '：') + '.json':
                fail('研究或复核角色只许写当前人物的证据、草稿、检查点：' + path)
        if Path(path).parent.as_posix() == 'app/public/philosopher' and Path(path).suffix.lower() in ('.webp', '.jpg', '.png') and Path(path).stem not in file_names:
            fail('肖像未先领取：' + path)
        if path.startswith('app/public/philosopher/editorial/'):
            name = Path(path).stem
            if name not in file_names:
                fail('正式资料包未先领取：' + path)
            if name not in known and name not in lock['repairExistingPackets']:
                fail('正式资料包不是目录人物：' + path)
            if path in frozen and name not in lock['repairExistingPackets']:
                old = json.loads(git('show', base + ':' + path))
                new = read(ROOT / path)
                if name not in mirrors or not append_only(old, new):
                    fail('越权改写已完成资料包：' + path)
    if args.publish_check:
        pointers = []
        for p in (ROOT / 'app/public').rglob('*'):
            if p.is_file():
                with p.open('rb') as f:
                    if f.read(64).startswith(b'version https://git-lfs.github.com/spec/v1'):
                        pointers.append(str(p.relative_to(ROOT)))
        if pointers:
            fail('发布目录仍有 LFS 指针：' + ', '.join(pointers[:8]))
    print(json.dumps({'ok': True, 'workspace': str(ROOT), 'branch': lock['branch'], 'comparisonBase': base, 'changedFiles': len(changed), 'claimedNames': len(named), 'publishPointerCheck': args.publish_check}, ensure_ascii=False))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--publish-check', action='store_true')
    group = p.add_mutually_exclusive_group()
    group.add_argument('--claim')
    group.add_argument('--release')
    group.add_argument('--block')
    p.add_argument('--owner', default='zcode-main')
    p.add_argument('--mode', choices=('research', 'repair', 'mirror', 'identity', 'context', 'portrait'), default='research')
    p.add_argument('--reason', default='')
    p.add_argument('--stage', default='')
    p.add_argument('--code', default='')
    p.add_argument('--trace', default='')
    p.add_argument('--role', choices=('main', 'researcher', 'reviewer'), default='main')
    p.add_argument('--name')
    args = p.parse_args()
    lock = environment()
    if args.claim or args.release or args.block:
        change_claim(args, lock)
    else:
        check(args, lock)

if __name__ == '__main__':
    main()
