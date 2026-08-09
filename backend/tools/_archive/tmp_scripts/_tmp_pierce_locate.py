# -*- coding: utf-8 -*-
"""皮尔斯文选章节重建: 28篇论文标题 → 页首定位 → 切章 (dry-run 先看命中率)
目录(书内页码): 见 _tmp_pierce_rebuild.py 同目录注释
"""
import json, re

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
ocr = ck['ocr']['西方_查尔斯_桑德斯_皮尔士_皮尔斯文选.pdf']

# 28 篇论文标题(目录原文, 去标点) + 附录
TITLES = [
    '什么是实用主义', '实效主义的一些论点', '实用主义回顾最后一次表述',
    '信念的确定', '如何使我们的观念清楚明白', '与人据说具有的某些能力相关的几个问题',
    '对4种能力的否定所产生的某些后果', '精神的法则',
    '现象学原理', '对形而上学的看法', '论形而上学', '论新范畴表', '第三性的实在',
    '数学的本质', '数学的本性', '审视必然性学说', '不明推论式与归纳式', '推理的有效性的标准',
    '一二三思维与自然界的基本范畴', '作为指号学的逻辑指号论', '论指号的本性', '指号',
    '理论结构', '科学态度和可错论', '哲学和科学一种分类', '宗教与科学的联姻', '上帝概念',
    '什么是基督教信仰',
    '皮尔斯文集目录英文版八卷本', '皮尔斯年表',
]

def norm(s):
    """去空格/标点/数字变化"""
    s = re.sub(r'[\s·．.\-—,，、（）()？?]', '', s)
    return s

# 逐页页首 4 行匹配
def head_lines(v, n=4):
    ls = [l.strip() for l in v.split('\n') if l.strip()]
    return ls[:n]

hits = {}
miss = []
for ti, t in enumerate(TITLES):
    tn = norm(t)
    key = tn[:6]  # 前6字(去标点后)作定位键, 不足取全部
    found = None
    for pg in sorted(ocr, key=lambda x: int(x)):
        v = ocr[pg]
        if not v or len(v) < 5:
            continue
        for hl in head_lines(v):
            if key in norm(hl):
                found = int(pg)
                break
        if found is not None:
            break
    if found is None:
        miss.append((ti, t))
    else:
        hits[t] = found

print('命中 %d/30' % len(hits))
for t, pg in sorted(hits.items(), key=lambda x: x[1]):
    print('  页%d %s' % (pg, t))
if miss:
    print('未命中:')
    for ti, t in miss:
        print('  [%d] %s' % (ti, t))
