# -*- coding: utf-8 -*-
"""curl 验证前端路径 + 抽查章节"""
import urllib.request, json

def get(p):
    with urllib.request.urlopen('http://localhost:5173' + p) as r:
        return r.read().decode('utf-8')

m = json.loads(get('/backend/data/book_chapters/c0e78ea6f80a/meta.json'))
print('meta: toc=%d chapterTitles=%d chapterCount=%d' % (len(m['toc']), len(m['chapterTitles']), m['chapterCount']))
d = json.loads(get('/book_detail/c0e78ea6f80a.json'))
print('detail: toc=%d summary: %s...' % (len(d['toc']), d['summary'][:36]))
for i in (0, 23, 38, 55, 118, 129):
    c = json.loads(get('/backend/data/book_chapters/c0e78ea6f80a/%d.json' % i))
    n = sum(len(b.get('value', '')) for b in c['content'])
    print('%3d %-20s %6d字符 %4d块' % (i, c['title'][:20], n, len(c['content'])))
