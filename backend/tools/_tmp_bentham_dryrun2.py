# -*- coding: utf-8 -*-
"""边沁干跑2: 仅正文页(29-468) 的章内目录条目统计"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})

NUM = re.compile(r'^\d{1,4}$')
ENTRY = re.compile(r'^\d+[.．、][^。！？]{1,60}$')

n_toc = n_body_tit = 0
toc_ex = []
bodytit_ex = []
for k in sorted(int(x) for x in ocr):
    if k < 29 or k > 468:
        continue
    v = ocr.get(str(k), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    for i, ln in enumerate(lines):
        if not ENTRY.match(ln):
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        if NUM.match(nxt) or ENTRY.match(nxt):
            n_toc += 1
            if len(toc_ex) < 12:
                toc_ex.append('页%d: %s | 后:%s' % (k, ln[:45], nxt[:20]))
        else:
            n_body_tit += 1
            if len(bodytit_ex) < 6:
                bodytit_ex.append('页%d: %s | 后:%s' % (k, ln[:45], nxt[:20]))

print('正文页 目录条目(后跟数字/连续条目):', n_toc)
print('正文页 正文条目标题(后跟正文):', n_body_tit)
print()
print('--- 章内目录条目样本(将被删) ---')
for e in toc_ex:
    print('  ', e)
print()
print('--- 正文条目标题样本(将保留) ---')
for e in bodytit_ex:
    print('  ', e)
