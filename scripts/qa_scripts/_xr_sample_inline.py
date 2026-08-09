# -*- coding: utf-8 -*-
import json, re
P = re.compile(r'([一-鿿]\d{3,4}[a-z])')
ch = json.load(open('_xr_out_aquinas6/0.json', encoding='utf-8'))
v = ch['content'][0]['value']
n = 0
for m in P.finditer(v):
    s = max(0, m.start() - 15)
    e = min(len(v), m.end() + 15)
    print('…%s…' % v[s:e].replace('\n', '⏎'))
    n += 1
    if n >= 7:
        break
print('合计匹配:', len(P.findall(v)))
