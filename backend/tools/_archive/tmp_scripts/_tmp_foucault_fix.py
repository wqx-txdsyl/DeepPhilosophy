# -*- coding: utf-8 -*-
"""导读福柯: chapterTitles 从章节文件标题重建 (去掉 2 个 OCR 垃圾标题)"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bid = '60eed962806b'
D = os.path.join(BASE, 'backend/data/book_chapters', bid)
meta = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))
n = meta['chapterCount']
titles = []
for i in range(n):
    t = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8')).get('title', '')
    titles.append(t)
print('章节文件标题: %s' % titles)
meta['chapterTitles'] = titles
for pre in (os.path.join(BASE, 'backend/data/book_chapters'),
            os.path.join(BASE, 'app/public/backend/data/book_chapters')):
    json.dump(meta, open(os.path.join(pre, bid, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)

d = json.load(open(os.path.join(BASE, 'backend/data/book_detail', bid + '.json'), encoding='utf-8'))
d['chapterTitles'] = titles
for pre in (os.path.join(BASE, 'backend/data/book_detail'),
            os.path.join(BASE, 'app/public/book_detail')):
    json.dump(d, open(os.path.join(pre, bid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('chapterTitles 重建 %d 项, 双端写回' % len(titles))
