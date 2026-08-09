# -*- coding: utf-8 -*-
"""复现 extract 的 chapter_entries 标题生成, 找 'MS ' 从哪来"""
import zipfile, re
from bs4 import BeautifulSoup
from urllib.parse import unquote

EP = r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub'
_LVL_PAT = re.compile(r'(第[一二三四五六七八九十百\d]+[部卷编篇章节回讲])')

def _clean_title(t):
    if len(t) <= 60:
        return t
    m = list(_LVL_PAT.finditer(t))
    if not m:
        return t[:40] + ('…' if len(t) > 40 else '')
    end = m[1].start() if len(m) > 1 else min(len(t), m[0].start() + 30)
    return t[:end].strip()

with zipfile.ZipFile(EP) as z:
    ncx = BeautifulSoup(z.read('toc.ncx').decode('utf-8', 'ignore'), 'xml')
    tocs = []
    for np in ncx.find_all('navPoint'):
        lab = np.find('navLabel'); c = np.find('content')
        if lab and c:
            tocs.append(_clean_title(lab.text.strip()))
    print('ncx 条目总数:', len(tocs))
    for i, t in enumerate(tocs):
        if 'MS 17' in t:
            print(i, repr(t))
    print()
    # 打印 118/128 前后 3 项
    for i in range(115, 132):
        print(i, repr(tocs[i]))
