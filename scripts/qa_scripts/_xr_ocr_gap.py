# -*- coding: utf-8 -*-
"""OCR 断点推断：ocr 缓存 vs books 完成 差集 + main 扫描顺序下一本"""
import json, os

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
ck = json.load(open(os.path.join(DP, 'backend/data/dp_pdf_import_ckpt.json'), encoding='utf-8'))
books = ck.get('books', {})   # 章节化完成
ocr = ck.get('ocr', {})       # 页级缓存（处理过/处理中）

print('=== ocr 有缓存但 books 未章节化（断点书候选）===')
for k in ocr:
    if k not in books:
        print('  [处理中?]', k)
print()
print('=== books 完成但 ocr 无缓存（文本层书，正常）===\n  （略）')
print()
# main 扫描顺序：region -> author -> fn
for region in ['东方', '西方']:
    rp = 'F:/philosophy/' + region
    if not os.path.isdir(rp):
        continue
    for author in sorted(os.listdir(rp)):
        ap = os.path.join(rp, author)
        if not os.path.isdir(ap):
            continue
        for fn in sorted(os.listdir(ap)):
            if not fn.lower().endswith('.pdf'):
                continue
            rel = '%s/%s/%s' % (region, author, fn)
            key = rel if rel in books or rel in ocr else None
            # books 用相对路径键
            if rel in books:
                st = '完成'
            elif rel in ocr:
                st = '缓存'
            else:
                st = '等待'
            if st != '完成' or True:
                pass
    # 打印所有 pdf 状态（简化为第一层）
for region in ['东方', '西方']:
    rp = 'F:/philosophy/' + region
    if not os.path.isdir(rp):
        continue
    for author in sorted(os.listdir(rp)):
        ap = os.path.join(rp, author)
        if not os.path.isdir(ap):
            continue
        for fn in sorted(os.listdir(ap)):
            if not fn.lower().endswith('.pdf'):
                continue
            rel = '%s/%s/%s' % (region, author, fn)
            if rel in books:
                st = '✔完成'
            elif rel in ocr:
                st = '◐缓存'
            else:
                st = '○等待'
            print('%s | %s' % (st, rel))
