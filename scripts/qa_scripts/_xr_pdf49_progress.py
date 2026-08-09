# -*- coding: utf-8 -*-
"""49 本批次进度：清单 vs checkpoint 完成 vs 库中 cc 对照"""
import json, os, hashlib

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
bk = json.load(open(os.path.join(DP, 'app/public/books.json'), encoding='utf-8'))
idmap = {b.get('id'): b for b in bk}
ck = json.load(open(os.path.join(DP, 'backend/data/dp_pdf_import_ckpt.json'), encoding='utf-8'))
books_ck = ck.get('books', {})   # 相对路径键
ocr_ck = ck.get('ocr', {})       # 安全名键

# 49 本清单（id|title|author）
print('=== 49 本（cc=0 pdf）当前进度 ===')
done_ck = 0
for line in open('C:/Users/wqx_0/AppData/Local/Temp/pdf49_list.txt', encoding='utf-8'):
    parts = line.rstrip('\n').split(' | ')
    if len(parts) < 3:
        continue
    bid, title, author = parts[0], parts[1], parts[2]
    b = idmap.get(bid, {})
    cc = b.get('chapterCount') or 0
    # checkpoint 相对路径键（需要 pdf 路径——从书名推断不了，用 bid 反查 rel）
    st = '✔已章节化' if cc > 0 else '○cc=0'
    print('  %s | %s | %s | %s' % (st, bid, title[:30], author[:14]))
print()

# 引擎完成的 34 本 vs 49 本对照：books.json 中 file_type=pdf 且 cc>0 的（引擎完成的全部）
print('=== 引擎 checkpoint 34 键 → 库中 cc 状态 ===')
for rel, v in books_ck.items():
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    b = idmap.get(bid, {})
    cc = b.get('chapterCount') or 0
    print('  %s | %s | %s | %s' % (v.get('src'), cc, bid, os.path.basename(rel)[:40]))
