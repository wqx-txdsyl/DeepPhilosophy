# -*- coding: utf-8 -*-
"""验证重导 85 章内容完整性: 总量对比 + 关键章边界抽查"""
import json, os, zipfile, re
from bs4 import BeautifulSoup

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'
EP = r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub'

# 1. 85 章总量
total = 0
for i in range(85):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print('85 章总字符:', total)

# 2. 源 part 正文总量（去标签近似）
def strip_html(h):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&nbsp;?', ' ', t)
    t = re.sub(r'&[a-z]+;', '', t)
    return len(t.strip())

with zipfile.ZipFile(EP) as z:
    names = [n for n in z.namelist() if re.match(r'text/part\d+.*\.html$', n)]
    total_src = sum(strip_html(z.read(n).decode('utf-8', 'ignore')) for n in names)
    print('源 part 正文总量(去标签):', total_src, '| part 数:', len(names))

print()
print('=== 边界抽查 ===')
for i, lbl in [(2, '卷1 MS101(哲学)'), (4, '卷1 MS101(私人)'), (8, '卷3 一、哲学'),
               (10, '卷3 三、唯心主义'), (51, '卷5 五(五)不规则的无穷小数'), (0, '卷1 卷标题')]:
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    blocks = ch.get('content', [])
    n = sum(len(b.get('value', '')) for b in blocks)
    head = blocks[0].get('value', '')[:40].replace('\n', '') if blocks else '(无块)'
    tail = blocks[-1].get('value', '')[-40:].replace('\n', '') if blocks else ''
    print('--- %d %s | %d字符 %d块' % (i, lbl, n, len(blocks)))
    print('   开头: %r' % head)
    print('   结尾: %r' % tail)
