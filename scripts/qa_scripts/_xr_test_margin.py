# -*- coding: utf-8 -*-
import re, json
P = re.compile(r'(?<=[一-鿿])\d{3,4}[a-z]$')
for s in ['还是所有447b', '所有447b', '实在的事439b物', '447b', '所有452a']:
    print(repr(s), '->', repr(P.sub('', s)))
# 真实文本里的行
ch = json.load(open('_xr_out_aquinas6/1.json', encoding='utf-8'))
v = ch['content'][0]['value']
i = v.find('447b')
print('1.json 447b 位置:', i)
if i >= 0:
    line = v[:i+5].rsplit('\n', 1)[-1]
    print('所在行 repr:', repr(line))
    print('sub 后:', repr(P.sub('', line)))
