# -*- coding: utf-8 -*-
"""探查 312/313/314 页首, 确定『论指号的本性』(书内299→PDF312) 与『指号』(书内301→PDF314) 真实位置"""
import json

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
ocr = ck['ocr']['西方_查尔斯_桑德斯_皮尔士_皮尔斯文选.pdf']

for pg in [311, 312, 313, 314, 315]:
    v = ocr.get(str(pg), '')
    print('===== PDF页%d =====' % pg)
    if not v:
        print('(空)')
    else:
        for ln in v.split('\n')[:6]:
            if ln.strip():
                print(repr(ln.strip()[:50]))
    print()
