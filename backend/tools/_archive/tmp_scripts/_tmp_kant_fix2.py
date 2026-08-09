# -*- coding: utf-8 -*-
"""康德句读修正: chapterCount=2 是错的, 文件 0-14 共 15 章全在 → meta 重建为 15 章
"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bid = 'aacc867ec43c'
D = os.path.join(BASE, 'backend/data/book_chapters', bid)
meta = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))

# 文件 0-14 的标题
titles = []
for i in range(20):
    fp = os.path.join(D, '%d.json' % i)
    if os.path.exists(fp):
        t = json.load(open(fp, encoding='utf-8')).get('title', '')
        titles.append((i, t))
print('章节文件:')
for i, t in titles:
    print('  [%d] %s' % (i, t[:30]))

n = len(titles)
toc_obj = [{'type': 'chapter', 'title': t, 'index': i} for i, t in titles]
meta['chapterCount'] = n
meta['chapterTitles'] = [t for _, t in titles]
meta['toc'] = toc_obj
print('重建: chapterCount=%d, toc=%d 项' % (n, len(toc_obj)))

for pre in (os.path.join(BASE, 'backend/data/book_chapters'),
            os.path.join(BASE, 'app/public/backend/data/book_chapters')):
    json.dump(meta, open(os.path.join(pre, bid, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# detail 双端
d = json.load(open(os.path.join(BASE, 'backend/data/book_detail', bid + '.json'), encoding='utf-8'))
d['chapterCount'] = n
d['chapterTitles'] = meta['chapterTitles']
d['toc'] = toc_obj
for pre in (os.path.join(BASE, 'backend/data/book_detail'),
            os.path.join(BASE, 'app/public/book_detail')):
    json.dump(d, open(os.path.join(pre, bid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('meta + detail 双端写回完成')

# books.json
bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
for it in items:
    if it.get('id') == bid:
        it['chapterCount'] = n
        break
json.dump(bj, open(os.path.join(BASE, 'app/public/books.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('books.json chapterCount 更新')
