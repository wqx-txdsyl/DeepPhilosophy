# -*- coding: utf-8 -*-
"""政治学 (53b09f03e24e): 补章 0 导读内容(页 2-18), 其他章不动"""
import json, os, re, shutil

CKPT = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/53b09f03e24e'
PUB = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/53b09f03e24e'

ckpt = json.load(open(CKPT, encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_亚里士多德_政治学.pdf', {})

FOOT_RE = re.compile(r'^\d{1,4}$')
GUTTER_RE = re.compile(r'^[一-龥]{1,2}$')
NOISE_RE = re.compile(r'^[\s+·•.,;:，。、~—…·]+$')
AT_RE = re.compile(r'@')
END_PARA_RE = re.compile(r'[\d。！？；：…~"”』」）】%.,;:!?]$')

paras = []
for p in range(2, 19):
    v = ocr.get(str(p), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    body = []
    for ln in lines:
        if ln == '政治学' or ln == '目录':
            continue
        if FOOT_RE.match(ln) or GUTTER_RE.match(ln):
            continue
        ln = AT_RE.sub('', ln)
        if NOISE_RE.match(ln) or not ln:
            continue
        body.append(ln)
    if body:
        paras.append('\n'.join(body))

merged = []
for seg in paras:
    if merged and not END_PARA_RE.search(merged[-1]):
        merged[-1] += seg
    else:
        merged.append(seg)
text = '\n\n'.join(merged)
blocks = [{'type': 'text', 'value': v} for v in [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]]
print('导读字符:', len(text), '| 块数:', len(blocks))
print('开头:', text[:60].replace('\n', ' '))
print('结尾:', text[-60:].replace('\n', ' '))

ch = json.load(open(os.path.join(D, '0.json'), encoding='utf-8'))
ch['content'] = blocks
json.dump(ch, open(os.path.join(D, '0.json'), 'w', encoding='utf-8'), ensure_ascii=False)
shutil.copy2(os.path.join(D, '0.json'), os.path.join(PUB, '0.json'))
print('已补章 0 + public 同步')
