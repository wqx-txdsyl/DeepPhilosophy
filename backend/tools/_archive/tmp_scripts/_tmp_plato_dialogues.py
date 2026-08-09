# -*- coding: utf-8 -*-
"""在柏拉图对话集 5 章正文里找对话篇目标题, 评估重切方案"""
import json, os, re

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'

# 王太庆译本《柏拉图对话集》已知篇目(含旧译名)
KNOWN = ['自辩篇', '克利陀篇', '斐都篇', '锭话篇', '普洛他过拉', '曼诺', '泰阿泰德',
         '智术之师', '治国篇', '理想国', '法律篇', '斐德罗', '会饮', '美诺', '普罗泰戈拉',
         '申辩', '克里同', '斐多', '巴门尼德', '智者', '政治家', '蒂迈欧', '斐莱布',
         '费莱布', '高尔吉亚', '欧绪弗洛', '游叙弗伦', '克拉底鲁', '欧悌甫戎']

pat = re.compile('|'.join(KNOWN))

for i in range(5):
    ch = json.load(open(os.path.join(CD, '%d.json' % i), encoding='utf-8'))
    hits = []
    for b in ch.get('content', []):
        v = b.get('value', '')
        if len(v) > 20 and pat.search(v):
            hits.append((b.get('value', '')[:50]))
    print('=== %d.json (%s) 篇目标题候选 %d 处 ===' % (i, ch.get('title', '')[:20], len(hits)))
    for h in hits[:25]:
        print('  ', h.replace('\n', '⏎'))
