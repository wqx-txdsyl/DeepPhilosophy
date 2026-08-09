# -*- coding: utf-8 -*-
"""403 本全量盘点：已检查/未检查/需OCR/txt 四分类统计 + 明细"""
import json, os, re

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
bk = json.load(open(os.path.join(DP, 'app/public/books.json'), encoding='utf-8'))
print('books.json 总数:', len(bk))

# 字段分布
from collections import Counter
ft = Counter(b.get('file_type') for b in bk)
cc = Counter(('cc>0' if (b.get('chapterCount') or 0) > 0 else 'cc=0') for b in bk)
print('file_type 分布:', dict(ft))
print('chapterCount 分布:', dict(cc))

# CHKLIST 已检查 bid 集合（状态列非 ⏳ 或空）
chk = set()
checked = set()
lines = open('f:/program/Python/PhiAgent/backend/tools/CHKLIST.md', encoding='utf-8').read().splitlines()
for ln in lines:
    m = re.match(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([0-9a-f]{12})\s*\|\s*([^|]+?)\s*\|\s*(\|?.*)$', ln)
    if not m:
        continue
    bid = m.group(3)
    st = m.group(4).strip()
    chk.add(bid)
    if st and st not in ('⏳',):
        checked.add(bid)
print()
print('CHKLIST 记录书数:', len(chk), '其中已检查(状态非⏳):', len(checked))

# 分类
txt = [b for b in bk if b.get('file_type') == 'txt']
done_checked = [b for b in bk if b.get('id') in checked]
need_ocr = [b for b in bk if (b.get('chapterCount') or 0) == 0 and b.get('file_type') == 'pdf']
unchecked = [b for b in bk if b.get('id') not in chk]
print()
print('=== 分类统计 ===')
print('① 已检查入库(不管):', len(done_checked))
print('② 未检查:', len(unchecked))
print('③ 需OCR(pdf cc=0):', len(need_ocr))
print('④ txt(不管):', len(txt))

# 未检查的明细（按 file_type 分组）
print()
print('=== ② 未检查明细（CHKLIST 无记录）===')
uc_txt = [b for b in unchecked if b.get('file_type') == 'txt']
uc_pdf = [b for b in unchecked if b.get('file_type') != 'txt']
print('-- 未检查 txt（可能也是④不管类）:', len(uc_txt))
for b in uc_txt:
    print('   TXT | %s | %s' % (b.get('id'), b.get('title')))
print('-- 未检查 非txt:', len(uc_pdf))
for b in uc_pdf:
    print('   %s | %s | %s | cc=%s' % (b.get('file_type'), b.get('id'), b.get('title'), b.get('chapterCount') or 0))

# 需OCR 明细
print()
print('=== ③ 需OCR 明细（pdf cc=0）===')
for b in need_ocr:
    print('   %s | %s | %s' % (b.get('id'), b.get('title'), b.get('author') or ''))
