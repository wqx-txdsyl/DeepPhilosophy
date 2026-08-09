# -*- coding: utf-8 -*-
"""读《资本论》105K vs OCR 281K 诊断"""
import json, os, re, hashlib

REL = '西方/路易·阿尔都塞/读《资本论》.pdf'
bid = hashlib.md5(REL.encode()).hexdigest()[:12]
print('bid:', bid)
D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/%s' % bid
files = sorted([f for f in os.listdir(D) if re.match(r'^\d+\.json$', f)], key=lambda x: int(x.split('.')[0]))
print('章数:', len(files))

total = 0
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    total += n
    head = ch['content'][0].get('value', '')[:45] if ch.get('content') else '(空)'
    print('[%02d] %-20s %8d | %s' % (ch['index'], str(ch.get('title'))[:20], n, head))
print('合计:', total)

# ckpt OCR 页数分布
ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读《资本论》.pdf', {})
keys = sorted(int(k) for k in ocr if ocr[k] and ocr[k] != '__FAILED__')
print()
print('OCR 页数:', len(keys), '| 范围: %d-%d' % (min(keys), max(keys)))
gaps = []
for i in range(len(keys) - 1):
    if keys[i + 1] - keys[i] > 1:
        gaps.append((keys[i], keys[i + 1]))
print('页序缺口(>1页):', gaps[:20], '共', len(gaps))
