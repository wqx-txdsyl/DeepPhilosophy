# -*- coding: utf-8 -*-
"""txt 样本：内容形态/章节结构/编码/大小"""
import os, re, glob

SAMPLE = ['科学革命的结构', '正义论', '逻辑研究', '词与物', '狱中札记']
for t in SAMPLE:
    hits = []
    for root, dirs, files in os.walk('F:/philosophy'):
        if root.count(os.sep) - 'F:/philosophy'.count(os.sep) > 3:
            dirs[:] = []
            continue
        for f in files:
            if f == t + '.txt' or f == t + '.TXT':
                hits.append(os.path.join(root, f))
    if not hits:
        print('=== %s: 未找到' % t)
        continue
    p = hits[0]
    size = os.path.getsize(p)
    print('=== %s (%s, %.1f KB)' % (t, p, size / 1024))
    # 编码探测
    for enc in ('utf-8', 'gbk', 'utf-16'):
        try:
            with open(p, encoding=enc) as f:
                head = f.read(2000)
            print('  编码:', enc)
            break
        except Exception:
            continue
    # 内容开头
    print('  开头: %s' % head[:220].replace('\n', ' | '))
    # 章节结构探测
    with open(p, encoding=enc) as f:
        txt = f.read()
    chaps = re.findall(r'^第[一二三四五六七八九十百千0-9]+[章卷部]', txt, re.M)
    print('  章节标题行(第N章/卷/部): %d 处, 前6: %s' % (len(chaps), chaps[:6]))
    # 总行数/总字数
    lines = txt.splitlines()
    nchar = sum(len(l) for l in lines)
    print('  行数 %d, 总字数 ~%d' % (len(lines), nchar))
    print()
