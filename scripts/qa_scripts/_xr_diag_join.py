# -*- coding: utf-8 -*-
"""诊断：手动验证 reflow 拼接逻辑在 5dcede8a79a6 章2 上的行为"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

d = json.load(open(r'f:/program/Python/PhiAgent/backend/data/book_chapters/5dcede8a79a6/2.json', encoding='utf-8'))
END = '。！？…'
FOOT = re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]')
HAN = re.compile(r'[一-鿿]')

rows = []
for b in d['content']:
    for ln in b.get('value', '').split('\n'):
        s = ln.strip()
        rows.append(('empty', '') if not s else ('line', s))

out, buf = [], ''
def flush():
    global buf
    if buf:
        out.append(buf)
        buf = ''

for kind, s in rows:
    if kind == 'empty':
        flush()
        continue
    if FOOT.match(s):
        flush()
        out.append(s)
        continue
    if not HAN.search(s):
        flush()
        out.append(s)
        continue
    buf = (buf + s) if buf else s
    if s[-1] in END or (len(s) >= 2 and s[-2] in END and s[-1] in '"”』」）】'):
        flush()
flush()
print('行流', len(rows), '→ 拼接后', len(out))
for x in out[:3]:
    print(repr(x[:40]))
