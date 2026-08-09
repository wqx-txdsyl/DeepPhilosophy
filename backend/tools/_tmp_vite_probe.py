# -*- coding: utf-8 -*-
"""vite 静态服务异常诊断: 其他书 + 重复请求 + 直连后端"""
import urllib.request

def get(path):
    try:
        with urllib.request.urlopen('http://localhost:5173' + path, timeout=10) as r:
            data = r.read()
            return (r.status, len(data), data[:20])
    except Exception as e:
        return ('ERR', 0, str(e)[:60])

# 1. 其他书的章节文件（工具论 b62e? 或任意已知 bid）
for p in [
    '/backend/data/book_chapters/c0e78ea6f80a/38.json',
    '/backend/data/book_chapters/c0e78ea6f80a/38.json?x=1',
    '/backend/data/book_chapters/c0e78ea6f80a/38.json',
    '/books.json',
    '/book_detail/c0e78ea6f80a.json',
    '/backend/data/book_chapters/c0e78ea6f80a/meta.json',
]:
    s, n, h = get(p)
    print('%-70s %s %dB %s' % (p, s, n, 'JSON' if h.startswith(b'{') else repr(h)))
