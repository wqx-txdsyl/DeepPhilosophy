# -*- coding: utf-8 -*-
"""直接探测 backend 8000 对 /backend/... 路径的响应 + 读 vite.config.js 的 proxy 规则"""
import urllib.request

for path in [
    '/backend/data/book_chapters/c0e78ea6f80a/38.json',
    '/backend/data/book_chapters/c0e78ea6f80a/meta.json',
    '/api/health',
]:
    try:
        with urllib.request.urlopen('http://localhost:8000' + path, timeout=10) as r:
            data = r.read()
            print('8000 %-60s %s %dB %s' % (path, r.status, len(data), repr(data[:40])))
    except Exception as e:
        print('8000 %-60s ERR %s' % (path, e))
