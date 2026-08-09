# -*- coding: utf-8 -*-
"""栏标分布统计 + 12.json 682b 重复之谜"""
import json, os, re
base = os.path.dirname(os.path.abspath(__file__))
P = re.compile(r'([\u4e00-\u9fff])(\d{3,4}[a-z]?)(\n|$)')
for name, d in [('第6卷', '_xr_out_aquinas6'), ('第7卷', '_xr_out_aquinas7')]:
    od = os.path.join(base, d)
    with_let = without = 0
    per_file = {}
    for fn in sorted(os.listdir(od)):
        if fn == 'meta.json':
            continue
        ch = json.load(open(os.path.join(od, fn), encoding='utf-8'))
        v = ch['content'][0]['value']
        n1 = n2 = 0
        for m in P.finditer(v):
            if m.group(2)[-1:].isalpha():
                n1 += 1
            else:
                n2 += 1
        per_file[fn] = (n1, n2)
        with_let += n1
        without += n2
    print('%s: 带字母 %d / 无字母 %d' % (name, with_let, without))
    for fn, (n1, n2) in sorted(per_file.items()):
        if n1 + n2:
            print('  %s: 带字母%d 无字母%d' % (fn, n1, n2))
# 12.json 682b 重复之谜
ch = json.load(open(os.path.join(base, '_xr_out_aquinas7', '12.json'), encoding='utf-8'))
v = ch['content'][0]['value']
idx = [m.start() for m in re.finditer('682b', v)]
print('12.json 682b 出现 %d 次: 位置 %s' % (len(idx), idx[:20]))
if idx:
    s = max(0, idx[0] - 100)
    print('上下文: …' + v[s:idx[0] + 30].replace('\n', '⏎') + '…')
    # 位置间隔
    gaps = [idx[i+1] - idx[i] for i in range(len(idx) - 1)]
    print('间隔: %s' % gaps[:20])
