# -*- coding: utf-8 -*-
"""内容级检查: 章节标题/字数/首尾 + FAILED 页空洞定位
用法: python _tmp_content_check.py <bid> [--failed-pages file]
"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BID = sys.argv[1]
D = os.path.join(BASE, 'backend/data/book_chapters', BID)
meta = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))
n = meta.get('chapterCount', 0)

print('== %s (%s) %d 章 ==' % (meta.get('title'), BID, n))
total = 0
empty = []
for i in range(n):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    blocks = ch.get('content', [])
    text = ''.join(b.get('value', '') for b in blocks if isinstance(b, dict))
    total += len(text)
    # 首段 40 字
    head = ''
    for b in blocks:
        if isinstance(b, dict) and b.get('value', '').strip():
            head = b['value'].strip().replace('\n', '')[:40]
            break
    flag = ' <== 空章!' if len(text) < 200 else ''
    if len(text) < 200:
        empty.append(i)
    print('[%2d] %-28s 字数:%-7d 首段: %s%s' % (i, (ch.get('title') or '')[:26], len(text), head, flag))
print('总字数: %d, 空/短章: %s' % (total, empty or '无'))

# toc 类型
print('toc[0] 类型:', type(meta.get('toc', [None])[0]).__name__ if meta.get('toc') else '空')
print('toc 首 3 项:', json.dumps(meta.get('toc', [])[:3], ensure_ascii=False)[:150])
