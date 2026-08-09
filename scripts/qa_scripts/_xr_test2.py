# -*- coding: utf-8 -*-
import json
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
SAFE = '西方_托马斯_阿奎那_神学大全_第一集_第6卷.pdf'
ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]
# 问题76 标题页 = 页 33（脚本输出 @页33）
p33 = pages['33']
i = p33.find('447b')
print('=== checkpoint 页33 前 220 字符 ===')
print(repr(p33[:220]))
print()
print('=== 页33 中 447b 附近 repr ===')
j = p33.find('447b')
print(repr(p33[j-30:j+40]))
print()
print('=== 页33 第1-10行 ===')
for k, ln in enumerate(p33.split('\n')[:10]):
    print('%d: %r' % (k, ln))
# 1.json 447b 上下文
ch = json.load(open('_xr_out_aquinas6/1.json', encoding='utf-8'))
v = ch['content'][0]['value']
print()
print('=== 1.json 447b 附近 repr ===')
j = v.find('447b')
print(repr(v[j-40:j+60]))
