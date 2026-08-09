# -*- coding: utf-8 -*-
"""自然辩证法修复后残留检查"""
import json, os, re

base = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/aa21ac425e87'
fn = 0
brk = 0
CONT = re.compile(r'^[的了而在并就又以与和或及其它们这那之於于者所把被对从向为给没不无也还其毁]')
for f in sorted(os.listdir(base), key=lambda x: int(x.split('.')[0]) if x.endswith('.json') and x != 'meta.json' else 99):
    if not f.endswith('.json') or f == 'meta.json':
        continue
    c = json.load(open(os.path.join(base, f), encoding='utf-8'))
    vals = [b.get('value', '').strip() for b in c['content']
            if isinstance(b, dict) and isinstance(b.get('value', ''), str) and b['value'].strip()]
    fn += sum(1 for v in vals if re.fullmatch(r'［\d+］', v))
    for i in range(1, len(vals)):
        p, q = vals[i - 1].rstrip(), vals[i]
        if (not p.endswith(('。', '！', '？', '：', '；', '”', '」', '』', '）', ']', '］'))
                and CONT.match(q)):
            brk += 1
            if brk <= 8:
                print(f'  残留断段 [{f}]: …{p[-16:]} | {q[:16]}…')
print('残留［N］独立段:', fn)
print('残留高置信断段:', brk)
