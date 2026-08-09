# -*- coding: utf-8 -*-
"""全量验证失败清单原因分析 v2: 未入库 vs 结构坏"""
import json, os, sys, io, re

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BC = os.path.join(BASE, 'backend/data/book_chapters')
PBC = os.path.join(BASE, 'app/public/backend/data/book_chapters')

# 从 _full_verify_result.txt 解析 FAIL 行 + ✗ 明细
p = os.path.join(BASE, 'backend/tools/_full_verify_result.txt')
lines = io.open(p, encoding='utf-8').read().split('\n')
fails = {}
cur = None
for l in lines:
    m = re.match(r'\[\s*\d+/\d+\] FAIL (.+) ([0-9a-f]{12})$', l)
    if m:
        cur = m.group(2)
        fails.setdefault(cur, [])
        continue
    m2 = re.match(r'\s*✗ (.+)', l)
    if m2 and cur:
        fails[cur].append(m2.group(1))

# books.json 拿 file_type
bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
byid = {it['id']: it for it in (bj if isinstance(bj, list) else bj.get('books', []))}

no_meta, no_dir, txt, structured, unknown = [], [], [], [], []
for bid, rs in fails.items():
    it = byid.get(bid, {})
    if it.get('file_type') == 'txt':
        txt.append((bid, it.get('title', '')))
        continue
    D = os.path.join(BC, bid)
    if not os.path.isdir(D):
        no_dir.append((bid, it.get('title', ''), rs))
        continue
    if not os.path.exists(os.path.join(D, 'meta.json')):
        no_meta.append((bid, it.get('title', ''), rs))
        continue
    structured.append((bid, it.get('title', ''), rs))

print('===== 分类统计 =====')
print('目录都不存在(引擎未入库): %d' % len(no_dir))
for b, t, rs in no_dir:
    print('  %s %s  %s' % (b, t[:20], rs[:3]))
print()
print('目录在但无 meta.json: %d' % len(no_meta))
for b, t, rs in no_meta:
    print('  %s %s  %s' % (b, t[:20], rs[:3]))
print()
print('txt 占位符: %d' % len(txt))
print('入库但结构问题: %d' % len(structured))
for b, t, rs in structured:
    print('  %s %s' % (b, t[:24]))
    for r in rs:
        print('      ✗ %s' % r)
