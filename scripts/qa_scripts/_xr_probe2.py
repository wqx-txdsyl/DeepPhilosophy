# -*- coding: utf-8 -*-
import json
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
p = ck['ocr']['西方_托马斯_阿奎那_神学大全_第一集_第7卷.pdf']
# 译后记起始页 333 附近几页的页首
for k in ['331', '332', '333', '334', '335']:
    if k in p:
        head = p[k][:120].replace('\n', '⏎')
        print('=== 页 %s 页首: %s' % (k, head))
