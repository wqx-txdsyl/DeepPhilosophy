# -*- coding: utf-8 -*-
"""toc 结构全量审计: 找出真正异常的 toc (index 覆盖缺失/字符串数组/空)"""
import json, os, io, sys
from collections import Counter

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'

bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
targets = [it for it in items if it.get('file_type') != 'txt']

ok = 0
problems = []  # (bid, title, 问题描述)
for it in targets:
    bid = it['id']
    fp = BASE + '/backend/data/book_chapters/%s/meta.json' % bid
    if not os.path.exists(fp):
        problems.append((bid, it.get('title', '')[:20], 'meta.json 缺失'))
        continue
    m = json.load(open(fp, encoding='utf-8'))
    n = m.get('chapterCount', 0)
    toc = m.get('toc', [])
    if not isinstance(toc, list) or not toc:
        problems.append((bid, it.get('title', '')[:20], 'toc 空/非数组'))
        continue
    # 分类项
    first = toc[0]
    if isinstance(first, str):
        # 字符串数组
        if len(toc) != n:
            problems.append((bid, it.get('title', '')[:20], '字符串 toc 长度 %d != chapterCount %d' % (len(toc), n)))
        else:
            ok += 1
        continue
    if not isinstance(first, dict):
        problems.append((bid, it.get('title', '')[:20], 'toc 项类型异常 %s' % type(first).__name__))
        continue
    ch_items = [t for t in toc if t.get('type') in (None, 'chapter') or 'index' in t]
    parts = [t for t in toc if t.get('type') == 'part']
    # chapter 项 index 集合
    idxs = [t.get('index') for t in toc if isinstance(t.get('index'), int)]
    need = set(range(n))
    got = set(idxs)
    missing = need - got
    extra = got - need
    if missing:
        problems.append((bid, it.get('title', '')[:20], 'index 缺失 %d 个 (缺 %s)' % (len(missing), sorted(missing)[:5])))
    elif extra:
        problems.append((bid, it.get('title', '')[:20], 'index 越界 %d 个 (%s)' % (len(extra), sorted(extra)[:5])))
    elif len(idxs) != n and parts:
        # 有 part 且 index 总项数不同但覆盖 OK —— 合法两级结构
        ok += 1
    elif len(toc) != n:
        problems.append((bid, it.get('title', '')[:20], 'toc %d 项 != %d 章 (无 part 结构)' % (len(toc), n)))
    else:
        ok += 1

print('结构正常: %d' % ok)
print('异常: %d' % len(problems))
from collections import defaultdict
by_reason = defaultdict(list)
for bid, t, r in problems:
    by_reason[r.split(' (')[0]].append((bid, t, r))
for reason, lst in sorted(by_reason.items(), key=lambda x: -len(x[1])):
    print()
    print('== %s (%d 本) ==' % (reason, len(lst)))
    for bid, t, r in lst[:40]:
        print('  %s %s  %s' % (bid, t, r))
