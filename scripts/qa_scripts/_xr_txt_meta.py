# -*- coding: utf-8 -*-
"""txt 90 本：books.json 字段全貌 + detail 是否存在"""
import json, os

bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
txts = [b for b in bk if b.get('file_type') == 'txt' and (b.get('chapterCount') or 0) == 0]

# 字段集合
keys = set()
for b in txts:
    keys.update(b.keys())
print('books.json txt 条目字段:', sorted(keys))
print()
# 样例完整条目
print('=== 前 3 本完整条目 ===')
for b in txts[:3]:
    print(json.dumps(b, ensure_ascii=False)[:400])
print()
# detail 状态
have_detail = 0
for b in txts:
    if os.path.exists('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/%s.json' % b.get('id')):
        have_detail += 1
print('有 book_detail: %d / 90' % have_detail)
# 有 detail 的看内容
n = 0
for b in txts:
    p = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/%s.json' % b.get('id')
    if os.path.exists(p) and n < 3:
        d = json.load(open(p, encoding='utf-8'))
        print('=== detail %s: %s' % (b.get('id'), json.dumps(d, ensure_ascii=False)[:300]))
        n += 1
print()
# 90 本完整清单（id|书名|作者）输出到文件
with open('C:/Users/wqx_0/AppData/Local/Temp/txt_list.txt', 'w', encoding='utf-8') as f:
    for b in txts:
        f.write('%s | %s | %s\n' % (b.get('id'), b.get('title'), b.get('author')))
print('清单已存 txt_list.txt, %d 行' % len(txts))
