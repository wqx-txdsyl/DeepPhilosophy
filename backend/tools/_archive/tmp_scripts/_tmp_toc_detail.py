# -*- coding: utf-8 -*-
"""查看越界/缺失项的详细信息"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BIDS = sys.argv[1:] or ['aacc867ec43c', '53d1b4ff90d2', 'a26240ee8f45']
for bid in BIDS:
    fp = os.path.join(BASE, 'backend/data/book_chapters', bid, 'meta.json')
    if not os.path.exists(fp):
        print('== %s: meta 缺失' % bid)
        continue
    m = json.load(open(fp, encoding='utf-8'))
    n = m.get('chapterCount', 0)
    toc = m.get('toc', [])
    print('== %s %s (%d 章, toc %d 项)' % (bid, m.get('title', '')[:24], n, len(toc)))
    # 越界项
    extra = [t for t in toc if isinstance(t.get('index'), int) and t['index'] >= n]
    for t in extra[:5]:
        print('  越界项:', json.dumps(t, ensure_ascii=False)[:120])
    # 章节文件大小 (判断内容分布)
    sizes = []
    for i in range(n):
        cf = os.path.join(BASE, 'backend/data/book_chapters', bid, '%d.json' % i)
        if os.path.exists(cf):
            sizes.append((i, os.path.getsize(cf)))
        else:
            sizes.append((i, -1))
    print('  章节文件大小: %s' % ['%d:%d' % (i, s) for i, s in sizes][:20])
    # 内容取样: 每章首段
    for i, s in sizes:
        if i > 3 and i != n - 1:
            continue
        cf = os.path.join(BASE, 'backend/data/book_chapters', bid, '%d.json' % i)
        if os.path.exists(cf):
            ch = json.load(open(cf, encoding='utf-8'))
            blocks = ch.get('content', [])
            head = ''
            for b in blocks:
                if isinstance(b, dict) and b.get('value', '').strip():
                    head = b['value'].strip().replace('\n', '')[:35]
                    break
            print('  [%d] %s  %s' % (i, (ch.get('title') or '')[:20], head))
    print()
