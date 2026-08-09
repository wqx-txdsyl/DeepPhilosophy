# -*- coding: utf-8 -*-
"""90 本 txt 源文件大小全查 + 同目录有没有其他非空版本"""
import json, os, re, glob

bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
txts = [b for b in bk if b.get('file_type') == 'txt' and (b.get('chapterCount') or 0) == 0]

empty = 0
nonempty = 0
for b in txts:
    t = b.get('title', '')
    found = None
    for root, dirs, files in os.walk('F:/philosophy'):
        if root.count(os.sep) - 'F:/philosophy'.count(os.sep) > 3:
            dirs[:] = []
            continue
        for f in files:
            if f == t + '.txt':
                found = os.path.join(root, f)
                break
        if found:
            break
    if found is None:
        print('  %s: 无同名 txt' % t[:30])
        continue
    sz = os.path.getsize(found)
    if sz == 0:
        empty += 1
    else:
        nonempty += 1
        print('  非空: %s (%.1f KB) %s' % (t[:30], sz / 1024, found))
print()
print('空文件: %d / 90' % empty)
print('非空: %d / 90' % nonempty)
# 非空的具体目录
for b in txts:
    t = b.get('title', '')
    found = None
    for root, dirs, files in os.walk('F:/philosophy'):
        if root.count(os.sep) - 'F:/philosophy'.count(os.sep) > 3:
            dirs[:] = []
            continue
        for f in files:
            if f == t + '.txt':
                found = os.path.join(root, f)
                break
        if found:
            break
    if found:
        sz = os.path.getsize(found)
        if sz > 0:
            print('  %s | %s | %.1f KB' % (b.get('id'), t[:30], sz / 1024))
