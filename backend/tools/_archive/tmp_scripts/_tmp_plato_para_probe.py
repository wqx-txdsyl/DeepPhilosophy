# -*- coding: utf-8 -*-
"""探查柏拉图对话集会饮篇的 OCR 页文本: 段落分隔是 \n\n 还是单 \n? 页眉页脚长啥样?"""
import json, re

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))

# 找到柏拉图对话集 ocr 键
cands = [k for k in ck['ocr'] if '柏拉图' in k]
print('OCR 键:', cands)

for k in cands:
    ocr = ck['ocr'][k]
    # 找会饮篇起始页: 页首含"会饮篇"
    starts = [pg for pg, v in sorted(ocr.items(), key=lambda x: int(x[0]))
              if isinstance(v, str) and '会饮篇' in v[:200]]
    print('会饮篇候选页:', starts[:5])
    if not starts:
        continue
    pg = starts[0]
    v = ocr[pg]
    print('===== 会饮篇起始页 %s 前 40 行(带 repr) =====' % pg)
    for ln in v.split('\n')[:40]:
        print(repr(ln))
    # 统计全书 \n\n 出现次数
    n2 = sum(v2.count('\n\n') for v2 in ocr.values() if isinstance(v2, str))
    n1 = sum(v2.count('\n') for v2 in ocr.values() if isinstance(v2, str))
    print('\n全书记 \n\n: %d 次, 单 \\n: %d 次' % (n2, n1))
    break
