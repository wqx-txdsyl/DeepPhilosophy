# -*- coding: utf-8 -*-
"""批量探测: 哪些章节文件请求返回真 JSON vs vite HTML fallback"""
import urllib.request

def probe(i):
    try:
        with urllib.request.urlopen('http://localhost:5173/backend/data/book_chapters/c0e78ea6f80a/%d.json' % i, timeout=10) as r:
            data = r.read()
            head = data[:30]
            return '%s %dB %s' % (r.status, len(data), 'JSON' if head.startswith(b'{') else repr(head[:20]))
    except Exception as e:
        return 'ERR %s' % e

for i in range(130):
    if i in (0, 5, 17, 23, 28, 38, 39, 55, 82, 83, 84, 89, 90, 95, 97, 105, 111, 129):
        print('%3d: %s' % (i, probe(i)))
