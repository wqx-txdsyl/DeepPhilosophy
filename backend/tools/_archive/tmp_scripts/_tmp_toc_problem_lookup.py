# -*- coding: utf-8 -*-
"""查看问题书的 meta toc 结构"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BIDS = sys.argv[1:] or ['c0e78ea6f80a', '53d1b4ff90d2', 'a26240ee8f45', 'aacc867ec43c', 'b471f41a78de']
for bid in BIDS:
    fp = os.path.join(BASE, 'backend/data/book_chapters', bid, 'meta.json')
    if not os.path.exists(fp):
        print('== %s: meta 缺失' % bid)
        continue
    m = json.load(open(fp, encoding='utf-8'))
    n = m.get('chapterCount', 0)
    toc = m.get('toc', [])
    print('== %s %s (%d 章, toc %d 项)' % (bid, m.get('title', '')[:20], n, len(toc)))
    if toc and isinstance(toc[0], dict):
        idxs = [t.get('index') for t in toc if isinstance(t.get('index'), int)]
        miss = sorted(set(range(n)) - set(idxs))
        extra = sorted(set(idxs) - set(range(n)))
        noidx = [t for t in toc if 'index' not in t]
        print('  index 缺失 %d 个: %s' % (len(miss), miss[:10]))
        print('  index 越界 %d 个: %s' % (len(extra), extra[:10]))
        print('  无 index 项 %d 个: %s' % (len(noidx), [(t.get('type'), t.get('title', '')[:15]) for t in noidx][:5]))
        types = {}
        for t in toc:
            types[t.get('type', '(无type)')] = types.get(t.get('type', '(无type)'), 0) + 1
        print('  type 分布:', types)
        print('  toc 前 5 项:', json.dumps(toc[:5], ensure_ascii=False)[:250])
    else:
        print('  toc 类型:', type(toc[0]).__name__ if toc else '空', '长度:', len(toc), 'chapterCount:', n)
