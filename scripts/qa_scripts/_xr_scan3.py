# -*- coding: utf-8 -*-
"""无字母行尾数字抽样（第6卷 42 处）"""
import json, os, re
base = os.path.dirname(os.path.abspath(__file__))
P = re.compile(r'([\u4e00-\u9fff])(\d{3,4})(\n)')
n = 0
for fn in sorted(os.listdir(base + '/_xr_out_aquinas6')):
    if fn == 'meta.json':
        continue
    ch = json.load(open(os.path.join(base, '_xr_out_aquinas6', fn), encoding='utf-8'))
    v = ch['content'][0]['value']
    for m in P.finditer(v):
        n += 1
        if n <= 14:
            s = max(0, m.start() - 20)
            print('[%s] …%s…' % (fn, v[s:m.end() + 8].replace('\n', '⏎')))
print('总数(≤14抽样): %d' % n)
