# -*- coding: utf-8 -*-
"""探查皮尔斯文选疑点页: 页1误命中 + 4未命中标题推测位置(书内页+13)"""
import json

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
ocr = ck['ocr']['西方_查尔斯_桑德斯_皮尔士_皮尔斯文选.pdf']


def show(pg, n=600, label=''):
    v = ocr.get(str(pg), '')
    print('===== PDF页%d %s =====' % (pg, label))
    print(v[:n])
    print()


# 1. 页1误命中原因
show(1, 400, '疑点: 误命中"论形而上学/指号"')
# 2. 未命中标题的推算位置(书内页+13)
show(284, 400, '推测: 一、二、三：思维与自然界的基本范畴(271+13)')
show(346, 400, '推测: 哲学和科学：一种分类(333+13)')
show(376, 400, '推测: 附录《皮尔斯文集》目录(363+13)')
show(411, 400, '推测: 皮尔斯年表(398+13)')
# 3. 论新范畴表真位置
show(217, 300, '推测: 论新范畴表(204+13)')
# 4. 正文页眉格式: 第15页(正文第2页)
show(15, 300, '正文页眉格式')
