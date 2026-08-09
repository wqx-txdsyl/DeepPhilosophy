# -*- coding: utf-8 -*-
"""恢复 130 章 title: 用 NCX 条目标题（与 extract 顺序一一对应）校准
上轮清洗误伤: 'MS 175'→'MS ', 'MS 177'→'MS ', '（二）2＋2＝4'→'（二）2＋2＝'"""
import zipfile, json, os, re
from bs4 import BeautifulSoup

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'
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

VOL_PAT = re.compile(r'^维特根斯坦文集.*第[一二三四五六七八九十百\d]+卷')

with zipfile.ZipFile(EP) as z:
    ncx = BeautifulSoup(z.read('toc.ncx').decode('utf-8', 'ignore'), 'xml')
    ncx_titles = [_clean_title(np.find('navLabel').text.strip()) for np in ncx.find_all('navPoint')
                  if np.find('navLabel') and np.find('content')]
print('ncx 条目:', len(ncx_titles))

fixed = 0
for i in range(130):
    p = os.path.join(D, '%d.json' % i)
    ch = json.load(open(p, encoding='utf-8'))
    expect = ncx_titles[i]
    if VOL_PAT.match(expect):
        expect = re.sub(r'[-\d]+$', '', expect)  # 卷标题清洗（与 final 一致）
    if ch.get('title') != expect:
        body = ''.join(b.get('value', '') for b in ch.get('content', []) if b.get('type') == 'text').strip()
        print('%3d: %r → %r (body=%r)' % (i, ch.get('title'), expect, body[:30]))
        ch['title'] = expect
        json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        fixed += 1
print('修正 %d 个 title' % fixed)
