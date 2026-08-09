# -*- coding: utf-8 -*-
"""读尼采源 epub 目录页 part0079 完整内容，拿全部章标题"""
import zipfile, re, html as h

z = zipfile.ZipFile('F:/philosophy/西方/弗里德里希·尼采/尼采经典著作及研究丛书（四册全）.epub')
t = z.read('OEBPS/part0079.html').decode('utf-8', errors='ignore') if 'OEBPS/part0079.html' in z.namelist() else ''
if not t:
    for n in z.namelist():
        if 'part0079' in n:
            t = z.read(n).decode('utf-8', errors='ignore')
            break
print('=== part0079 内容 ===')
body = re.sub(r'<[^>]+>', '|', t)
body = h.unescape(body)
lines = [l.strip() for l in body.split('|') if l.strip()]
print('\n'.join(lines[:120]))
