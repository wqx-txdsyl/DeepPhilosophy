# -*- coding: utf-8 -*-
"""自然与快乐（221f09d04944）下编源页诊断：checkpoint OCR 原始页行结构"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
oc = ck.get('ocr', {})
print('OCR 键:', list(oc.keys())[:3], '...')

safe = [k for k in oc if '伊壁鸠鲁' in k or '自然' in k]
print('候选键:', safe)

for k in safe:
    pages = oc[k]
    n = len(pages)
    print('\n===== %s (%d 页) =====' % (k, n))
    # 打印中间页和后段页的行结构
    for p in [n // 2, n - 5]:
        txt = pages.get(str(p), '')
        lines = [l for l in txt.split('\n') if l.strip()]
        if not lines:
            print('页 %d 空' % p)
            continue
        lens = [len(l.strip()) for l in lines[:12]]
        print('页 %d 行数=%d 前12行长度=%s' % (p, len(lines), lens))
        print('  首5行:', ' || '.join(l.strip()[:22] for l in lines[:5]))
        print('  末3行:', ' || '.join(l.strip()[:22] for l in lines[-3:]))
