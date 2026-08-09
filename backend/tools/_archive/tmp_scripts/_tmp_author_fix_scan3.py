# -*- coding: utf-8 -*-
"""精确反查: md5(rel) → bid, 确认每个条目对应的磁盘 PDF 路径"""
import json, os, hashlib

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
by_id = {it.get('id'): it for it in items}

# 全部 PDF → bid
all_pdf = {}  # rel -> bid
for root, dirs, files in os.walk(r'F:/philosophy'):
    for fn in files:
        if fn.lower().endswith('.pdf'):
            rel = os.path.relpath(os.path.join(root, fn), r'F:/philosophy').replace('\\', '/')
            all_pdf[rel] = hashlib.md5(rel.encode()).hexdigest()[:12]

print('== 系列 PDF 精确反查 ==')
for rel, bid in sorted(all_pdf.items()):
    if '最伟大的思想家' in rel:
        it = by_id.get(bid)
        print('  %-28s → %s | %s | 作者: %s' % (
            rel, bid, it.get('title', '(未入库)')[:18] if it else '(未入库)',
            it.get('author', '') if it else ''))

print()
print('== 纯人名标题条目对应的磁盘 PDF ==')
for it in items:
    t = it.get('title', '')
    # 纯人名标题的条目（可能是系列书改名）
    if t in ('克尔恺廓尔', '奥古斯丁', '尼采', '帕斯卡尔', '柏拉图', '梅洛-庞蒂', '苏格拉底', '莱布尼茨',
             '奥古斯丁忏悔录'):
        bid = it.get('id')
        # 找对应的 rel
        rels = [r for r, b in all_pdf.items() if b == bid]
        print('  %-12s | %s | 作者: %s | PDF: %s' % (t, bid, it.get('author', ''), rels or '(未入库)'))
