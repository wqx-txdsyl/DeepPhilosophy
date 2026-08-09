# -*- coding: utf-8 -*-
"""139 批次摸底①：txt 90 本全貌（书名/作者/大小/有无源文件/书籍性质）"""
import json, os, re

bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
txts = [b for b in bk if b.get('file_type') == 'txt' and (b.get('chapterCount') or 0) == 0]
print('txt 且 cc=0 的书:', len(txts))
# 分布
print()
print('=== 按书名前 30 本 ===')
for b in txts[:30]:
    print('  %s | %s | %s' % (b.get('id'), (b.get('title') or '')[:38], (b.get('author') or '')[:20]))
print('  …共 %d 本' % len(txts))
print()
# 找源文件：F:/philosophy 下同名 txt
print('=== 源文件检查 ===')
found = 0
for b in txts:
    t = b.get('title', '')
    hits = []
    for root, dirs, files in os.walk('F:/philosophy'):
        # 限制深度，避免太慢
        if root.count(os.sep) - 'F:/philosophy'.count(os.sep) > 3:
            dirs[:] = []
            continue
        for f in files:
            if t[:8] in f or (t[:4] and t[:4] in f):
                hits.append(os.path.join(root, f))
    if hits:
        found += 1
        if found <= 15:
            print('  %s:' % t[:24], [os.path.basename(h) for h in hits[:3]])
print('  找到源文件: %d / %d' % (found, len(txts)))
