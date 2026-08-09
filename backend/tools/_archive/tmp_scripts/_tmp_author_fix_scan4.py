# -*- coding: utf-8 -*-
"""提取 6 本系列书 + 导读类存疑书的书名页文本, 找真实作者"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
by_id = {it.get('id'): it for it in items}

# 1. 6 本系列书 PDF（作者=哲学家本人）
SERIES = {
    '西方/帕斯卡尔.pdf': None,  # 占位, 下面用真实路径
}
series_pdfs = [os.path.join(r'F:/philosophy', rel).replace('\\', '/')
               for rel in ['西方/布莱兹·帕斯卡尔/最伟大的思想家 - 帕斯卡尔.pdf',
                           '西方/弗里德里希·尼采/最伟大的思想家 - 尼采.pdf',
                           '西方/戈特弗里德·威廉·莱布尼茨/最伟大的思想家 - 莱布尼茨.pdf',
                           '西方/索伦·克尔凯郭尔/最伟大的思想家 - 克尔恺廓尔.pdf',
                           '西方/苏格拉底/最伟大的思想家 - 苏格拉底.pdf',
                           '西方/莫里斯·梅洛-庞蒂/最伟大的思想家 - 梅洛-庞蒂.pdf']]

# 2. 导读类存疑: 标题含 导读/导论 且 作者含 哲学家本人特征 (先列全部看)
print('== books.json 中标题含 导读/导论 的条目 ==')
for it in items:
    t = it.get('title', '')
    if '导读' in t or '导论' in t or t.startswith('哲学导'):
        print('  %s | %s | %s' % (t[:40], it.get('author', '')[:24], it.get('id')))

def first_pages(fp, n=3):
    doc = fitz.open(fp)
    out = []
    for p in range(min(n, doc.page_count)):
        out.append(doc[p].get_text() or '')
    doc.close()
    return '\n'.join(out)

print()
print('== 系列书书名页文本 ==')
for fp in series_pdfs:
    txt = first_pages(fp)
    # 去空行, 取前 25 行
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    print('--- %s' % os.path.basename(os.path.dirname(fp)))
    for l in lines[:14]:
        if len(l) < 60:
            print('   %s' % l)
