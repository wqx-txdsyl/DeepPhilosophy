# -*- coding: utf-8 -*-
"""政治学: ckpt 页 0-15 + 章 0-2 标题与字符量"""
import json, os, re, hashlib

REL = '西方/亚里士多德/政治学.pdf'
SAFE = re.sub(r'[^\w\-.]', '_', REL)
ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get(SAFE, {})
print('OCR 页:', len(ocr), '范围: %d-%d' % (min(int(k) for k in ocr), max(int(k) for k in ocr)))
for p in range(0, 12):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()] if v else []
    print('页%-3d (%2d行): %s' % (p, len(lines), ' | '.join(l[:20] for l in lines[:3])[:70]))

print()
D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/53b09f03e24e'
for fn in ['0.json', '1.json', '2.json', '3.json']:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    print('[%s] %-24s %d | 首块: %s' % (fn, ch.get('title'), n, ch['content'][0].get('value', '')[:40] if ch.get('content') else '(空)'))
