# -*- coding: utf-8 -*-
"""边沁干跑: 章内目录条目行(^\d+[.．] 后跟孤立数字行) 与 正文条目标题 的区分"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})

NUM = re.compile(r'^\d{1,4}$')
ENTRY = re.compile(r'^\d+[.．、][^。！？]{1,60}$')

n_entry = n_toc = n_body_tit = 0
toc_examples = []
bodytit_examples = []
for k in sorted(int(x) for x in ocr):
    v = ocr.get(str(k), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    for i, ln in enumerate(lines):
        if not ENTRY.match(ln):
            continue
        n_entry += 1
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        nxt2 = lines[i + 2] if i + 2 < len(lines) else ''
        if NUM.match(nxt) or ENTRY.match(nxt):
            # 后跟孤立数字行 或 连续条目行 → 目录条目
            n_toc += 1
            if len(toc_examples) < 8:
                toc_examples.append('页%d: %s | 后:%s %s' % (k, ln[:40], nxt[:15], nxt2[:15]))
        else:
            n_body_tit += 1
            if len(bodytit_examples) < 8:
                bodytit_examples.append('页%d: %s | 后:%s' % (k, ln[:45], nxt[:20]))

print('^\d+[.．] 行总数:', n_entry)
print('目录条目(后跟数字/连续条目):', n_toc)
print('正文条目标题(后跟正文):', n_body_tit)
print()
print('--- 目录条目样本 ---')
for e in toc_examples:
    print('  ', e)
print()
print('--- 正文条目标题样本 ---')
for e in bodytit_examples:
    print('  ', e)
