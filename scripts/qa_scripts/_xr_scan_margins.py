# -*- coding: utf-8 -*-
"""第6/7卷行内栏标扫描：汉字+3-4位数字[+字母]+行尾"""
import json, os, re
base = os.path.dirname(os.path.abspath(__file__))
P = re.compile(r'([\u4e00-\u9fff])(\d{3,4}[a-z]?)(\n|$)')
for name, d in [('第6卷', '_xr_out_aquinas6'), ('第7卷', '_xr_out_aquinas7')]:
    od = os.path.join(base, d)
    tot = 0
    samples = []
    for fn in sorted(os.listdir(od)):
        if fn == 'meta.json':
            continue
        ch = json.load(open(os.path.join(od, fn), encoding='utf-8'))
        v = ch['content'][0]['value']
        for m in P.finditer(v):
            tot += 1
            if len(samples) < 12:
                s = max(0, m.start() - 18)
                samples.append('[%s] …%s…' % (fn, v[s:m.end() + 6].replace('\n', '⏎')))
    print('===== %s 行内栏标/行尾数字: %d 处 =====' % (name, tot))
    for s in samples:
        print('  ' + s)
