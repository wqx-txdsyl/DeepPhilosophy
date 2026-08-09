# -*- coding: utf-8 -*-
"""books_catalog.json chapterCount 校准: 从 book_chapters/<id>/meta.json 回写真实章数
仅修复/盘点用; 无章节目录的书(txt 等)保持原值"""
import json, os

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
CP = B + r'\backend\data\books_catalog.json'
CD = B + r'\backend\data\book_chapters'

cat = json.load(open(CP, encoding='utf-8'))
fixed = 0
checked = 0
for item in cat['books']:
    bid = item['id']
    mp = os.path.join(CD, bid, 'meta.json')
    if not os.path.exists(mp):
        continue
    m = json.load(open(mp, encoding='utf-8'))
    real = m.get('chapterCount', 0)
    checked += 1
    if item.get('chapterCount') != real:
        print('%-16s %-40s %d -> %d' % (bid, item['title'][:38], item.get('chapterCount', 0), real))
        item['chapterCount'] = real
        fixed += 1

json.dump(cat, open(CP, 'w', encoding='utf-8'), ensure_ascii=False)
print()
print('检查 %d 本, 修正 %d 本' % (checked, fixed))
print('total:', cat['total'])
