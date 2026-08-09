# -*- coding: utf-8 -*-
import json, re
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
# 1. gubernetur 定位
print('=== gubernetur 出现页 ===')
for k, v in ck['ocr']['西方_托马斯_阿奎那_神学大全_第一集_第7卷.pdf'].items():
    if 'gubernetur' in v:
        print('页 %s:' % k)
        i = v.find('gubernetur')
        print('  …%s…' % v[max(0,i-80):i+40].replace('\n','⏎'))
# 2. 页27 完整原文长度 + 末尾
p27 = ck['ocr']['西方_托马斯_阿奎那_神学大全_第一集_第7卷.pdf']['27']
print()
print('=== 页27 长度 %d ===' % len(p27))
print(p27[-400:])
# 3. 3318 形态
print()
print('=== 3318 出现页 ===')
for k, v in ck['ocr']['西方_托马斯_阿奎那_神学大全_第一集_第7卷.pdf'].items():
    if '3318' in v:
        i = v.find('3318')
        print('页 %s: …%s…' % (k, v[max(0,i-60):i+40].replace('\n','⏎')))
