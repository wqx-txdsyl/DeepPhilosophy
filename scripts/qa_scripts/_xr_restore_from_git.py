# -*- coding: utf-8 -*-
"""从 DP git HEAD 恢复 book_chapters/{bid} + book_detail/{bid}.json 到 PA 侧
用法: python _xr_restore_from_git.py <bid>   (PA bc/PA bd 被误伤且 gitignored 时用)
"""
import json, os, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

BID = sys.argv[1]
DP_REPO = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
PA_BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
PA_BD = 'f:/program/Python/PhiAgent/backend/data/book_detail'

def git_show(path):
    r = subprocess.run(['git', '-C', DP_REPO, 'show', 'HEAD:' + path],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout

# 1. 章节目录（ls-tree 列出 HEAD 中该目录所有文件）
ls = subprocess.run(['git', '-C', DP_REPO, 'ls-tree', '-r', 'HEAD',
                     'backend/data/book_chapters/%s' % BID],
                    capture_output=True, text=True).stdout
files = [l.split('\t')[1].strip() for l in ls.splitlines() if l.strip()]
print('HEAD 中 %s 章节文件 %d 个' % (BID, len(files)))
if not files:
    sys.exit('无文件，终止')

dst_dir = os.path.join(PA_BC, BID)
os.makedirs(dst_dir, exist_ok=True)
for f in files:
    raw = git_show(f)
    if raw is None:
        print('  ✗ %s 不存在' % f)
        continue
    with open(os.path.join(dst_dir, os.path.basename(f)), 'wb') as fp:
        fp.write(raw.lstrip(b'\xef\xbb\xbf'))  # 去 BOM
print('  ✓ 章节文件已反写回 PA')

# 2. book_detail
raw = git_show('app/public/book_detail/%s.json' % BID)
if raw is None:
    print('  ⚠ detail 在 git 不存在（可能从未入库）')
else:
    with open(os.path.join(PA_BD, BID + '.json'), 'wb') as fp:
        fp.write(raw.lstrip(b'\xef\xbb\xbf'))
    print('  ✓ detail 已反写回 PA')

# 3. 抽查：与 HEAD 比对 md5
import hashlib
def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:10]
mism = 0
for f in files:
    base = os.path.basename(f)
    pa_p = os.path.join(dst_dir, base)
    head_raw = git_show(f).lstrip(b'\xef\xbb\xbf')
    if md5(pa_p) != hashlib.md5(head_raw).hexdigest()[:10]:
        print('  ✗ %s md5 不一致' % base)
        mism += 1
print('校验: %s' % ('✓ 全部一致' if mism == 0 else '✗ %d 不一致' % mism))
