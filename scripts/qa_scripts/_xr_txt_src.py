# -*- coding: utf-8 -*-
"""90 本 txt：同书名任意格式源文件 + books.json 字段 + detail 状态"""
import json, os, re

bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
txts = [b for b in bk if b.get('file_type') == 'txt' and (b.get('chapterCount') or 0) == 0]

# 建 F:/philosophy 全量文件索引（一次遍历）
index = {}  # name(去扩展名) -> [paths]
for root, dirs, files in os.walk('F:/philosophy'):
    if root.count(os.sep) - 'F:/philosophy'.count(os.sep) > 3:
        dirs[:] = []
        continue
    for f in files:
        stem = os.path.splitext(f)[0]
        stem2 = re.sub(r'[《》()（）\[\]【】\s]', '', stem)
        index.setdefault(stem2, []).append(os.path.join(root, f))

print('=== 90 本 txt：同书名任意格式 ===')
have = 0
none = 0
for b in txts:
    t = b.get('title', '')
    key = re.sub(r'[《》()（）\[\]【】\s]', '', t)
    hits = index.get(key, [])
    # 排除 .txt（占位）
    real = [h for h in hits if not h.lower().endswith('.txt')]
    if real:
        have += 1
        exts = sorted(set(os.path.splitext(h)[1].lower() for h in real))
        print('  ✓ %s | %s | %s | %s' % (b.get('id'), t[:28], b.get('author', '')[:14], exts))
    else:
        none += 1
print()
print('有非txt源: %d / 90' % have)
print('仅空txt: %d / 90' % none)
print()
print('=== 仅空 txt 的书（内容完全缺失，需找源）===')
for b in txts:
    t = b.get('title', '')
    key = re.sub(r'[《》()（）\[\]【】\s]', '', t)
    if not index.get(key, []):
        print('  %s | %s | %s' % (b.get('id'), t[:34], b.get('author', '')[:18]))
