# -*- coding: utf-8 -*-
"""黑格尔分级：ncx 册名提取 + 库里 445 章标题清单"""
import zipfile, re, json

z = zipfile.ZipFile('f:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/黑格尔作品集（套装共14册）.epub')
t = z.read('toc.ncx').decode('utf-8', errors='ignore')

# 解析 navPoint 层级（简单：深度追踪 <navPoint> 开闭）
depth = 0
navs = []
for mm in re.finditer(r'<(/?)\s*navPoint[^>]*>', t):
    if mm.group(1) == '/':
        depth -= 1
    else:
        title_m = re.search(r'<text>(.*?)</text>', t[mm.end():mm.end() + 500])
        navs.append((depth, re.sub(r'\s+', ' ', title_m.group(1)).strip() if title_m else '?'))
        depth += 1

# 最高层（depth=0）= 册
print('=== ncx 最高层（册）===')
books = []
for d, title in navs:
    if d == 0:
        books.append(title)
        print('  册:', title)
print('册数:', len(books))
print()

# depth=1 的（册下第一层）
print('=== 每册下第一层条目（部分）===')
cur = None
for d, title in navs:
    if d == 0:
        cur = title
    elif d == 1:
        print('  %-14s | %s' % (cur[:14], title[:40]))
print()

# 库里 445 章标题
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/bbac1be0bb4b/meta.json', encoding='utf-8'))
print('=== 库里 toc %d 章标题全貌 ===' % len(m['toc']))
with open('C:/Users/wqx_0/AppData/Local/Temp/hegel_toc.txt', 'w', encoding='utf-8') as f:
    for t in m['toc']:
        f.write('[%3d] %s\n' % (t.get('index'), t.get('title')))
print('已存 hegel_toc.txt')
